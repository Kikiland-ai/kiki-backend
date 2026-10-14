// Browser receives trusted analysis events; it never turns partial rows into evidence.
export async function consumeAnalysisStream(response,{expectedFrame,expectedContext,onEvent,signal}){
 if(!response.ok){const error=await response.json().catch(()=>({}));throw Object.assign(Error(error.detail||'The frame check could not start.'),{status:response.status,retry_after_ms:error.retry_after_ms});}
 if(!response.headers.get('content-type')?.includes('text/event-stream'))throw Error('The analyzer did not return a stream.');
 const reader=response.body.getReader(),decoder=new TextDecoder('utf-8',{fatal:true});let pending='',lines=[],requestId=null,protocol=null,last=0,terminal=false,admitted=false,total=0,finalState=null,coreSeen=false,admittedRevision=null;
 try{while(true){if(signal?.aborted)throw new DOMException('Cancelled','AbortError');const {value,done}=await reader.read();if(done)break;total+=value.length;if(total>4000000)throw Error('Analysis stream exceeded its limit.');pending+=decoder.decode(value,{stream:true});
  while(pending.includes('\n')){const index=pending.indexOf('\n'),line=pending.slice(0,index).replace(/\r$/,'');pending=pending.slice(index+1);
   if(line.startsWith('data:'))lines.push(line.slice(5).replace(/^ /,''));
   if(line||!lines.length)continue;const event=JSON.parse(lines.join('\n'));lines=[];
   if(!['lab-analysis-stream/v1','lab-analysis-stream/v2'].includes(event.schema)||typeof event.request_id!=='string'||!Number.isSafeInteger(event.event_sequence))throw Error('Invalid analysis event.');
   if(requestId===null){requestId=event.request_id;protocol=event.schema;}if(requestId!==event.request_id||protocol!==event.schema)throw Error('Foreign analysis request.');
   if(event.event_sequence<=last)continue;last=event.event_sequence;
   if(event.type==='admitted'){
    if(admitted||!event.frame||['frame_id','sha256','width','height','byte_count','view_revision'].some(k=>event.frame[k]!==expectedFrame[k]))throw Error('Analysis frame provenance changed.');
    if(Object.entries(expectedContext).some(([k,v])=>event.context?.[k]!==v))throw Error('Analysis context changed.');admitted=true;admittedRevision=event.context?.lab_revision;
   }else if(['provisional_findings','critical_fields_ready','guidance_committed','state_snapshot','attempt_reset'].includes(event.type)&&!admitted)throw Error('Finding arrived before admission.');
   if(event.type==='guidance_committed'&&event.schema==='lab-analysis-stream/v2'){
    const state=event.state,context=event.current_context;
    if(coreSeen||event.provisional!==false||!state||state.projection!=='committed-decision/v1'||!Number.isSafeInteger(state.revision)||state.revision!==event.revision||(Number.isSafeInteger(admittedRevision)&&state.revision<=admittedRevision)||state.lab_session_id!==expectedContext.lab_session_id||context?.lab_session_id!==state.lab_session_id||context.lab_revision!==state.revision||state.runtime?.last_analysis_timing?.frame_id!==expectedFrame.frame_id||JSON.stringify(state.queue)!==JSON.stringify(event.queue)||JSON.stringify(state.guidance)!==JSON.stringify(event.guidance)||JSON.stringify(state).length>131072)throw Error('Invalid committed decision.');
    if(state.queue.current_checkpoint_id!==context.checkpoint_id||['workspace_id','capture_epoch','view_revision'].some(key=>expectedContext[key]!==undefined&&context[key]!==expectedContext[key])||['id','capture_epoch','view_revision','parameter_revision','condition'].some(key=>state.workspace?.[key]!==context[key==='id'?'workspace_id':key]))throw Error('Committed context changed.');
    coreSeen=true;finalState=state;
   }
   if(event.type==='analysis_waiting'||(event.type==='state_snapshot'&&event.schema==='lab-analysis-stream/v1'))finalState=event.state;
   if(event.type==='analysis_failed'||event.type==='discarded')throw Object.assign(Error(event.reason||'The checked context changed.'),{status:event.status,retry_after_ms:event.retry_after_ms});
   if(event.type==='stream_complete')terminal=true;
   await onEvent(event);
  }
 }pending+=decoder.decode();if(pending.trim()||lines.length||!terminal||!finalState)throw Error('Analysis stream ended before a final state.');return finalState;
 }finally{await reader.cancel().catch(()=>{});}
}

// Resolve the authoritative core independently of the auxiliary tail. Callers
// must never install a late state_snapshot over a newer committed revision.
export function startAnalysisStream(response,options){
 let settle,fail,settled=false;
 const committed=new Promise((resolve,reject)=>{settle=resolve;fail=reject;});
 const completion=consumeAnalysisStream(response,{...options,onEvent:async event=>{
  await options.onEvent(event);
  if(!settled&&((event.schema==='lab-analysis-stream/v2'&&event.type==='guidance_committed')||event.type==='analysis_waiting')){settled=true;settle(event.state);}
 }}).then(state=>{if(!settled){settled=true;settle(state);}return state;},error=>{if(!settled){settled=true;fail(error);}throw error;});
 // The owner may await committed first, attaching its tail handler afterward.
 completion.catch(()=>{});committed.catch(()=>{});
 return {committed,completion};
}
