"""Reuse the hardened profile request and original pipeline for the longer trial."""
import importlib.util,json,sys,time
from pathlib import Path
spec=importlib.util.spec_from_file_location('hardening','work/harden-profile-prompt.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
folder=Path('work/longer-vco-tts')
source=h.read_json(folder/'input.json')
h.validate_input(source)

class LongerGenerator(h.TrialGenerator):
    def generate(self,stage,request):
        self.last_stage=stage
        data=json.loads(request['contents'][0]['parts'][0]['text'])
        request=h.build_request(source,stage,data.get('draft_translation'),'v2')
        h.save_result(request,folder/f'{stage}.attempt2.request.json')
        print('Request:',stage,flush=True)
        start=time.monotonic()
        try: generated=super(h.TrialGenerator,self).generate(stage,request)
        finally:self.stage_metrics.append({'stage':stage,'elapsed_seconds':round(time.monotonic()-start,3)})
        h.save_result({'response':generated,'call':self.calls[-1]},folder/f'{stage}.attempt2.raw.json')
        self.count_errors=h.count_diagnostics(source,generated)
        checked=h.validate_stage(source,generated,h.validate_input(source))
        self.phrase_checks.extend({'stage':stage,**check} for check in h.check_preferences(source,checked))
        print('Passed raw validation:',stage,flush=True)
        return generated

generator=LongerGenerator(source,'v2','longer-vco-attempt2')
generator.timeout=180
summary={'model':generator.model,'attempt':2,'timeout_seconds':180,'prompt_version':'learner-profile-fewshot/v2',
         'source_words':len(' '.join(s['english'] for s in source['sentences']).split()),
         'source_sentence_ids':[s['id'] for s in source['sentences']],
         'source_provenance':'assistant-authored adapted reference with synthetic ideal numerical example',
         'raw_validation':True,'postprocessing':False,'scientific_and_native_review':'pending'}
try:
    result=h.run_pipeline(source,generator)
    result['prompt_version']='learner-profile-fewshot/v2'
    result['language_profile']=h.PROFILE
    result['experiment']={'longer_paragraph':True,'phrase_checks':generator.phrase_checks,'postprocessing':False}
    h.save_result(result,folder/'script.result.json')
    outputs={'translation.txt':' '.join(s['display_text'] for s in result['translation']['sentences']),
             'mixed-script.txt':result['paragraph'],'speech-ready.txt':result['speech_script']}
    for filename,text in outputs.items():
        with (folder/filename).open('x',encoding='utf-8') as f:f.write(text+'\n')
    summary['outcome']='passed_all_automated_checks'
    print('PASS: saved longer translation, mixed script and speech-ready text',flush=True)
    print(result['paragraph'],flush=True)
except h.PipelineError as error:
    summary.update({'outcome':'failed','stage':generator.last_stage,'error':str(error),'count_diagnostics':generator.count_errors})
    print('FAIL:',str(error),flush=True)
summary.update({'calls':generator.calls,'stage_metrics':generator.stage_metrics})
h.save_result(summary,folder/'script.attempt2.summary.json')
print(json.dumps(summary,ensure_ascii=False),flush=True)
if summary['outcome']=='failed':raise SystemExit(2)
