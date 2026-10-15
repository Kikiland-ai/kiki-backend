"""Offline stream/acceptance tests. Fixture findings are not vision accuracy evidence."""
import asyncio,copy,hashlib,io,json,tempfile,unittest
from pathlib import Path
import httpx
from PIL import Image
from contracts.lab_tracking import StartLab,AttachCapture,CheckFrame,ContextChange
from prototypes.lab_tracking.definition import CHECKPOINTS
from prototypes.lab_tracking.procedure import PROCEDURES
from prototypes.lab_tracking.provider import AnalysisFailure
from prototypes.lab_tracking.service import LabService
from prototypes.json_stream.parser import FindingParser,SSEDecoder
from prototypes.json_stream.analysis import JsonStreamingAnalyzer,STREAM_SINK,priority_request

def findings(cp):
 return {'criteria':[{'criterion_id':c['id'],'status':'unknown','evidence':'Controlled "phase", ଓଡ଼ିଆ.'} for c in cp['completion_criteria']], 'action_findings':[{'action_id':a['id'],'status':'unknown','evidence':'Controlled action.'} for a in PROCEDURES[cp['id']]],'uncertainties':[],'summary':'Controlled fixture, not a real lab.'}

def decision(cp):return {key:value for key,value in findings(cp).items() if key!='summary'}

class ParserTests(unittest.TestCase):
 def setUp(self):self.cp=CHECKPOINTS['CP-DSB-05'];self.value=findings(self.cp)
 def test_each_byte_boundary_and_early_row(self):
  raw=json.dumps(self.value,ensure_ascii=False).encode();parser=FindingParser(self.cp);events=[]
  for byte in raw:events+=parser.feed(bytes([byte]))
  self.assertEqual(parser.finish(),self.value);self.assertEqual(len([e for e in events if e['type']=='provisional_findings']),7)
  parser=FindingParser(self.cp);prefix=b'{"criteria":['+json.dumps(self.value['criteria'][0]).encode()
  self.assertEqual(parser.feed(prefix)[0]['type'],'provisional_findings');self.assertFalse(parser.closed)
 def test_strict_duplicate_missing_foreign_and_truncated_output(self):
  raw=json.dumps(self.value)
  cases=[raw[:-1],raw+'{}',raw.replace('"status": "unknown"','"status": "match", "status": "unknown"',1),raw.replace(self.value['criteria'][0]['criterion_id'],'foreign',1),json.dumps({**self.value,'action_findings':[]}),json.dumps({**self.value,'criteria':[self.value['criteria'][0]]*2}),raw.replace('"summary":','"extra": 1, "summary":')]
  for case in cases:
   with self.subTest(case=case[:40]),self.assertRaises(AnalysisFailure):
    parser=FindingParser(self.cp);parser.feed(case.encode());parser.finish()
 def test_fragmented_sse_and_incomplete_transport(self):
  raw=('data: '+json.dumps({'value':'ଓଡ଼ିଆ'},ensure_ascii=False)+'\r\n\r\n').encode();parser=SSEDecoder();events=[]
  for byte in raw:events+=parser.feed(bytes([byte]))
  parser.finish();self.assertEqual(json.loads(events[0])['value'],'ଓଡ଼ିଆ')
  parser=SSEDecoder();parser.feed(b'data: {}')
  with self.assertRaises(AnalysisFailure):parser.finish()
 def test_priority_schema_retains_full_authored_identifiers(self):
  body=priority_request(b'fixture',self.cp,{'workspace':{'condition':'baseline','model_name':'fixture'},'steps':{self.cp['id']:{'criteria':[]}},'responses':[],'current_visit_id':'visit'},'gemini-3.5-flash-lite')
  schema=body['generationConfig']['responseJsonSchema'];self.assertEqual(list(schema['properties']),['criteria','action_findings','uncertainties','summary']);self.assertEqual(schema['properties']['action_findings']['minItems'],5)
 def test_short_decision_is_independently_complete_and_rejects_auxiliary_fields(self):
  parser=FindingParser(self.cp,decision_only=True);parser.feed(json.dumps(decision(self.cp)).encode());result=parser.finish()
  self.assertTrue(result['summary'].startswith('Not established: Controlled'));self.assertEqual(result['criteria'],self.value['criteria'])
  with self.assertRaises(AnalysisFailure):
   parser=FindingParser(self.cp,decision_only=True);parser.feed(json.dumps(self.value).encode());parser.finish()

class BytesStream(httpx.AsyncByteStream):
 def __init__(self,prefix,suffix,release=None):self.prefix=prefix;self.suffix=suffix;self.release=release
 async def __aiter__(self):
  yield self.prefix
  if self.release:await self.release.wait()
  yield self.suffix

class PipelineTests(unittest.IsolatedAsyncioTestCase):
 async def asyncSetUp(self):
  self.temp=tempfile.TemporaryDirectory();self.now=1800000000;self.release=None;self.nonstop=False;self.calls=[]
  buffer=io.BytesIO();Image.new('RGB',(96,54),'white').save(buffer,'JPEG');self.pixels=buffer.getvalue()
  self.capture={'status':'sharing','pixels':self.pixels,'frame':{'frame_id':'capture:1:1','view_revision':1,'capture_epoch':1,'sequence':1,'byte_count':len(self.pixels),'width':96,'height':54,'sha256':hashlib.sha256(self.pixels).hexdigest(),'server_received_unix':self.now,'server_received_at':'fixture'}}
  async def transport(request):
   self.calls.append(request);body=json.loads(request.content);cp=json.loads(body['contents'][0]['parts'][0]['text'])['checkpoint'];value=json.dumps(decision(cp));prefix='{"criteria": ['+json.dumps(findings(cp)['criteria'][0]);
   def event(text,finish=None):return ('data: '+json.dumps({'candidates':[{'content':{'parts':[{'text':text}]},**({'finishReason':finish} if finish else {})}]})+'\n\n').encode()
   return httpx.Response(200,stream=BytesStream(event(prefix),event(value[len(prefix):],'MAX_TOKENS' if self.nonstop else 'STOP'),self.release))
  self.analyzer=JsonStreamingAnalyzer(api_key='fixture',transport=httpx.MockTransport(transport))
  self.service=LabService(Path(self.temp.name),lambda sid,owner:self.capture,analyzer=self.analyzer,clock=lambda:self.now)
  self.state=self.service.start('owner',StartLab(model_name='synthetic',operator_trial=True,progression_mode='screen_guided'))
  self.id=self.state['lab_session_id'];self.state=self.service.attach(self.id,'owner',AttachCapture(revision=self.state['revision'],capture_session_id='capture'))
 async def asyncTearDown(self):self.service.store.db.close();self.temp.cleanup()
 async def run_check(self,sink):
  token=STREAM_SINK.set(sink)
  try:return await self.service.check(self.id,'owner',CheckFrame(revision=self.state['revision'],frame_id=self.capture['frame']['frame_id'],view_revision=1))
  finally:STREAM_SINK.reset(token)
 async def test_partial_row_cannot_mutate_support_or_checkpoint_until_stop(self):
  self.release=asyncio.Event();seen=asyncio.Event();events=[]
  async def sink(event):
   events.append(event['type'])
   if event['type']=='provisional_findings':seen.set()
  task=asyncio.create_task(self.run_check(sink));await seen.wait();state=self.service.load(self.id,'owner')
  self.assertIsNone(state['runtime']['candidate']);self.assertEqual(state['queue']['done_checkpoint_ids'],[]);self.assertFalse(state.get('procedure_tracking'))
  self.release.set();result=await task
  self.assertEqual(result['runtime']['candidate']['prompt_version'],'dsb-step-observer/v4-short-decision1');self.assertIn('admitted',events);self.assertEqual(result['runtime']['last_analysis_timing']['wire_format'],'lab-observer-decision/v1')
 async def test_committed_core_releases_latch_and_provider_before_auxiliary_tail(self):
  from prototypes.json_stream.api import stream_router
  release=asyncio.Event();calls=0
  async def auxiliary(state):
   nonlocal calls
   calls+=1
   if calls==1:await release.wait()
  self.service.stream_auxiliary_hook=auxiliary
  endpoint=stream_router(self.service,lambda request:'owner',lambda request:None).routes[0].endpoint
  class Request:
   def __init__(request,body):request.body=body
   async def stream(request):yield json.dumps(request.body).encode()
  async def open_stream():
   state=self.service.load(self.id,'owner')
   response=await endpoint(self.id,Request({'revision':state['revision'],'frame_id':self.capture['frame']['frame_id'],'view_revision':1}))
   return response.body_iterator
  async def committed(iterator):
   while True:
    for packet in (await anext(iterator)).strip().split('\n\n'):
     event=json.loads(packet[6:])
     if event['type']=='guidance_committed':return event
  first=await open_stream();core=await committed(first)
  self.assertEqual(core['schema'],'lab-analysis-stream/v2');self.assertEqual(core['state']['projection'],'committed-decision/v1');self.assertNotIn('evidence',core['state'])
  self.assertIsNone(self.service.load(self.id,'owner')['runtime']['analysis_token'])
  self.assertIsNone(self.service.store.db.execute('SELECT lease_owner FROM provider_rotation').fetchone()[0])
  self.now+=3.1;self.capture['frame'].update(frame_id='capture:1:2',sequence=2,server_received_unix=self.now)
  second=await open_stream();newer=await committed(second);self.assertGreater(newer['revision'],core['revision'])
  async for event in second:pass
  release.set()
  async for event in first:pass
  self.assertEqual(self.service.load(self.id,'owner')['revision'],newer['revision'],'Late auxiliary delivery cannot save an older revision')
 async def test_api_context_modes_share_chunks_and_keep_delivery_context_checks(self):
  from prototypes.json_stream.api import stream_router
  for index,mode in enumerate(('per_event','per_chunk')):
   if index:
    self.now+=3.1;self.capture['frame'].update(frame_id='capture:1:2',sequence=2,server_received_unix=self.now)
   state=self.service.load(self.id,'owner')
   body={'revision':state['revision'],'frame_id':self.capture['frame']['frame_id'],'view_revision':1}
   class Request:
    async def stream(request):yield json.dumps(body).encode()
   endpoint=stream_router(self.service,lambda request:'owner',lambda request:None,context_mode=mode).routes[0].endpoint
   response=await endpoint(self.id,Request());packets=[]
   async for chunk in response.body_iterator:
    packets.extend(json.loads(packet[6:]) for packet in chunk.strip().split('\n\n'))
   result=next(e['state'] for e in packets if e['type']=='state_snapshot');timing=result['runtime']['last_analysis_timing']
   self.assertEqual(timing['context_validation_mode'],mode);self.assertEqual(timing['context_db_reads'],5 if mode=='per_event' else 2)
   tail=next(e['timing'] for e in packets if e['type']=='stream_complete')
   self.assertGreater(tail['context_delivery_db_reads'],0);self.assertNotIn('context_delivery_db_reads',timing);self.assertEqual(result['queue']['done_checkpoint_ids'],[])
 async def test_api_final_commit_rejects_view_change_after_last_finding(self):
  from prototypes.json_stream.api import stream_router
  self.release=asyncio.Event()
  async def transport(request):
   body=json.loads(request.content);cp=json.loads(body['contents'][0]['parts'][0]['text'])['checkpoint']
   def event(text,finish=False):return ('data: '+json.dumps({'candidates':[{'content':{'parts':[{'text':text}]},**({'finishReason':'STOP'} if finish else {})}]})+'\n\n').encode()
   return httpx.Response(200,stream=BytesStream(event(json.dumps(decision(cp))),event('',True),self.release))
  self.analyzer.provider.transport=httpx.MockTransport(transport)
  state=self.service.load(self.id,'owner');body={'revision':state['revision'],'frame_id':self.capture['frame']['frame_id'],'view_revision':1}
  class Request:
   async def stream(request):yield json.dumps(body).encode()
  endpoint=stream_router(self.service,lambda request:'owner',lambda request:None,context_mode='per_chunk').routes[0].endpoint
  response=await endpoint(self.id,Request());seen=asyncio.Event();packets=[]
  async def collect():
   async for chunk in response.body_iterator:
    for packet in chunk.strip().split('\n\n'):
     value=json.loads(packet[6:]);packets.append(value)
     if value['type']=='critical_fields_ready':seen.set()
  task=asyncio.create_task(collect());await asyncio.wait_for(seen.wait(),2)
  current=self.service.load(self.id,'owner');self.service.change(self.id,'owner',ContextChange(revision=current['revision'],action='view_changed',view_revision=2));self.release.set();await task
  self.assertTrue(any(e['type']=='discarded' for e in packets));self.assertFalse(any(e['type']=='guidance_committed' for e in packets));self.assertIsNone(self.service.load(self.id,'owner')['runtime']['candidate'])
 async def test_nonstop_has_no_candidate_and_preserves_progress(self):
  self.nonstop=True
  async def sink(event):pass
  result=await self.run_check(sink);self.assertIsNone(result['runtime']['candidate']);self.assertEqual(result['runtime']['analysis_status'],'waiting_for_provider')
 async def test_changed_view_discards_complete_stream(self):
  self.release=asyncio.Event();seen=asyncio.Event()
  async def sink(event):
   if event['type']=='provisional_findings':seen.set()
  task=asyncio.create_task(self.run_check(sink));await seen.wait();current=self.service.load(self.id,'owner')
  self.service.change(self.id,'owner',ContextChange(revision=current['revision'],action='view_changed',view_revision=2))
  self.release.set()
  from fastapi import HTTPException
  with self.assertRaises(HTTPException):await task
  self.assertIsNone(self.service.load(self.id,'owner')['runtime']['candidate'])
 async def test_cancel_releases_analysis_latch_and_provider_lease(self):
  self.release=asyncio.Event();seen=asyncio.Event()
  async def sink(event):
   if event['type']=='provisional_findings':seen.set()
  task=asyncio.create_task(self.run_check(sink));await seen.wait();task.cancel()
  with self.assertRaises(asyncio.CancelledError):await task
  current=self.service.load(self.id,'owner');self.assertIsNone(current['runtime']['analysis_token']);self.assertEqual(current['runtime']['analysis_status'],'cancelled')
  row=self.service.store.db.execute('SELECT lease_owner FROM provider_rotation').fetchone();self.assertIsNone(row[0])

if __name__=='__main__':unittest.main()

class StreamApiTests(unittest.TestCase):
 def test_owned_http_stream_has_priority_guidance_then_snapshot_and_no_cross_owner_access(self):
  from fastapi.testclient import TestClient
  from prototypes.backend.app import create_app
  import time
  async def transport(request):
   body=json.loads(request.content);cp=json.loads(body['contents'][0]['parts'][0]['text'])['checkpoint'];text=json.dumps(decision(cp))
   data=('data: '+json.dumps({'candidates':[{'content':{'parts':[{'text':text}]},'finishReason':'STOP'}]})+'\n\n').encode()
   return httpx.Response(200,stream=BytesStream(data,b''))
  with tempfile.TemporaryDirectory() as directory:
   analyzer=JsonStreamingAnalyzer(api_key='fixture',transport=httpx.MockTransport(transport));app=create_app(Path(directory),analyzer=analyzer,proxy_secret='')
   pixels=b'controlled exact bytes';capture={'status':'sharing','pixels':pixels,'frame':{'frame_id':'capture:1:1','view_revision':1,'capture_epoch':1,'byte_count':len(pixels),'width':96,'height':54,'sha256':hashlib.sha256(pixels).hexdigest(),'server_received_unix':time.time(),'server_received_at':'fixture'}}
   app.state.lab.capture=lambda sid,owner:capture
   with TestClient(app) as client:
    client.get('/');headers={'origin':'http://testserver'}
    self.assertIn('Short decision + async details',client.get('/').text)
    self.assertIn('startAnalysisStream',client.get('/static/lab.js').text)
    self.assertEqual(client.get('/static/json-stream-client.js').status_code,200)
    response_types=client.get('/openapi.json').json()['paths']['/lab-sessions/{lab_id}/check-stream']['post']['responses']['200']['content']
    self.assertIn('text/event-stream',response_types);self.assertNotIn('application/json',response_types)
    state=client.post('/lab-sessions',headers=headers,json={'model_name':'synthetic','operator_trial':True,'progression_mode':'screen_guided'}).json();lab_id=state['lab_session_id']
    state=client.post(f'/lab-sessions/{lab_id}/attach',headers=headers,json={'revision':state['revision'],'capture_session_id':'capture'}).json()
    body={'revision':state['revision'],'frame_id':'capture:1:1','view_revision':1}
    response=client.post(f'/lab-sessions/{lab_id}/check-stream',headers=headers,json=body)
    self.assertEqual(response.status_code,200,response.text)
    events=[json.loads(line[6:]) for line in response.text.split('\n\n') if line];types=[e['type'] for e in events]
    self.assertEqual(types[0],'admitted');self.assertLess(types.index('guidance_committed'),types.index('state_snapshot'));self.assertEqual(types[-1],'stream_complete')
    stranger=TestClient(app);stranger.get('/')
    self.assertEqual(stranger.post(f'/lab-sessions/{lab_id}/check-stream',headers=headers,json=body).status_code,404);stranger.close()
   app.state.store.db.close();app.state.lab.store.db.close()
