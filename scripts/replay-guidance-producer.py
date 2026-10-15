"""Free control/drawing replay using actual analyzer + provider pool + LabService.
No cloud Site or model call. Synthetic pixels/findings cannot certify recognition.
"""
import argparse,asyncio,base64,hashlib,importlib.util,json,sys,tempfile,time
from uuid import uuid4
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
from contracts.lab_tracking import StartLab,AttachCapture,CheckFrame
from prototypes.lab_tracking.service import LabService
from prototypes.lab_tracking.procedure import PROCEDURES
from prototypes.json_stream.analysis import JsonStreamingAnalyzer,STREAM_SINK
from prototypes.json_stream.drawing_context import DRAWING_RUN
from prototypes.json_stream.guidance import DrawingRun
from prototypes.json_stream.guidance_check import check_with_drawing
from prototypes.json_stream.guidance_outbox import GuidanceOutbox
from prototypes.json_stream.guidance_trace import GuidanceTrace
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'docs/architecture/examples/analysis-owned-guidance/v0.1'
load=lambda name:json.loads((P/name).read_text())
clock=lambda:datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')

async def replay(arm,pair,write,revision,run_id):
    now=time.time();pixels=base64.b64decode((P/'frame.jpeg.b64').read_text());received=clock();admission=None
    capture={'status':'sharing','pixels':pixels,'frame':{'frame_id':pair,'view_revision':1,'capture_epoch':1,'sequence':1,'byte_count':len(pixels),'width':96,'height':54,'sha256':hashlib.sha256(pixels).hexdigest(),'server_received_unix':now,'server_received_at':received}}
    trace=GuidanceTrace(write,request_id=pair+'-'+arm,pair_id=pair,arm=arm,sample_kind='offline_replay',model='gemini-3.5-flash-lite',configuration_id='fixture-cp01-chunk64-batched-perchunk',source_revision=revision,run_id=run_id)
    async def transport(request):
        body=json.loads(request.content);cp=json.loads(body['contents'][0]['parts'][0]['text'].split('\nAuthored')[0])['checkpoint']
        value={'criteria':[{'criterion_id':c['id'],'status':'unknown','evidence':'Synthetic replay only.'} for c in cp['completion_criteria']], 'action_findings':[{'action_id':a['id'],'status':'unknown','evidence':'Synthetic replay only.'} for a in PROCEDURES[cp['id']]],'uncertainties':[]}
        if arm=='drawing_v1':value['screen_guidance']=[{'action_id':'CP-DSB-01/create','mode':'annotate','targets':[{'target_id':'workspace.canvas','status':'resolved','region':{'x':.1,'y':.1,'width':.7,'height':.7}}],'marks':[{'kind':'box','cue_id':'workspace','target_id':'workspace.canvas'}]}]
        text=json.dumps(value)
        class Bytes(httpx.AsyncByteStream):
            async def __aiter__(self):
                for start in range(0,len(text),64):
                    yield ('data: '+json.dumps({'candidates':[{'content':{'parts':[{'text':text[start:start+64]}]},**({'finishReason':'STOP'} if start+64>=len(text) else {})}]})+'\n\n').encode()
                    await asyncio.sleep(0)
        return httpx.Response(200,stream=Bytes())
    analyzer=JsonStreamingAnalyzer(api_key='synthetic',transport=httpx.MockTransport(transport),io_mode='batched')
    with tempfile.TemporaryDirectory() as directory:
        service=LabService(Path(directory),lambda sid,owner:capture,analyzer=analyzer)
        try:
            s=service.start('synthetic-owner',StartLab(model_name='synthetic',operator_trial=True,progression_mode='screen_guided'));id=s['lab_session_id']
            s=service.attach(id,'synthetic-owner',AttachCapture(revision=s['revision'],capture_session_id='fixture'))
            def admit(px,cp,state):
                nonlocal admission
                a=load('input.single.json');a.update(analysis_request_id=pair+'-'+arm,admitted_context=service.context(state),current_action_id='CP-DSB-01/create')
                a['frame'].update(frame_id=pair,received_at=received,admitted_at=clock(),view_revision=1)
                a['frame_handle']['expires_at']=datetime.fromtimestamp(time.time()+8,timezone.utc).isoformat()
                a['eligible_actions']=[{'action_id':'CP-DSB-01/create','checkpoint_id':cp['id'],'teaching_intent':'show_action_target','canonical_instruction':PROCEDURES[cp['id']][0]['title'],'canonical_reason':'Synthetic fixture.', 'required_target_ids':['workspace.canvas'],'target_labels':{'workspace.canvas':'Selected canvas'},'subcriteria':{'workspace.canvas':['CP-DSB-01:workspace']},'overlay_texts':{'label':'Selected canvas'},'relationships':[]}]
                admission=a;return a
            def project(state):
                cp=state['queue']['current_checkpoint_id']
                return {'session_status':state['status'],'observation_status':'available','current_context':service.context(state),'admitted_context':admission['admitted_context'],'current_action_id':'CP-DSB-01/create', 'analysis_request_id':admission['analysis_request_id'],**{k:admission[k] for k in ('frame','frame_handle','source_binding')},'canonical_instruction':PROCEDURES[cp][0]['title'],'expected_criterion_ids':[c['criterion_id'] for c in state['steps'][cp]['criteria']],'expected_action_ids':[a['id'] for a in PROCEDURES[cp]],'now':clock()}
            async def sink(event):pass
            token=STREAM_SINK.set(sink);started=time.monotonic()
            try:
                body=CheckFrame(revision=s['revision'],frame_id=pair,view_revision=1)
                if arm=='drawing_v1':await check_with_drawing(service,id,'synthetic-owner',body,run=DrawingRun(admit,trace),outbox=GuidanceOutbox(service.store),stream_id='synthetic-stream',project_runtime=project)
                else:
                    trace.emit('admitted',image_bytes=len(pixels));result=await service.check(id,'synthetic-owner',body)
                    trace.emit('analysis_validated',**result['runtime']['last_analysis_timing'])
                    trace.emit('tracker_committed',commit_finished_ms=round((time.monotonic()-started)*1000),**result['runtime']['last_analysis_timing'])
            except Exception as error:
                trace.emit('discarded' if getattr(error,'status_code',None)==409 else 'failed',reason=str(error))
            finally:STREAM_SINK.reset(token)
        finally:service.store.db.close()

async def main(args):
    source_files=[*sorted((ROOT/'prototypes/json_stream').glob('*.py')),ROOT/'contracts/lab_observer_drawing.v1.schema.json']
    revision='working-tree-sha256:'+hashlib.sha256(b''.join(p.read_bytes() for p in source_files)).hexdigest()
    args.output.mkdir(parents=True,exist_ok=True);path=args.output/'timings.jsonl'
    rows=[];run_id=str(uuid4())
    with path.open('w') as f:
        def write(record):rows.append(record);f.write(json.dumps(record)+'\n');f.flush()
        for n in range(args.pairs):
            # Alternate order to avoid always warming the same arm first.
            for arm in (('control','drawing_v1') if n%2==0 else ('drawing_v1','control')):await replay(arm,'synthetic-pair-'+str(n),write,revision,run_id)
    spec=importlib.util.spec_from_file_location('compare',ROOT/'scripts/compare-guidance-traces.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    report=mod.summarize(rows);(args.output/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    errors=sum(row['stage'] in ('failed','discarded') for row in rows)
    print(json.dumps({'schema':'guidance-producer-evaluation/v1','pairs':args.pairs,'paid_model_calls':0,'errors':errors,'logs':str(path),'comparison':str(args.output/'comparison.json'),'sample_kind':'offline_replay','live_latency_measured':False}))
    if errors:raise SystemExit(1)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--pairs',type=int,default=5);parser.add_argument('--output',type=Path,default=ROOT/'work/evaluations/guidance-v1');args=parser.parse_args()
    if not 1<=args.pairs<=100:parser.error('--pairs must be 1..100')
    asyncio.run(main(args))
