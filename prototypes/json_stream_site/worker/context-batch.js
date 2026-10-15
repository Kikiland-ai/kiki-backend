// One current-state read per group of findings already decoded from one transport
// chunk. No timer, TTL cache or speculative canonical state. Per-event is control.
function streamContextBatch({mode='per_chunk',signal,read,valid,push}){
 if(!['per_chunk','per_event'].includes(mode))throw Error('invalid_stream_context_configuration');
 const metrics={context_validation_mode:mode,context_db_reads:0,context_db_ms:0,context_batches:0,context_events:0,context_max_batch:0,provider_chunks:0};
 async function group(events){
  if(signal.aborted)throw Error('analysis_cancelled');
  const started=performance.now();let current;metrics.context_db_reads++;
  try{current=await read();}finally{metrics.context_db_ms=Math.round(metrics.context_db_ms+performance.now()-started);}
  if(signal.aborted)throw Error('analysis_cancelled');
  if(!valid(current))throw Error('stale_context');
  metrics.context_batches++;metrics.context_events+=events.length;metrics.context_max_batch=Math.max(metrics.context_max_batch,events.length);
  // Synchronous enqueue: a rejected group publishes none of its findings.
  for(const event of events)push(event);
 }
 async function batch(events){
  if(!Array.isArray(events)||events.length>64)throw Error('invalid_output');
  if(!events.length)return;
  if(mode==='per_event'){for(const event of events)await group([event]);}
  else await group(events);
 }
 return {batch,metrics};
}
export {streamContextBatch};
