// Experiment adapter around the existing owner, receipt, context and atomic tracker gates.
function streamContext(s){const cp=checkpoint(s),step=s.steps.find(v=>v.checkpoint_id===cp?.id);return {lab_session_id:s.lab_session_id,experiment_id:s.experiment_id,checkpoint_id:cp?.id||null,visit_id:step?.current_visit_id||null,lab_revision:s.revision,workspace_id:s.workspace.id,capture_epoch:s.workspace.capture_epoch,view_revision:s.workspace.view_revision,parameter_revision:s.workspace.parameter_revision,condition:s.workspace.condition};}
async function analyzeLabFrameStream(bytes,cp,state,env,emit){
 const {model,body}=buildLabRequest(bytes,cp,state,env),schema=body.generationConfig.responseJsonSchema;
 const order=['criteria','action_findings','uncertainties','summary'];schema.properties=Object.fromEntries(order.map(k=>[k,schema.properties[k]]));schema.required=order;
 schema.properties.criteria.minItems=cp.completion_criteria.length;schema.properties.action_findings.minItems=GUIDED_POLICY.procedures[cp.id].length;
 body.systemInstruction.parts[0].text+="\nSerialize top-level JSON fields in this order: criteria, action_findings, uncertainties, summary. Put the complete authored checkpoint decision findings first, then complete action findings, then critical uncertainties, and the short visible summary last. Keep every ID, status and supporting evidence. Do not emit a completion claim or generate next-step instructions.\nOcclusion check is mandatory before any wire or receiver_structure match: inspect the ENTIRE path from the named source output to the named destination input. A foreground settings dialog, panel or other window covering ANY part of that path makes the connection UNKNOWN, even when both endpoints and line pieces on both sides are visible and appear aligned. Never mentally join separated line fragments through an opaque window. receiver_structure requires BOTH receiver input paths fully visible end-to-end. modulated-wire and local-wire must each be unknown when their own paths are partly covered. Expected circuit topology, aligned line pieces and block names are not visible connection evidence.";
 const started=Date.now();let attempt=0,firstByte=null,firstFinding=null,criticalMs=null;
 const fetcher=typeof env.LAB_STREAM_FETCH==='function'?env.LAB_STREAM_FETCH:fetch;
 const consumed=await providerRequest(env,model,body,fetcher,{signal:emit.signal,
  async reset(){attempt++;firstByte=firstFinding=criticalMs=null;if(attempt>1)await emit({type:'attempt_reset',attempt});},
  async consume(response){const parser=new FindingParserJS(cp,GUIDED_POLICY.procedures[cp.id]),decoder=new SSEDecoderJS(),reader=response.body.getReader();let stopped=false,usage={},critical=false;
   try{while(true){const {value,done}=await reader.read();if(done)break;if(firstByte===null)firstByte=Date.now()-started;
    for(const data of decoder.feed(value)){
     if(data==='[DONE]')continue;let raw;try{raw=streamStrictJSON(data);}catch{throw Error('invalid_output');}
     const candidates=raw.candidates||[];if(!Array.isArray(candidates)||candidates.length>1)throw Error('invalid_output');
     if(candidates.length){const candidate=candidates[0],parts=candidate.content?.parts||[],text=parts.filter(p=>typeof p.text==='string'&&!p.thought).map(p=>p.text).join('');
      if(stopped&&(text||candidate.finishReason))throw Error('invalid_output');
      for(const event of parser.feed(text)){if(firstFinding===null)firstFinding=Date.now()-started;await emit({...event,attempt});}
      if(!critical&&['criteria','action_findings','uncertainties'].every(k=>parser.completed.has(k))){critical=true;criticalMs=Date.now()-started;await emit({type:'critical_fields_ready',attempt});}
      if(candidate.finishReason){if(candidate.finishReason!=='STOP')throw Error('incomplete_output');stopped=true;}
     }
     if(raw.usageMetadata)usage=raw.usageMetadata;
    }
   }decoder.finish();if(!stopped)throw Error('incomplete_output');return {value:validateLabResult(parser.finish(),cp,true),usage};
   }finally{await reader.cancel().catch(()=>{});}
  }});
 return {result:consumed.value,model,timing:{provider_ms:Date.now()-started,first_byte_ms:firstByte,first_finding_ms:firstFinding,critical_fields_ms:criticalMs,stream_attempts:attempt,output_tokens:consumed.usage.candidatesTokenCount??null,wire_format:'lab-observer-json-stream/v1'}};
}
async function labStreamRoute(request,env,owner,executionContext){
 const url=new URL(request.url),match=/^\/lab-sessions\/([a-f0-9-]{36})\/check-stream$/.exec(url.pathname);
 if(!match)return null;if(request.method!=='POST')labError(405,'POST required.');
 const id=match[1],s=await labLoad(env,id,owner),capture=await readState(request,env,s.workspace.capture_session_id,owner);
 if(capture.status!=='sharing')labError(409,'Share the current model before checking.');
 if(!providerConfigured(env))labError(503,'Configure GEMINI_API_KEYS in this test Site’s server secrets.');
 const meta=metadata(request.headers.get('x-capture-frame')),abort=new AbortController();let sequence=0,closed=false,admitted=null;
 const requestId=crypto.randomUUID();let task;
 const stream=new ReadableStream({start(controller){
  const push=event=>{if(closed||abort.signal.aborted)return;controller.enqueue(new TextEncoder().encode('data: '+JSON.stringify({schema:'lab-analysis-stream/v1',request_id:requestId,event_sequence:++sequence,server_time:nowISO(),context:admitted,...event})+'\n\n'));};
  const emit=Object.assign(async event=>{
   if(abort.signal.aborted)throw Error('analysis_cancelled');
   if(event.type==='admitted')admitted=event.context;
   else if(admitted){const current=await labLoad(env,id,owner);if(!current.runtime.capture_active||current.status!=='active'||JSON.stringify(streamContext(current))!==JSON.stringify(admitted))throw Error('stale_context');}
   push({...event,provisional:event.type!=='admitted'});
  },{signal:abort.signal});
  task=(async()=>{try{
   const result=await labAnalyze(env,s,request,owner,meta,capture,emit);
   if(abort.signal.aborted)return;
   if(admitted&&result.runtime.analysis_status==='available'){
    push({type:'guidance_committed',provisional:false,revision:result.revision,current_context:streamContext(result),guidance:result.guidance,queue:result.queue,status:result.status});
    push({type:'state_snapshot',provisional:false,state:result,current_context:streamContext(result)});
   }else push({type:'analysis_waiting',provisional:false,state:result});
   console.info(JSON.stringify({event:'analysis_stream_timing',request_id:requestId,checkpoint_id:admitted?.checkpoint_id||null,analysis_status:result.runtime.analysis_status,...result.runtime.last_analysis_timing}));
   push({type:'stream_complete',provisional:false,timing:result.runtime.last_analysis_timing||null});
  }catch(error){if(!abort.signal.aborted)push({type:error.status===409||error.message==='stale_context'?'discarded':'analysis_failed',provisional:false,status:error.status||502,reason:error.detail||'stream_failure',retry_after_ms:error.retry_after_ms||0});}
  finally{if(!closed){closed=true;controller.close();}}
  })();executionContext?.waitUntil(task);
 },cancel(){closed=true;abort.abort();}});
 return response(stream,200,{'Content-Type':'text/event-stream; charset=utf-8','Cache-Control':'no-store','X-Accel-Buffering':'no'});
}
