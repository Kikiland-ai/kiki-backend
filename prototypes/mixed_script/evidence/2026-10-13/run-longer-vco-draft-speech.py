"""Join the accepted script to one real TTS call; no auto retries or alignment."""
import copy,hashlib,json,os,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from prototypes.mixed_script.pipeline import PipelineError,read_json,save_result,validate_input,validate_stage
from prototypes.mixed_script.speech import GeminiSpeechGenerator
folder=Path('work/longer-vco-tts')
result=read_json(folder/'script.draft.result.json')
glossary=validate_input(result['source'])
for stage in ('translation','mixed'):
    if result.get(stage) is None:continue
    raw={'sentences':[{k:s[k] for k in ('id','spans','speech_text')} for s in result[stage]['sentences']]}
    validate_stage(result['source'],raw,glossary)
script=result['speech_script']
for name in ('speech-draft.wav','speech-draft.mp3','audio.manifest.draft.json','bundle.draft.result.json','speech.draft.attempt1.summary.json'):
    if (folder/name).exists():raise SystemExit('Existing speech output preserved: '+name)
generator=GeminiSpeechGenerator(os.environ.get('GEMINI_API_KEY',''),model='gemini-3.8-flash-lite-tts')
save_result(generator.make_request(script),folder/'speech.draft.request.json')
summary={'model':generator.model,'voice':generator.voice,'script_sha256':hashlib.sha256(script.encode()).hexdigest(),
         'script_canonical_validation':'passed_after_span_label_repair','script_stage':'translation_draft','mixed_refinement':'blocked_HTTP503','scientific_and_native_review':'pending'}
print('Requesting speech:',generator.model,'voice:',generator.voice,flush=True)
start=time.monotonic()
try:
    audio,metadata=generator.generate(script)
    with (folder/'speech-draft.wav').open('xb') as f:f.write(audio)
    metadata['script_result_file']='script.draft.result.json'
    metadata['script_stage']='translation_draft'
    metadata['mixed_refinement']='blocked_HTTP503'
    metadata['phrase_warnings']=result['validation']['phrase_warnings']
    metadata['wav_file']='speech-draft.wav'
    command=['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-n','-i',str(folder/'speech-draft.wav'),
             '-codec:a','libmp3lame','-b:a','64k',str(folder/'speech-draft.mp3')]
    converted=subprocess.run(command,capture_output=True)
    if converted.returncode==0:
        metadata['mp3_file']='speech-draft.mp3'
        metadata['mp3_sha256']=hashlib.sha256((folder/'speech-draft.mp3').read_bytes()).hexdigest()
        metadata['mp3_bytes']=(folder/'speech-draft.mp3').stat().st_size
    else:
        metadata['mp3_conversion']='failed; original WAV preserved'
    save_result(metadata,folder/'audio.manifest.draft.json')
    joined=copy.deepcopy(result)
    joined['audio']={'status':'generated','wav_file':'speech-draft.wav','mp3_file':metadata.get('mp3_file'),
                     'duration_seconds':metadata['audio']['duration_seconds'],'model':generator.model,
                     'voice':generator.voice,'manifest_file':'audio.manifest.draft.json','timing_cues':None,
                     'review':metadata['review']}
    save_result(joined,folder/'bundle.draft.result.json')
    summary.update({'outcome':'generated','audio':metadata['audio'],'mp3_bytes':metadata.get('mp3_bytes')})
    print('Generated real WAV; measured seconds:',metadata['audio']['duration_seconds'],flush=True)
except PipelineError as error:
    summary.update({'outcome':'failed','error':str(error)})
    print('FAIL:',str(error),flush=True)
summary['elapsed_seconds']=round(time.monotonic()-start,3)
save_result(summary,folder/'speech.draft.attempt1.summary.json')
print(json.dumps(summary,ensure_ascii=False),flush=True)
if summary['outcome']=='failed':raise SystemExit(2)
