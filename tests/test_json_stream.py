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
   self.calls.append(request);body=json.loads(request.content);cp=json.loads(body['contents'][0]['parts'][0]['text'])['checkpoint'];value=json.dumps(findings(cp));prefix='{"criteria": ['+json.dumps(findings(cp)['criteria'][0]);
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
  self.assertEqual(result['runtime']['candidate']['prompt_version'],'dsb-step-observer/v3-json-stream2');self.assertIn('admitted',events);self.assertEqual(result['runtime']['last_analysis_timing']['wire_format'],'lab-observer-json-stream/v1')
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
   body=json.loads(request.content);cp=json.loads(body['contents'][0]['parts'][0]['text'])['checkpoint'];text=json.dumps(findings(cp))
   data=('data: '+json.dumps({'candidates':[{'content':{'parts':[{'text':text}]},'finishReason':'STOP'}]})+'\n\n').encode()
   return httpx.Response(200,stream=BytesStream(data,b''))
  with tempfile.TemporaryDirectory() as directory:
   analyzer=JsonStreamingAnalyzer(api_key='fixture',transport=httpx.MockTransport(transport));app=create_app(Path(directory),analyzer=analyzer,proxy_secret='')
   pixels=b'controlled exact bytes';capture={'status':'sharing','pixels':pixels,'frame':{'frame_id':'capture:1:1','view_revision':1,'capture_epoch':1,'byte_count':len(pixels),'width':96,'height':54,'sha256':hashlib.sha256(pixels).hexdigest(),'server_received_unix':time.time(),'server_received_at':'fixture'}}
   app.state.lab.capture=lambda sid,owner:capture
   with TestClient(app) as client:
    client.get('/');headers={'origin':'http://testserver'}
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
