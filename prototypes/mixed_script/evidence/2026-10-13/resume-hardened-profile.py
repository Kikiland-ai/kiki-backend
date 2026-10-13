"""One delayed retry of the failed mixed request; reuse validated translation."""
import copy
import json
import time
from pathlib import Path
import importlib.util
spec=importlib.util.spec_from_file_location('harden_profile_prompt','work/harden-profile-prompt.py')
harness=importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)
ROOT,TrialGenerator,PROFILE=harness.ROOT,harness.TrialGenerator,harness.PROFILE
PipelineError,check_preferences,digest=harness.PipelineError,harness.check_preferences,harness.digest
read_json,run_pipeline,save_result=harness.read_json,harness.run_pipeline,harness.save_result
validate_input,validate_stage,DEFAULT_INPUT=harness.validate_input,harness.validate_stage,harness.DEFAULT_INPUT

RUN_ID='labels-v2-resume'
raw=read_json(ROOT/'labels-v2-translation.raw.json')
source=read_json(DEFAULT_INPUT)

class ResumeGenerator(TrialGenerator):
    def generate(self,stage,request):
        if stage!='translation':return super().generate(stage,request)
        checked=validate_stage(source,raw['response'],validate_input(source))
        self.phrase_checks.extend({'stage':stage,**c} for c in check_preferences(source,checked))
        self.calls.append(copy.deepcopy(raw['call']))
        self.stage_metrics.append({'stage':stage,'elapsed_seconds':0,'reused':True})
        print('Reusing validated translation from labels-v2; no translation request sent',flush=True)
        return copy.deepcopy(raw['response'])

summary_path=ROOT/f'{RUN_ID}.summary.json'
if summary_path.exists():raise SystemExit('Resume artifact exists; preserved')
backoff=time.time()-(ROOT/'labels-v2.summary.json').stat().st_mtime
print('Elapsed since failed run:',round(backoff,1),'seconds',flush=True)
if backoff<10:raise SystemExit('Wait for bounded backoff before the single retry')
generator=ResumeGenerator(source,'v2',RUN_ID)
summary={'run_id':RUN_ID,'version':'v2','case':'vco','reused_translation_from':'labels-v2',
         'backoff_seconds':round(backoff,1),'model':generator.model,'postprocessing':False,
         'semantic_review':'pending','native_Odia_review':'pending'}
try:
    result=run_pipeline(source,generator)
    previous=read_json(ROOT/'labels-v2-mixed.request.json')
    retried=read_json(ROOT/f'{RUN_ID}-mixed.request.json')
    assert digest(previous)==digest(retried)
    result['prompt_version']='learner-profile-fewshot/v2'
    result['language_profile']=PROFILE
    result['experiment']={'run_id':RUN_ID,'reused_translation_from':'labels-v2',
                          'same_mixed_request_retried':True,'new_api_requests':1,
                          'phrase_checks':generator.phrase_checks,'postprocessing':False,
                          'scientific_and_native_review':'pending'}
    save_result(result,ROOT/f'{RUN_ID}.result.json')
    summary['outcome']='passed_all_automated_checks'
    summary['same_mixed_request_retried']=True
    print('PASS: full original VCO flow with unchanged v2 prompt',flush=True)
except PipelineError as error:
    summary.update({'outcome':'failed','stage':generator.last_stage,'error':str(error),
                    'term_count_diagnostics':generator.count_errors})
    print('FAIL:',str(error),flush=True)
summary.update({'calls':generator.calls,'stage_metrics':generator.stage_metrics,
                'new_api_requests':sum(not metric.get('reused',False) for metric in generator.stage_metrics)})
save_result(summary,summary_path)
print(json.dumps(summary,ensure_ascii=False),flush=True)
