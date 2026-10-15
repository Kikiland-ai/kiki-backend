"""Validate a decoded chunk as a group; no TTL caching or canonical mutation."""
import time
from prototypes.lab_tracking.provider import AnalysisFailure

class ContextBatch:
    def __init__(self,mode,read,valid,publish):
        if mode not in ('per_chunk','per_event'):raise ValueError('invalid_stream_context_configuration')
        self.mode,self.read,self.valid,self.publish=mode,read,valid,publish
        self.metrics={'context_validation_mode':mode,'context_db_reads':0,'context_db_ms':0,'context_batches':0,'context_events':0,'context_max_batch':0,'provider_chunks':0,'context_delivery_db_reads':0,'context_delivery_db_ms':0}
    async def batch(self,events):
        if not isinstance(events,list) or len(events)>64:raise AnalysisFailure('invalid_output')
        groups=[[event] for event in events] if self.mode=='per_event' else ([events] if events else [])
        for group in groups:
            started=time.monotonic();self.metrics['context_db_reads']+=1
            try:current=self.read()
            finally:self.metrics['context_db_ms']+=round((time.monotonic()-started)*1000)
            if not self.valid(current):raise AnalysisFailure('stale_stream_context')
            self.metrics['context_batches']+=1;self.metrics['context_events']+=len(group);self.metrics['context_max_batch']=max(self.metrics['context_max_batch'],len(group))
            await self.publish(group)
