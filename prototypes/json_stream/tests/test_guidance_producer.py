"""Production producer components against independent synthetic protocol fixtures.
These are not target-recognition, renderer or live-latency acceptance tests.
"""
import asyncio
import base64
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import httpx
from fastapi import HTTPException
from contracts.lab_tracking import StartLab, AttachCapture, CheckFrame, ContextChange
from prototypes.lab_tracking.definition import CHECKPOINTS
from prototypes.lab_tracking.procedure import PROCEDURES
from prototypes.lab_tracking.provider import AnalysisFailure
from prototypes.lab_tracking.service import LabService
from prototypes.json_stream.analysis import JsonStreamingAnalyzer, STREAM_SINK
from prototypes.json_stream.drawing_context import DRAWING_RUN
from prototypes.json_stream.guidance import DrawingRun, validate_input, validate_model, build_committed, committed_state, provider_schema
from prototypes.json_stream.parser import FindingParser
from prototypes.json_stream.guidance_outbox import GuidanceOutbox
from prototypes.json_stream.guidance_trace import GuidanceTrace
P=Path(__file__).resolve().parents[3]/'docs/architecture/examples/analysis-owned-guidance/v0.1'
load=lambda name:json.loads((P/name).read_text())
pixels=base64.b64decode((P/'frame.jpeg.b64').read_text())

def runtime(name='single'):
    r=load('trusted.'+name+'.json')
    r.update(cue_sequence=1, canonical_instruction=next(a['canonical_instruction'] for a in r['eligible_actions'] if a['action_id']==r['current_action_id']))
    return r

class ContractRuntimeTests(unittest.TestCase):
    def test_production_projection_all_modes(self):
        for name in ('single','comparison','action-advance','none','declined','text-only','multi-unresolved'):
            source='action-advance' if name=='action-advance' else 'comparison' if name in ('comparison','multi-unresolved') else 'single'
            with self.subTest(name=name):
                admission=load('input.'+source+'.json');r=runtime(source);value=load('model.'+name+'.json')
                result=build_committed(admission,value,r)
                expected=load('committed.'+name+'.json')
                self.assertEqual(result['outcome'],expected['outcome'])
                self.assertEqual(result['action_id'],expected['action_id'])
                self.assertEqual(result['packet']['operations'] if result['packet'] else None,expected['packet']['operations'] if expected['packet'] else None)
                self.assertEqual(result['text_bindings'],expected['text_bindings'])
    def test_no_successor_does_not_relabel_current_geometry(self):
        result=build_committed(load('input.single.json'),load('model.single.json'),runtime('action-advance'))
        self.assertEqual(result['reason'],'no_matching_candidate');self.assertIsNone(result['packet'])
    def test_parser_each_byte_and_duplicate_foreign_nonfinite_late_tail(self):
        a=load('input.single.json');cp=CHECKPOINTS['CP-DSB-03'];value=load('model.single.json');raw=json.dumps(value).encode()
        p=FindingParser(cp,True,a)
        for b in raw:p.feed(bytes([b]))
        result=p.finish();self.assertNotIn('screen_guidance',result);self.assertEqual(p.drawing_result,value)
        for bad in [raw[:-1],raw+b'{}',raw.replace(b'"x": 0.2',b'"x": NaN'),raw.replace(b'"x": 0.2',b'"x": 1e309'),raw.replace(b'"cue_id": "note"',b'"cue_id": "focus-0"'),raw.replace(b'"text_ref": "canonical_instruction"',b'"text_ref": "foreign"'),raw.replace(b'"mode": "annotate"',b'"mode": "text_only"'),raw.replace(b'"x": 0.2',b'"x": 0.99')]:
            with self.subTest(bad=bad[-80:]),self.assertRaises(AnalysisFailure):
                p=FindingParser(cp,True,a);p.feed(bad);p.finish()
    def test_stale_foreign_expired_and_duplicate_provenance_rejected(self):
        a=load('input.single.json');m=load('model.single.json')
        for field,value in [('current_action_id','foreign'),('session_status','paused'),('now','2026-10-15T00:00:30Z'),('cue_sequence',0),('canonical_instruction','foreign')]:
            r=runtime();r[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):build_committed(a,m,r)
        for key in ('view_revision','parameter_revision','capture_epoch','condition','workspace_id'):
            r=runtime();r['current_context'][key]='foreign' if key in ('condition','workspace_id') else r['current_context'][key]+1
            with self.subTest(key=key),self.assertRaises(ValueError):build_committed(a,m,r)
        for key in ('frame_id','sha256','encoded_width'):
            r=runtime();r['frame'][key]='foreign' if key!='encoded_width' else 97
            with self.subTest(key=key),self.assertRaises(ValueError):build_committed(a,m,r)
    def test_actual_pixels_required_and_provider_schema_restricted(self):
        a=load('input.single.json');cp=CHECKPOINTS['CP-DSB-03'];validate_input(a,pixels,cp,a['admitted_context'])
        with self.assertRaises(ValueError):validate_input(a,pixels+b'x',cp,a['admitted_context'])
        schema=provider_schema(cp,[a['id'] for a in PROCEDURES[cp['id']]],a)
        self.assertEqual(list(schema['properties']),['criteria','action_findings','uncertainties','screen_guidance'])
        for forbidden in ('"$ref"','"if"','"then"','"allOf"','"const"'):self.assertNotIn(forbidden,json.dumps(schema))
    def test_comparison_retains_failures_and_separates_repeated_runs(self):
        root=P.parents[4]
        spec=importlib.util.spec_from_file_location('compare',root/'scripts/compare-guidance-traces.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        rows=[]
        for run_id in ('run-a','run-b'):
            for arm in ('control','drawing_v1'):
                trace=GuidanceTrace(rows.append,request_id='same-request',pair_id='same-case',arm=arm,sample_kind='offline_replay',model='fixture',run_id=run_id)
                trace.emit('admitted')
                trace.emit('failed',reason='provider_http_503') if arm=='drawing_v1' else trace.emit('tracker_committed',commit_finished_ms=5)
        report=module.summarize(rows)
        self.assertEqual(report['paired_cases'],2)
        self.assertEqual([g['requests'] for g in report['groups']],[2,2])
        drawing=next(g for g in report['groups'] if g['arm']=='drawing_v1')
        self.assertEqual(drawing['reasons'],{'provider_http_503':2});self.assertEqual(drawing['metrics']['commit_finished_ms']['n'],0)

    def test_log_records_do_not_expose_payload_or_keys(self):
        rows=[];t=GuidanceTrace(rows.append,request_id='request',pair_id='pair',arm='drawing_v1',sample_kind='offline_replay',model='fixture')
        t.emit('failed',reason='sensitive-provider-response',image_bytes=725,api_key='DO-NOT-LOG',summary='private screen')
        self.assertEqual(rows[0]['reason'],'provider_failure');self.assertNotIn('DO-NOT-LOG',json.dumps(rows));self.assertNotIn('private screen',json.dumps(rows))

class ChunkStream(httpx.AsyncByteStream):
    def __init__(self,parts,seen,release):self.parts=parts;self.seen=seen;self.release=release
    async def __aiter__(self):
        yield self.parts[0]
        self.seen.set()
        await self.release.wait()
        yield self.parts[1]

class PipelineRaceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.now=1792022402.0;self.seen=asyncio.Event();self.release=asyncio.Event();self.calls=[];self.logs=[];self.bad_stop=False;self.bad_tail=False
        self.capture={'status':'sharing','pixels':pixels,'frame':{'frame_id':'synthetic-frame','view_revision':1,'capture_epoch':1,'sequence':1,'byte_count':len(pixels),'width':96,'height':54,'sha256':hashlib.sha256(pixels).hexdigest(),'server_received_unix':self.now,'server_received_at':'2026-10-15T00:00:02Z','captured_elapsed_ms':2000}}
        async def transport(request):
            self.calls.append(request);body=json.loads(request.content);cp=json.loads(body['contents'][0]['parts'][0]['text'].split('\nAuthored')[0])['checkpoint']
            value={'criteria':[{'criterion_id':c['id'],'status':'unknown','evidence':'Synthetic only.'} for c in cp['completion_criteria']], 'action_findings':[{'action_id':a['id'],'status':'unknown','evidence':'Synthetic only.'} for a in PROCEDURES[cp['id']]], 'uncertainties':[], 'screen_guidance':[]}
            raw=json.dumps(value);cut=raw.index(', "screen_guidance"');prefix=raw[:cut];suffix=raw[cut:]+(' trailing' if self.bad_tail else '')
            def sse(text,stop=None):return ('data: '+json.dumps({'candidates':[{'content':{'parts':[{'text':text}]},**({'finishReason':stop} if stop else {})}]})+'\n\n').encode()
            return httpx.Response(200,stream=ChunkStream([sse(prefix),sse(suffix,'MAX_TOKENS' if self.bad_stop else 'STOP')],self.seen,self.release))
        self.analyzer=JsonStreamingAnalyzer(api_key='synthetic',transport=httpx.MockTransport(transport))
        self.service=LabService(Path(self.tmp.name),lambda sid,owner:self.capture,analyzer=self.analyzer,clock=lambda:self.now)
        state=self.service.start('owner',StartLab(model_name='synthetic',operator_trial=True,progression_mode='screen_guided'));self.id=state['lab_session_id']
        self.service.attach(self.id,'owner',AttachCapture(revision=state['revision'],capture_session_id='synthetic-capture'))
        self.run=DrawingRun(self.admit,GuidanceTrace(self.logs.append,request_id='synthetic-analysis',pair_id='race',arm='drawing_v1',sample_kind='offline_replay',model=self.analyzer.model))
    async def asyncTearDown(self):self.service.store.db.close();self.tmp.cleanup()
    def admit(self,px,cp,state):
        a=load('input.single.json');a['admitted_context']=self.service.context(state);a['current_action_id']='CP-DSB-01/create';a['analysis_request_id']='synthetic-analysis'
        a['eligible_actions']=[{'action_id':'CP-DSB-01/create','checkpoint_id':cp['id'],'teaching_intent':'show_action_target','canonical_instruction':PROCEDURES[cp['id']][0]['title'],'canonical_reason':'Synthetic fixture.', 'required_target_ids':['workspace.canvas'],'target_labels':{'workspace.canvas':'Selected canvas'},'subcriteria':{'workspace.canvas':['CP-DSB-01:workspace']},'overlay_texts':{'label':'Selected canvas'},'relationships':[]}]
        a['frame'].update(frame_id='synthetic-frame',received_at='2026-10-15T00:00:02Z',admitted_at='2026-10-15T00:00:02Z',view_revision=1)
        return a
    async def check(self):
        state=self.service.load(self.id,'owner');token=DRAWING_RUN.set(self.run)
        async def sink(e):pass
        st=STREAM_SINK.set(sink)
        try:return await self.service.check(self.id,'owner',CheckFrame(revision=state['revision'],frame_id=self.capture['frame']['frame_id'],view_revision=1))
        finally:STREAM_SINK.reset(st);DRAWING_RUN.reset(token)
    async def test_partial_findings_and_new_periodic_frame_cannot_mix_admission(self):
        task=asyncio.create_task(self.check());await asyncio.wait_for(self.seen.wait(),2)
        before=self.service.load(self.id,'owner');self.assertIsNone(before['runtime']['candidate']);self.assertIsNone(self.run.model)
        self.capture['frame']={**self.capture['frame'],'frame_id':'newer-frame','sequence':2,'sha256':'0'*64};self.capture['pixels']=pixels+b'new'
        self.release.set();state=await task
        self.assertEqual(state['runtime']['candidate']['source_frame']['frame_id'],'synthetic-frame')
        self.assertEqual(len(self.calls),1);self.assertEqual(self.run.admission['frame']['frame_id'],'synthetic-frame')
        self.assertEqual(self.logs[-1]['stage'],'analysis_validated');self.assertEqual(state['runtime']['last_analysis_timing']['wire_format'],'lab-observer-drawing/v1')
    async def test_view_invalidation_during_stream_cannot_save_progress(self):
        task=asyncio.create_task(self.check());await asyncio.wait_for(self.seen.wait(),2)
        state=self.service.load(self.id,'owner');self.service.change(self.id,'owner',ContextChange(revision=state['revision'],action='view_changed',view_revision=2))
        self.release.set()
        with self.assertRaises(HTTPException) as exc:await task
        self.assertEqual(exc.exception.status_code,409);self.assertIsNone(self.service.load(self.id,'owner')['runtime']['candidate'])
    async def test_missing_stop_and_malformed_tail_never_commit(self):
        for bad in ('bad_stop','bad_tail'):
            setattr(self,bad,True);self.release.set();state=await self.check()
            self.assertEqual(state['runtime']['analysis_status'],'waiting_for_provider');self.assertIsNone(self.run.model)
            setattr(self,bad,False)
            # Independent request after the failed provider cooldown.
            self.now+=70;self.run=DrawingRun(self.admit);self.capture['frame']['server_received_unix']=self.now
    async def test_outbox_sequences_cancel_duplicate_and_revision_fence(self):
        self.release.set();result=await self.check();outbox=GuidanceOutbox(self.service.store)
        def project(state):
            r=runtime();r.update(current_context=self.service.context(state),admitted_context=self.run.admission['admitted_context'],current_action_id='CP-DSB-01/create',analysis_request_id='synthetic-analysis',frame=self.run.admission['frame'],frame_handle=self.run.admission['frame_handle'],source_binding=self.run.admission['source_binding'],canonical_instruction=PROCEDURES['CP-DSB-01'][0]['title'],expected_criterion_ids=[c['id'] for c in CHECKPOINTS['CP-DSB-01']['completion_criteria']],expected_action_ids=[a['id'] for a in PROCEDURES['CP-DSB-01']],now='2026-10-15T00:00:03Z')
            return r
        def append(**kw):return outbox.append(owner='owner',lab_id=self.id,stream_id='stream',expected_revision=result['revision'],project_runtime=project,admission=self.run.admission,model=self.run.model,**kw)
        correct=deepcopy(self.run.model);self.run.model['criteria'][0]['evidence']='Different analysis.'
        with self.assertRaisesRegex(ValueError,'foreign_analysis_result'):append()
        self.run.model=correct
        first=append();self.assertEqual(first['cue_sequence'],1)
        with self.assertRaisesRegex(ValueError,'duplicate_publication'):append()
        cancel=append(cancel={'cancel_id':'cancel-1','reason':'view_change'});self.assertEqual(cancel['cue_sequence'],2)
        with self.assertRaisesRegex(ValueError,'cancelled_context'):append()
        state=self.service.load(self.id,'owner');self.service.change(self.id,'owner',ContextChange(revision=state['revision'],action='view_changed',view_revision=2))
        with self.assertRaisesRegex(ValueError,'revision_conflict'):append()
        count=self.service.store.db.execute('SELECT COUNT(*) FROM drawing_outbox').fetchone()[0];self.assertEqual(count,2)
