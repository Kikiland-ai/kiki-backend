"""Explicit bounded paired smoke on synthetic fixtures; never changes a lab.
Run deliberately with --live. This eight-call smoke is not a production benchmark.
"""
import argparse,asyncio,hashlib,json,statistics,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from prototypes.lab_tracking.analysis import GeminiAnalyzer
from prototypes.lab_tracking.definition import CHECKPOINTS
from prototypes.lab_tracking.provider import AnalysisFailure
from prototypes.json_stream.analysis import JsonStreamingAnalyzer,STREAM_SINK,SHORT_DECISION

async def main():
 parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');parser.add_argument('--arms',nargs='+',choices=['baseline','stream','stream-reference','priority-buffered','decision-buffered'],default=['stream-reference','stream']);parser.add_argument('--case');parser.add_argument('--manifest',default='fixtures/screen-reader-baseline/manifest.json');parser.add_argument('--repeats',type=int,default=1);parser.add_argument('--output',type=Path,default=Path('work/json-stream-smoke.json'));args=parser.parse_args()
 if not args.live:parser.error('Explicit --live required; provider calls can incur cost.')
 root=Path(__file__).resolve().parents[1];manifest=json.loads((root/args.manifest).read_text());records=[]
 baseline=GeminiAnalyzer();stream=JsonStreamingAnalyzer();cp=CHECKPOINTS['CP-DSB-05']
 state={'workspace':{'condition':'baseline','model_name':'dsb_demo_1'},'steps':{cp['id']:{'criteria':[]}},'responses':[],'current_visit_id':'controlled-stream-eval'}
 args.output.parent.mkdir(parents=True,exist_ok=True)
 cases=[c for c in manifest['cases'] if not args.case or c['id']==args.case]
 for i,case in enumerate(cases*args.repeats):
  for arm in (args.arms if i%2==0 else list(reversed(args.arms))):
   pixels=(root/case['image']).read_bytes();assert hashlib.sha256(pixels).hexdigest()==case['sha256'];started=time.monotonic();first=None
   async def sink(event):
    nonlocal first
    if event['type']=='provisional_findings' and first is None:first=time.monotonic()-started
   token=STREAM_SINK.set(sink if arm in ('stream','stream-reference') else None);short_token=SHORT_DECISION.set(arm!='stream-reference')
   from prototypes.lab_tracking.analysis import build_request
   from prototypes.json_stream.analysis import priority_request
   short=arm in ('stream','decision-buffered')
   request_body=build_request(pixels,cp,state,baseline.model) if arm=='baseline' else priority_request(pixels,cp,state,baseline.model,decision_only=short)
   row={'prompt_sha256':hashlib.sha256(request_body['systemInstruction']['parts'][0]['text'].encode()).hexdigest(),'request_sha256':hashlib.sha256(json.dumps(request_body,sort_keys=True).encode()).hexdigest(),'case':case['id'],'arm':arm,'image_sha256':case['sha256'],'model':baseline.model,'expected':case['expected_focused_findings']}
   try:
    if arm in ('priority-buffered','decision-buffered'):
     from prototypes.json_stream.analysis import priority_request
     from prototypes.lab_tracking.analysis import validate_result,AnalysisFindings
     response=await baseline.provider.post(baseline.model,request_body);raw=response.json();candidate=raw['candidates'][0]
     if candidate.get('finishReason')!='STOP':raise AnalysisFailure('incomplete_output')
     from prototypes.json_stream.parser import FindingParser
     parsed=FindingParser(cp,decision_only=short);parsed.feed(''.join(p['text'] for p in candidate['content']['parts'] if 'text' in p and not p.get('thought')).encode())
     result=AnalysisFindings(parsed.finish(),{'wire_format':'decision-buffered-control' if short else 'priority-json-buffered-control','output_tokens':raw.get('usageMetadata',{}).get('candidatesTokenCount')})
    else:result=await (stream if arm in ('stream','stream-reference') else baseline).analyze(pixels,cp,state)
    elapsed=time.monotonic()-started;actual={r['criterion_id'].split(':')[-1]:r['status'] for r in result['criteria']};actual.update({r['action_id'].split('/')[-1]:r['status'] for r in result['action_findings']})
    row.update(status='success',passed=all(actual.get(k)==v for k,v in case['expected_focused_findings'].items()),actual={k:actual.get(k) for k in case['expected_focused_findings']},total_seconds=round(elapsed,3),first_feedback_seconds=round(first if first is not None else elapsed,3),metrics=getattr(result,'metrics',{}))
   except AnalysisFailure as error:row.update(status='failure',category=str(error),passed=False,total_seconds=round(time.monotonic()-started,3))
   finally:STREAM_SINK.reset(token);SHORT_DECISION.reset(short_token)
   records.append(row);print(json.dumps(row),flush=True)
   report={'schema':'json-stream-smoke/v1','synthetic_only':True,'real_simulink_accuracy_claim':False,'production_latency_claim':False,'repeats_per_case_arm':args.repeats,'records':records}
   args.output.write_text(json.dumps(report,indent=2)+'\n')
   if row.get('category','').startswith('provider_http_429'):return
asyncio.run(main())
