// Explicit offline provider/Chrome-attestation fixtures; never a live proof.
import {readFileSync} from 'node:fs';
import {randomBytes,randomUUID,webcrypto} from 'node:crypto';
import worker from '../dist/server/index.js';
import {localDB} from './local-db.mjs';
export const fixtureImage=Buffer.from(readFileSync('scripts/fixtures/jpeg.txt','utf8'),'base64');
export const fixtureOrigin='https://kiki-screen-receiver.woodsycarp256.chatgpt.site';
export function fixtureEnv(){
 const env={DB:localDB(),CAPTURE_RECEIPT_KEY:randomBytes(32).toString('hex'),GEMINI_API_KEY:'explicit-offline-fixture',GUIDANCE_SAMPLE_KIND:'offline_replay',GUIDANCE_SOURCE_REVISION:'working-integration',GUIDANCE_CONFIGURATION_ID:'offline-same-worker',fixtureCalls:0,fixtureDelay:0};
 env.LAB_STREAM_FETCH=async(url,options)=>{
  env.fixtureCalls++;const b=JSON.parse(options.body),[raw,catalog]=b.contents[0].parts[0].text.split('\nAuthored drawing catalogue: '),ctx=JSON.parse(raw);
  const model={criteria:ctx.checkpoint.completion_criteria.map(c=>({criterion_id:c.id,status:'unknown',evidence:'Controlled offline fixture.'})),action_findings:ctx.procedure.map(a=>({action_id:a.id,status:'unknown',evidence:'Controlled offline fixture.'})),uncertainties:[]};
  if(catalog)model.screen_guidance=JSON.parse(catalog).map(action=>({action_id:action.action_id,mode:env.fixtureMode||'annotate',targets:env.fixtureMode==='none'?[]:action.required_target_ids.map(target_id=>({target_id,status:env.fixtureMode==='text_only'?'unresolved':'resolved',region:env.fixtureMode==='text_only'?null:{x:.25,y:.325,width:.18,height:.07}})),marks:env.fixtureMode&&env.fixtureMode!=='annotate'?[]:[{kind:'box',cue_id:'focus',target_id:action.required_target_ids[0]},{kind:'text',cue_id:'note',anchor:{target_id:action.required_target_ids[0],u:0,v:1},text_ref:Object.hasOwn(action.overlay_texts,'canonical_instruction')?'canonical_instruction':'action_title'}]}));
  const whole=JSON.stringify(model),cut=whole.indexOf(',"screen_guidance"'),encoder=new TextEncoder(),prefix=cut<0?whole:whole.slice(0,cut);
  return new Response(new ReadableStream({async start(c){const send=(text,stop)=>c.enqueue(encoder.encode('data: '+JSON.stringify({candidates:[{content:{parts:[{text}]},...(stop?{finishReason:env.fixtureFinish||'STOP'}:{})}]})+'\n\n'));
   try{send(prefix,false);if(env.fixtureBarrier)await env.fixtureBarrier;if(env.fixtureDelay)await new Promise(r=>setTimeout(r,env.fixtureDelay));send(cut<0?'':whole.slice(cut),true);c.close();}catch{}}}),{headers:{'Content-Type':'text/event-stream'}});
 };return env;
}
export function fixtureRequest(path,method='GET',body=null,cookie=null,extra={}){return new Request(fixtureOrigin+path,{method,headers:{Origin:fixtureOrigin,'oai-authenticated-user-id':'guidance-offline-owner',...(cookie?{Cookie:cookie}:{}),...extra},...(body===null?{}:{body:body instanceof Uint8Array?body:JSON.stringify(body)})});}
export async function seedCheckpoint(env,state,cp='CP-DSB-03'){
 state.queue.current_checkpoint_id=cp;state.queue.upcoming_checkpoint_ids=state.queue.upcoming_checkpoint_ids.filter(id=>id>cp);const step=state.steps.find(s=>s.checkpoint_id===cp);step.status='in_progress';step.current_visit_id=randomUUID();step.visits=[step.current_visit_id];step.timing.entered_at=new Date().toISOString();
 await env.DB.prepare('UPDATE lab_sessions SET state_json=? WHERE id=?').bind(JSON.stringify(state),state.lab_session_id).run();return state;
}
export async function setupGuidance(){
 const env=fixtureEnv(),call=(path,method='GET',body=null,cookie=null,extra={})=>worker.fetch(fixtureRequest(path,method,body,cookie,extra),env);
 let state=await(await call('/lab-sessions','POST',{operator_trial:true,model_name:'explicit_fixture',progression_mode:'screen_guided'})).json();state=await seedCheckpoint(env,state);
 let r=await call('/screen-sessions','POST');const captureId=(await r.json()).session_id;let cookie=r.headers.get('set-cookie').split(';')[0];
 const meta={type:'frame',capture_epoch:1,view_revision:1,sequence:1,captured_elapsed_ms:100,width:96,height:54,source_width:96,source_height:54,byte_count:fixtureImage.length,mime_type:'image/jpeg'};
 r=await call(`/screen-sessions/${captureId}/frame`,'POST',fixtureImage,cookie,{'Content-Type':'image/jpeg','X-Capture-Frame':JSON.stringify(meta)});cookie=r.headers.get('set-cookie').split(';')[0];const frame=JSON.parse(Buffer.from(r.headers.get('x-capture-observation'),'base64')).observation.latest_frame;
 state=await(await call(`/lab-sessions/${state.lab_session_id}/attach`,'POST',{revision:state.revision,capture_session_id:captureId},cookie)).json();
 const pair=await webcrypto.subtle.generateKey({name:'ECDSA',namedCurve:'P-256'},false,['sign','verify']),public_key=await webcrypto.subtle.exportKey('jwk',pair.publicKey),sessionId=randomUUID(),handle='kiki:'+randomUUID();
 const identity={mode:'live_tutor',public_key,sessionId,capture_handle:handle};
 const connection=await(await call(`/lab-sessions/${state.lab_session_id}/guidance/connect`,'POST',{identity,contract:'analysis-owned-guidance/v0.1',capture_session_id:captureId})).json();
 const proof={schema:'kiki-native-binding/v1',connection_id:connection.connection_id,challenge:connection.challenge,adapter_session_id:sessionId,capture_handle:handle,controller_origin:fixtureOrigin,binding:{adapter_session_id:sessionId,capture_handle:handle,ticket_id:randomUUID(),descriptor:{sessionId,revision:3,generation:3,visible:true,viewport:{width:960,height:540,zoom:1},freshness_probe:{schema:'screen-capture-probe/v1',token:'0123456789abcdef01234567',columns:16,rows:6,region:{x:.8,y:.8,width:.1,height:.1}}}},frame};
 const signature=Buffer.from(await webcrypto.subtle.sign({name:'ECDSA',hash:'SHA-256'},pair.privateKey,new TextEncoder().encode(JSON.stringify(proof)))).toString('base64');
 const headers={'Content-Type':'image/jpeg','X-Capture-Frame':JSON.stringify(meta),'X-Guidance-Contract':'analysis-owned-guidance/v0.1','X-Guidance-Connection':connection.connection_id,'X-Guidance-Attestation':JSON.stringify({proof,signature})};
 return {privateKey:pair.privateKey,env,call,state,cookie,frame,meta,headers,proof,connection,async check(){const r=await call(`/lab-sessions/${state.lab_session_id}/check-stream`,'POST',fixtureImage,cookie,headers);return r;}};
}
