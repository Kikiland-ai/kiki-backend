"""Refine a core-valid retained draft; record label repairs and preference warnings."""
import copy,importlib.util,json,os,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from prototypes.mixed_script.pipeline import GeminiGenerator,PipelineError,read_json,save_result,validate_input,validate_stage,occurrences,is_odia_letter
spec=importlib.util.spec_from_file_location('h','work/harden-profile-prompt.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
folder=Path('work/longer-vco-tts')
source=read_json(folder/'input.json')
retained=read_json(folder/'translation.attempt4.raw.json')

code=Path('work/trial-learner-language-profile-attempt2.py').read_text()
start=code.index('def normalize_language_spans(');end=code.index('\nclass ProfileGenerator',start)
namespace={'copy':copy,'is_odia_letter':is_odia_letter}
exec(code[start:end],namespace)
normalize=namespace['normalize_language_spans']
raw_draft,translation_repairs=normalize('translation',retained['response'])
translation=validate_stage(source,raw_draft,validate_input(source))
preference_warnings=[]
for original,translated in zip(source['sentences'],translation['sentences']):
    for phrase in h.PROFILE['retain_english_phrases']:
        expected=occurrences(original['english'],phrase)
        actual=occurrences(translated['display_text'],phrase)
        if expected!=actual:preference_warnings.append({'sentence_id':original['id'],'phrase':phrase,'expected':expected,'actual':actual})
save_result({'response':raw_draft,'repairs':translation_repairs,'call':retained['call'],
             'core_validation':'passed','additional_phrase_warnings':preference_warnings},folder/'translation.attempt4.normalized.json')
request=h.build_request(source,'mixed',translation,'v2')
data=json.loads(request['contents'][0]['parts'][0]['text'])
data['preferred_phrase_counts_by_sentence']={s['id']:{p:occurrences(s['english'],p) for p in h.PROFILE['retain_english_phrases']} for s in source['sentences']}
request['contents'][0]['parts'][0]['text']=json.dumps(data,ensure_ascii=False)
request['systemInstruction']['parts'].append({'text':'Respect preferred_phrase_counts_by_sentence exactly, including zero counts. The draft is provisional: correct its phrase-count discrepancies while retaining the ORIGINAL claims, qualifiers, values and units. In s5 and s7 the original says ideal model, not ideal linear model; do not insert that longer selected phrase there. Keep all required spoken expansions exact. Return the original schema.'})
save_result(request,folder/'mixed.refinement.request.json')
generator=GeminiGenerator(os.environ.get('GEMINI_API_KEY',''),model='gemini-3.1-flash-lite',timeout=180)
summary={'model':generator.model,'reused_translation':'translation.attempt4.raw.json',
         'translation_core_validation':'passed_after_label_only_repair','translation_preference_warnings':preference_warnings,
         'new_translation_requests':0,'text_repair':False,'span_label_normalization':True,
         'scientific_and_native_review':'pending'}
print('Requesting mixed refinement of retained draft; no new translation request',flush=True)
start=time.monotonic()
try:
    raw_mixed=generator.generate('mixed',request)
    save_result({'response':raw_mixed,'call':generator.calls[-1]},folder/'mixed.refinement.raw.json')
    normalized,mixed_repairs=normalize('mixed',raw_mixed)
    mixed=validate_stage(source,normalized,validate_input(source))
    phrase_checks=h.check_preferences(source,mixed)
    result={
        'schema':'mixed-script/v1','prompt_version':'learner-profile-fewshot/v2+preferred-counts',
        'input_sha256':h.digest(source),
        'provenance':{'mode':'gemini','provider':'Gemini Developer API','model':generator.model,
                      'calls':[retained['call'],*generator.calls]},
        'source':source,'language_profile':h.PROFILE,'translation':translation,'mixed':mixed,
        'paragraph':' '.join(s['display_text'] for s in mixed['sentences']),
        'speech_script':' '.join(s['speech_text'] for s in mixed['sentences']),
        'validation':{'automated':'passed','checks':['sentence_ids','language_spans_after_label_repair','Odia_script','English_terms','protected_literals','numeric_values','spoken_expansions','final_preferred_phrase_counts'],
                      'meaning_review':'pending','native_Odia_review':'pending'},
        'experiment':{'translation_phrase_warnings':preference_warnings,'final_phrase_checks':phrase_checks,
                      'span_label_repairs':translation_repairs+mixed_repairs,'all_display_characters_preserved':True,
                      'speech_text_modified':False,'translation_reused':True,'new_api_requests':1},
        'audio':{'status':'not_generated','timing_cues':None},
    }
    save_result(result,folder/'script.result.json')
    for filename,text in {'translation.txt':' '.join(s['display_text'] for s in translation['sentences']),
                          'mixed-script.txt':result['paragraph'],'speech-ready.txt':result['speech_script']}.items():
        with (folder/filename).open('x',encoding='utf-8') as f:f.write(text+'\n')
    summary.update({'outcome':'passed_final_automated_checks','label_repaired_sentence_ids':[r['sentence_id'] for r in translation_repairs+mixed_repairs]})
    print('PASS: saved longer final mixed script and speech-ready text',flush=True)
    print(result['paragraph'],flush=True)
except PipelineError as error:
    summary.update({'outcome':'failed','error':str(error)})
    print('FAIL:',str(error),flush=True)
summary.update({'calls':generator.calls,'elapsed_seconds':round(time.monotonic()-start,3)})
save_result(summary,folder/'mixed.refinement.summary.json')
print(json.dumps(summary,ensure_ascii=False),flush=True)
if summary['outcome']=='failed':raise SystemExit(2)
