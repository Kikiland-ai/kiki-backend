"""No provider calls; verify batching boundaries and stale-group rejection."""
import unittest
from prototypes.json_stream.context_batch import ContextBatch
from prototypes.lab_tracking.provider import AnalysisFailure
class ContextBatchTests(unittest.IsolatedAsyncioTestCase):
 async def test_chunk_shape_parity_including_no_gain_case(self):
  for chunks in (1,3,7):
   for mode in ('per_event','per_chunk'):
    reads=0;shown=[];events=[{'id':i} for i in range(7)]
    def read():
     nonlocal reads
     reads+=1;return True
    async def publish(group):shown.extend(group)
    gate=ContextBatch(mode,read,bool,publish)
    for i in range(chunks):await gate.batch(events[i*7//chunks:(i+1)*7//chunks])
    self.assertEqual(shown,events);self.assertEqual(reads,7 if mode=='per_event' else chunks)
 async def test_no_snapshot_cache_after_view_or_visit_change(self):
  current=True;shown=[]
  async def publish(group):shown.extend(group)
  gate=ContextBatch('per_chunk',lambda:current,bool,publish)
  await gate.batch([{'id':1},{'id':2}]);current=False
  with self.assertRaises(AnalysisFailure):await gate.batch([{'id':3},{'id':4}])
  self.assertEqual(shown,[{'id':1},{'id':2}]);self.assertEqual(gate.metrics['context_db_reads'],2)
 async def test_empty_and_bounded_group(self):
  async def publish(group):self.fail('Unexpected publish')
  gate=ContextBatch('per_chunk',lambda:self.fail('Unexpected read'),bool,publish)
  await gate.batch([])
  with self.assertRaises(AnalysisFailure):await gate.batch([{}]*65)
