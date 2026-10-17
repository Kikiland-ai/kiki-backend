// Full owned HTTP/SSE lab replay. Synthetic pixels and mocked vision, zero API calls.
import assert from 'node:assert/strict';
import {mock} from 'node:test';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {randomBytes} from 'node:crypto';
import worker from '../dist/server/index.js';
import {localDB} from './local-db.mjs';
export async function replayLab({ioMode='batched',contextMode='per_chunk'}={}){
 const definition=JSON.parse(await readFile('data/experiment.json','utf8')),policy=JSON.parse(await readFile('data/guided-policy.json','utf8'));
 const image=Buffer.from(await readFile('scripts/fixtures/jpeg.txt','utf8'),'base64'),DB=localDB();
 const records=[],env={DB,KIKI_PROVIDER_IO:ioMode,KIKI_STREAM_CONTEXT_MODE:contextMode,CAPTURE_RECEIPT_KEY:randomBytes(32).toString('hex'),GEMINI_API_KEYS:'["fixture-a","fixture-b","fixture-c","fixture-d"]'};
 let sequence=0,cookie,state,capture,mismatch=false,modelCalls=0;
 const req=(path,method='GET',body=null,extra={})=>new Request('https://receiver.test'+path,{method,headers:{'oai-authenticated-user-id':'replay-owner',Origin:'https://receiver.test',...(cookie?{Cookie:cookie}:{}),...(body?{'Content-Type':'application/json'}:{}),...extra},...(body?{body:body instanceof Uint8Array?body:JSON.stringify(body)}:{})});
 const call=async(path,method='GET',body=null,extra={})=>{const r=await worker.fetch(req(path,method,body,extra),env);if(r.headers.get('set-cookie'))cookie=r.headers.get('set-cookie').split(';')[0];assert.ok(r.ok,`${path}: ${r.status} ${r.ok?'':await r.text()}`);return r;};
 const mutate=async body=>{state=await(await call(`/lab-sessions/${state.lab_session_id}/action`,'POST',{revision:state.revision,...body})).json();};
 env.LAB_STREAM_FETCH=async(url,options)=>{
  modelCalls++;const context=JSON.parse(JSON.parse(options.body).contents[0].parts[0].text),status=mismatch?'mismatch':'match';
  const value={criteria:context.checkpoint.completion_criteria.map(c=>({criterion_id:c.id,status,evidence:'Synthetic replay finding; not real vision evidence.'})),action_findings:context.procedure.map(a=>({action_id:a.id,status:a.kind==='visible'?status:'unknown',evidence:'Synthetic replay action.'})),uncertainties:[]};
  return new Response('data: '+JSON.stringify({candidates:[{content:{parts:[{text:JSON.stringify(value)}]},finishReason:'STOP'}],usageMetadata:{promptTokenCount:123,cachedContentTokenCount:20,thoughtsTokenCount:7,candidatesTokenCount:42,totalTokenCount:172}})+'\n\n',{headers:{'Content-Type':'text/event-stream'}});
 };
 const check=async()=>{
  mock.timers.tick(3100);sequence++;
  const meta={type:'frame',capture_epoch:1,view_revision:1,sequence,captured_elapsed_ms:sequence*3100,width:96,height:54,source_width:96,source_height:54,byte_count:image.length,mime_type:'image/jpeg'};
  await call(`/screen-sessions/${capture}/frame`,'POST',image,{'Content-Type':'image/jpeg','X-Capture-Frame':JSON.stringify(meta)});
  const events=(await(await call(`/lab-sessions/${state.lab_session_id}/check-stream`,'POST',image,{'Content-Type':'image/jpeg','X-Capture-Frame':JSON.stringify(meta)})).text()).split('\n\n').filter(Boolean).map(row=>JSON.parse(row.slice(6)));
  assert.ok(events.some(e=>e.type==='guidance_committed'),'Complete STOP must commit');
  state=events.find(e=>e.type==='state_snapshot').state;
  assert.equal(state.runtime.last_analysis_timing.provider_db_operations,ioMode==='batched'?4:17);
  assert.equal(state.runtime.last_analysis_timing.input_tokens,123);
  assert.equal(state.runtime.last_analysis_timing.context_validation_mode,contextMode);
  assert.equal(state.runtime.last_analysis_timing.context_db_reads,contextMode==='per_chunk'?1:state.runtime.last_analysis_timing.context_events);
  records.push({frame_sequence:sequence,checkpoint:state.queue.current_checkpoint_id,done_count:state.queue.done_checkpoint_ids.length,revision:state.revision,mismatch,metrics:state.runtime.last_analysis_timing});
 };
 const originalInfo=console.info;console.info=()=>{};mock.timers.enable({apis:['Date'],now:Date.UTC(2026,9,15)});
 try{
  state=await(await call('/lab-sessions','POST',{operator_trial:true,model_name:'synthetic_replay',progression_mode:'screen_guided'})).json();
  capture=(await(await call('/screen-sessions','POST')).json()).session_id;
  await mutate({action:'note',text:'Synthetic automation run; no learner state.'});
  // Attach requires a valid receipt for an uploaded frame.
  sequence++;const initial={type:'frame',capture_epoch:1,view_revision:1,sequence,captured_elapsed_ms:0,width:96,height:54,source_width:96,source_height:54,byte_count:image.length,mime_type:'image/jpeg'};
  await call(`/screen-sessions/${capture}/frame`,'POST',image,{'Content-Type':'image/jpeg','X-Capture-Frame':JSON.stringify(initial)});
  state=await(await call(`/lab-sessions/${state.lab_session_id}/attach`,'POST',{revision:state.revision,capture_session_id:capture})).json();
  for(const cp of definition.checkpoints){
   assert.equal(state.queue.current_checkpoint_id,cp.id);
   const before=state.queue.done_checkpoint_ids.length;
   await check();assert.equal(state.queue.done_checkpoint_ids.length,before,'One frame cannot complete a checkpoint');
   if(cp.id==='CP-DSB-03'){
    mismatch=true;await check();assert.equal(state.queue.done_checkpoint_ids.length,before,'Contradictory settings cannot advance');mismatch=false;
    await check();assert.equal(state.queue.done_checkpoint_ids.length,before,'Contradiction resets support');
   }
   await check();
   if(state.queue.current_checkpoint_id===cp.id){
    const responses=cp.completion_criteria.filter(c=>policy.responses[c.id]);
    for(const criterion of responses)for(const response_kind of policy.responses[criterion.id])await mutate({action:'answer',response_kind,text:'Synthetic explicit learner report, unassessed.'});
    if(state.queue.current_checkpoint_id===cp.id){
     const pending=state.steps.find(s=>s.checkpoint_id===cp.id).criteria.filter(c=>c.state!=='satisfied').map(c=>c.criterion_id);
     assert.ok(pending.every(id=>(policy.confirmations[cp.id]||[]).includes(id)),`Unexpected pending criteria ${pending}`);
     await mutate({action:'review',criterion_ids:pending,review_note:'Synthetic explicit student confirmation only; not inferred from pixels.'});
    }
   }
   assert.equal(state.queue.done_checkpoint_ids.length,before+1,`${cp.id} must advance once`);
  }
  assert.equal(state.status,'completed');assert.equal(state.queue.done_checkpoint_ids.length,12);
  return {schema:'lab-replay/v1',passed:true,synthetic_only:true,vision_mocked:true,real_simulink_accuracy_claim:false,paid_model_calls:0,mocked_model_calls:modelCalls,io_mode:ioMode,context_mode:contextMode,checkpoints_completed:12,records};
 }finally{console.info=originalInfo;mock.timers.reset();DB.close();}
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
 const arg=(name,fallback)=>{const i=process.argv.indexOf(name);return i<0?fallback:process.argv[i+1];};
 const result=await replayLab({ioMode:arg('--io-mode','batched'),contextMode:arg('--context-mode','per_chunk')}),output=arg('--output','work/lab-replay.json');await mkdir(dirname(output),{recursive:true});await writeFile(output,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({passed:result.passed,checkpoints_completed:result.checkpoints_completed,paid_model_calls:0,report:output}));
}
