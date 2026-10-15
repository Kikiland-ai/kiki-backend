"""Database optimization parity; synthetic provider transport, no paid calls."""
import asyncio,json,sqlite3,threading,unittest
from unittest.mock import patch
import httpx
from prototypes.json_stream.provider import StreamingProviderPool
from prototypes.lab_tracking.provider import AnalysisFailure

class ProviderIOTests(unittest.IsolatedAsyncioTestCase):
 def pool(self,mode,transport,keys=None,db=None):
  with patch.dict('os.environ',{'GEMINI_API_KEYS':json.dumps(keys or ['fixture-'+str(i) for i in range(4)])}):
   pool=StreamingProviderPool(io_mode=mode,transport=httpx.MockTransport(transport))
  db=db or sqlite3.connect(':memory:');pool.bind_store(db,threading.RLock());self.addCleanup(db.close);return pool,db
 async def run_stream(self,pool):
  metrics={}
  async def consume(response):return json.loads(await response.aread())
  async def reset():pass
  result=await pool.stream('fixture',{},consume,reset,metrics.update);return result,metrics
 async def test_four_queries_and_identical_round_robin(self):
  for mode,count in [('serial',17),('batched',4)]:
   seen=[]
   def transport(request):seen.append(request.headers['x-goog-api-key']);return httpx.Response(200,json={'fixture':True})
   pool,db=self.pool(mode,transport)
   for _ in range(2):
    result,metrics=await self.run_stream(pool);self.assertTrue(result['fixture']);self.assertEqual(metrics['provider_db_operations'],count)
    self.assertIsNone(db.execute('SELECT lease_owner FROM provider_rotation').fetchone()[0])
   self.assertEqual(seen,['fixture-0','fixture-1'])
 async def test_shared_quota_snapshot_refreshed_after_429(self):
  seen=[]
  def transport(request):
   key=request.headers['x-goog-api-key'];seen.append(key)
   return httpx.Response(429,headers={'Retry-After':'60'}) if key=='fixture-a' else httpx.Response(200,json={'ok':True})
  keys=[{'key':'fixture-a','quota_pool':'one'},{'key':'fixture-b','quota_pool':'one'},{'key':'fixture-c','quota_pool':'two'}]
  pool,_=self.pool('batched',transport,keys);await self.run_stream(pool);self.assertEqual(seen,['fixture-a','fixture-c'])
 async def test_full_failed_cycle_still_cools_down(self):
  seen=[]
  def transport(request):seen.append(request);return httpx.Response(503)
  pool,db=self.pool('batched',transport)
  for _ in range(2):
   with self.assertRaises(AnalysisFailure) as caught:await self.run_stream(pool)
   self.assertGreaterEqual(caught.exception.retry_at_ms,int(pool.clock()*1000)+59000)
  self.assertEqual(len(seen),4);self.assertIsNone(db.execute('SELECT lease_owner FROM provider_rotation').fetchone()[0])
 async def test_cancel_releases_atomic_lease(self):
  started=asyncio.Event();release=asyncio.Event()
  async def transport(request):started.set();await release.wait();return httpx.Response(200,json={})
  pool,db=self.pool('batched',transport);task=asyncio.create_task(self.run_stream(pool));await started.wait()
  with self.assertRaisesRegex(AnalysisFailure,'provider_rotation_busy'):await self.run_stream(pool)
  task.cancel()
  with self.assertRaises(asyncio.CancelledError):await task
  self.assertIsNone(db.execute('SELECT lease_owner FROM provider_rotation').fetchone()[0])

class UsageTelemetryTests(unittest.IsolatedAsyncioTestCase):
 async def test_actual_usage_is_metadata_not_model_findings(self):
  from prototypes.json_stream.analysis import JsonStreamingAnalyzer,STREAM_SINK
  from prototypes.lab_tracking.definition import CHECKPOINTS
  from prototypes.lab_tracking.procedure import PROCEDURES
  cp=CHECKPOINTS['CP-DSB-05']
  findings={'criteria':[{'criterion_id':c['id'],'status':'unknown','evidence':'Synthetic only.'} for c in cp['completion_criteria']],'action_findings':[{'action_id':a['id'],'status':'unknown','evidence':'Synthetic only.'} for a in PROCEDURES[cp['id']]],'uncertainties':[]}
  def transport(request):
   data={'candidates':[{'content':{'parts':[{'text':json.dumps(findings)}]},'finishReason':'STOP'}],'usageMetadata':{'promptTokenCount':123,'cachedContentTokenCount':20,'thoughtsTokenCount':7,'candidatesTokenCount':42,'totalTokenCount':172}}
   return httpx.Response(200,content=('data: '+json.dumps(data)+'\n\n').encode(),headers={'Content-Type':'text/event-stream'})
  analyzer=JsonStreamingAnalyzer(api_key='fixture',transport=httpx.MockTransport(transport))
  async def sink(event):pass
  token=STREAM_SINK.set(sink)
  try:result=await analyzer.analyze(b'fixture',cp,{'workspace':{'condition':'baseline','model_name':'fixture'},'steps':{cp['id']:{'criteria':[]}},'responses':[],'current_visit_id':'visit'})
  finally:STREAM_SINK.reset(token)
  self.assertEqual(result.metrics['input_tokens'],123);self.assertEqual(result.metrics['thinking_tokens'],7);self.assertEqual(result.metrics['cached_tokens'],20);self.assertEqual(result.metrics['total_tokens'],172)
  self.assertNotIn('input_tokens',result);self.assertEqual(result['criteria'],findings['criteria'])
