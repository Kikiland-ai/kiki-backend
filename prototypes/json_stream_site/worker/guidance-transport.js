/* Owned, opt-in live transport. State CAS + sequence + outbox append are batched
 * atomically in D1. Native source claims are signed by the connected extension;
 * this is an owner-authorized extension, not remote hardware attestation. */
const gSame=(a,b)=>JSON.stringify(a,Object.keys(a).sort())===JSON.stringify(b,Object.keys(b).sort());
// Provider generation uses one structural mark object instead of a four-way
// union. The unchanged full producer schema validates every returned kind.
class LiveDrawingRunJS extends DrawingRunJS {
 async extendRequest(...args){await super.extendRequest(...args);const body=args[0],marks=body.generationConfig.responseJsonSchema.properties.screen_guidance.items.properties.marks;
  const variants=marks.items.anyOf;if(variants){const properties={};for(const v of variants)for(const [key,value] of Object.entries(v.properties)){if(key==='kind'){properties.kind||={enum:[]};properties.kind.enum.push(...value.enum);}else properties[key]=value;}
   marks.items={type:'object',additionalProperties:false,required:['kind','cue_id'],properties};
   body.systemInstruction.parts[0].text+=' For each mark emit only the fields for its kind: box/ellipse use target_id; text uses text_ref and anchor; arrow uses relationship_id, from and to. Omit unrelated optional fields. Runtime validation enforces the complete typed contract.';
  }
 }
}
const G_CONTRACT='analysis-owned-guidance/v0.1';
const gJSON=value=>JSON.stringify(value);
const gNeed=(ok,message='Invalid guidance request.')=>{if(!ok)labError(422,message);};
const gNow=()=>new Date().toISOString();
async function gStream(env,id,owner,session){const row=await env.DB.prepare('SELECT * FROM guidance_streams WHERE id=? AND owner=? AND session_id=?').bind(id,owner,session).first();if(!row)labError(404,'Guidance connection not found.');return row;}
function gContext(s,last=null){if(!s.queue.current_checkpoint_id)return {...last,lab_revision:s.revision};return streamContext(s);}
function gCancelStatements(env,s,expected,eventType,eventId){
 if(eventType==='analysis_completed')return [];
 const context=s.queue.current_checkpoint_id?gContext(s):null;if(!context&&s.status!=='completed')return [];
 const reason=eventType==='capture_detached'||eventType==='session_paused'?'pause':eventType.includes('view')?'view_change':eventType.includes('parameter')||eventType.includes('condition')?'condition_change':s.status==='completed'?'step_change':'step_change';
 const cancel={schema:G_CONTRACT,message_type:'cancel',cancel_id:eventId,guidance_stream_id:'pending',cue_sequence:1,context:context||{},reason,issued_at:gNow()};
 const retire=eventType==='capture_detached'||eventType==='capture_attached'||s.status==='completed';
 const guard='session_id=? AND owner=? AND active=1 AND EXISTS (SELECT 1 FROM lab_sessions WHERE id=? AND mutation_id=?)';
 return [env.DB.prepare(`UPDATE guidance_streams SET sequence=sequence+1,fence_revision=MAX(fence_revision,?),publication_id=?,context_json=CASE WHEN ? IS NULL THEN json_set(context_json,'$.lab_revision',?) ELSE ? END WHERE ${guard}`).bind(eventType==='analysis_started'?expected:s.revision,eventId,context?gJSON(context):null,s.revision,context?gJSON(context):null,s.lab_session_id,s.owner_id,s.lab_session_id,eventId),
 env.DB.prepare(`INSERT INTO guidance_outbox(stream_id,sequence,publication_id,message_json,created_at) SELECT id,sequence,?||':'||id,json_set(?,'$.guidance_stream_id',id,'$.cue_sequence',sequence,'$.context',json(context_json)),? FROM guidance_streams WHERE session_id=? AND owner=? AND publication_id=? AND EXISTS(SELECT 1 FROM lab_sessions WHERE id=? AND mutation_id=?)`).bind(eventId,gJSON(cancel),Date.now(),s.lab_session_id,s.owner_id,eventId,s.lab_session_id,eventId),
 ...(retire?[env.DB.prepare('UPDATE guidance_streams SET active=0 WHERE session_id=? AND owner=? AND publication_id=?').bind(s.lab_session_id,s.owner_id,eventId)]:[])];
}
async function gVerify(request,env,s,bytes,capture){
 const id=request.headers.get('x-guidance-connection'),raw=request.headers.get('x-guidance-attestation');
 gNeed(id&&raw&&raw.length<12000,'Connect the new guidance extension to this shared tab.');
 const row=await gStream(env,id,s.owner_id,s.lab_session_id);gNeed(row.active&&row.capture_id===s.workspace.capture_session_id&&Date.now()-row.created_at<3600000,'Guidance attachment expired. Reconnect it.');
 let a;try{a=JSON.parse(raw);}catch{labError(422,'Invalid signed source attestation.');}
 const identity=JSON.parse(row.identity_json),proof=a.proof;
 gNeed(proof?.schema==='kiki-native-binding/v1'&&proof.connection_id===id&&proof.challenge===row.challenge&&proof.adapter_session_id===identity.sessionId&&proof.capture_handle===identity.capture_handle&&proof.controller_origin===new URL(request.url).origin,'Foreign source attestation.');
 const key=await crypto.subtle.importKey('jwk',identity.public_key,{name:'ECDSA',namedCurve:'P-256'},false,['verify']);
 let signature;try{signature=Uint8Array.from(atob(a.signature),c=>c.charCodeAt(0));}catch{labError(422,'Invalid source signature.');}
 gNeed(await crypto.subtle.verify({name:'ECDSA',hash:'SHA-256'},key,signature,new TextEncoder().encode(gJSON(proof))),'Source signature failed.');
 const f=proof.frame,d=proof.binding.descriptor;
 gNeed(f.frame_id===capture.latest.frame_id&&f.sha256===capture.latest.sha256&&f.byte_count===bytes.byteLength&&f.width===capture.latest.width&&f.height===capture.latest.height&&f.view_revision===s.workspace.view_revision,'Source proof does not match the admitted frame.');
 gNeed(proof.binding.adapter_session_id===identity.sessionId&&proof.binding.capture_handle===identity.capture_handle&&KikiFrameProbe.valid(d.freshness_probe)&&d.sessionId===identity.sessionId&&d.visible&&d.viewport.zoom===1&&d.revision>=1&&Math.abs(f.width/f.height-d.viewport.width/d.viewport.height)<.02,'Unverified source transform.');
 return {row,identity,proof};
}
function gAdmit(working,frame,verified,requestId){
 const observation=crypto.randomUUID(),handle=crypto.randomUUID(),d=verified.proof.binding.descriptor;
 return {schema:G_CONTRACT,message_type:'analysis_input',model_contract:'lab-observer-drawing/v1',analysis_request_id:requestId,
 admitted_context:streamContext(working),current_action_id:labProjection(working).guidance.current_action.id,
 frame:{observation_id:observation,frame_id:frame.frame_id,sha256:frame.sha256,byte_count:frame.byte_count,encoded_width:frame.width,encoded_height:frame.height,capture_elapsed_ms:frame.captured_elapsed_ms,capture_time_authority:'capture_client_monotonic',received_at:frame.server_received_at,admitted_at:new Date(working.runtime.last_analysis_started_ms).toISOString(),receipt_time_authority:'observer_server_utc',view_revision:frame.view_revision},
 frame_handle:{handle_id:handle,expires_at:new Date(frame.server_received_unix_ms+20000).toISOString(),media_type:'image/jpeg',access_policy:'same_owner_ephemeral'},
 source_binding:{binding_id:verified.identity.sessionId,binding_revision:d.revision,surface:'live_workspace',transform_revision:d.revision},eligible_actions:guidanceActions(working)};
}
async function gPublish(env,result,owner,run,verified,trace){
 const admission=run.admission;if(!run.model)return null;
 for(let attempt=0;attempt<3;attempt++){
  const current=await labLoad(env,result.lab_session_id,owner),row=await gStream(env,verified.row.id,owner,result.lab_session_id);
  if(current.revision!==result.revision||!row.active||row.fence_revision>=admission.admitted_context.lab_revision)labError(409,'Drawing was cancelled before publication.');
  if(!current.queue.current_checkpoint_id){trace.emit('discarded',{},'inactive_context');return null;}
  const existing=await env.DB.prepare('SELECT message_json FROM guidance_outbox WHERE publication_id=?').bind(admission.analysis_request_id).first();if(existing)return JSON.parse(existing.message_json);
  const projected=labProjection(current),binding=admission.source_binding;
  let packet;try{packet=buildCommittedDrawing(admission,run.model,{session_status:current.status,observation_status:projected.observation.status,admitted_context:admission.admitted_context,current_context:streamContext(current),current_action_id:projected.guidance.current_action.id,canonical_instruction:projected.guidance.instruction,analysis_request_id:admission.analysis_request_id,frame:admission.frame,frame_handle:admission.frame_handle,source_binding:binding,guidance_stream_id:row.id,cue_sequence:row.sequence+1,last_cue_sequence:row.sequence,expected_criterion_ids:LAB_DEFINITION.checkpoints.find(c=>c.id===admission.admitted_context.checkpoint_id).completion_criteria.map(c=>c.id),expected_action_ids:GUIDED_POLICY.procedures[admission.admitted_context.checkpoint_id].map(a=>a.id),now:gNow(),owner_id:owner,trusted_live_bindings:{[binding.binding_id]:{owner_id:owner,binding_revision:binding.binding_revision,transform_revision:binding.transform_revision,verified_frame:admission.frame,proof_kind:'native_capture_handle_and_pixel_match'}}});}
  catch(e){trace.emit('discarded',{},e.message);return null;}
  const publication=admission.analysis_request_id;
  const saved=await env.DB.batch([
   env.DB.prepare('UPDATE guidance_streams SET sequence=?,publication_id=?,context_json=? WHERE id=? AND owner=? AND active=1 AND sequence=? AND fence_revision<? AND EXISTS(SELECT 1 FROM lab_sessions WHERE id=? AND owner=? AND revision=?) AND NOT EXISTS(SELECT 1 FROM guidance_outbox WHERE publication_id=?)').bind(packet.cue_sequence,publication,gJSON(packet.context),row.id,owner,row.sequence,admission.admitted_context.lab_revision,current.lab_session_id,owner,current.revision,publication),
   env.DB.prepare('INSERT OR IGNORE INTO guidance_outbox(stream_id,sequence,publication_id,message_json,created_at) SELECT id,sequence,?,?,? FROM guidance_streams WHERE id=? AND owner=? AND publication_id=? AND sequence=?').bind(publication,gJSON(packet),Date.now(),row.id,owner,publication,packet.cue_sequence)
  ]);
  if(saved[0].meta.changes){trace.emit('published',{frame_age_at_commit_ms:Date.now()-Date.parse(packet.frame.received_at),screen_guidance_bytes:new TextEncoder().encode(gJSON(packet)).length});return packet;}
 }
 labError(409,'Guidance publication conflicted with a newer context.');
}
async function guidanceRoute(request,env,owner){
 const url=new URL(request.url),m=/^\/lab-sessions\/([a-f0-9-]{36})\/guidance\/(connect|events|clock|ack)$/.exec(url.pathname);if(!m)return null;
 const s=await labLoad(env,m[1],owner),kind=m[2];
 if(kind==='clock'&&request.method==='GET')return json({server_time_ms:Date.now(),clock_authority:'observer_server_utc',max_uncertainty_ms:250});
 if(kind==='connect'&&request.method==='POST'){
  const b=await labJSON(request),identity=b.identity;
  gNeed(s.runtime.capture_active&&s.status==='active'&&b.capture_session_id===s.workspace.capture_session_id,'Attach the shared tab first.');
  gNeed(b.contract===G_CONTRACT&&identity?.mode==='live_tutor'&&identity.public_key?.kty==='EC'&&identity.public_key.crv==='P-256'&&typeof identity.sessionId==='string'&&identity.capture_handle?.startsWith('kiki:'),'Unsupported guidance adapter.');
  try{await crypto.subtle.importKey('jwk',identity.public_key,{name:'ECDSA',namedCurve:'P-256'},false,['verify']);}catch{labError(422,'Invalid adapter public key.');}
  const id=crypto.randomUUID(),challenge=crypto.randomUUID(),context=streamContext(s),retirement=crypto.randomUUID(),cancel={schema:G_CONTRACT,message_type:'cancel',cancel_id:retirement,guidance_stream_id:'pending',cue_sequence:1,context:{},reason:'workspace_change',issued_at:gNow()};
  await env.DB.batch([env.DB.prepare('UPDATE guidance_streams SET active=0,sequence=sequence+1,fence_revision=MAX(fence_revision,?),publication_id=? WHERE session_id=? AND owner=? AND active=1').bind(s.revision,retirement,s.lab_session_id,owner),env.DB.prepare("INSERT INTO guidance_outbox(stream_id,sequence,publication_id,message_json,created_at) SELECT id,sequence,?||':'||id,json_set(?,'$.guidance_stream_id',id,'$.cue_sequence',sequence,'$.context',json(context_json)),? FROM guidance_streams WHERE session_id=? AND owner=? AND publication_id=?").bind(retirement,gJSON(cancel),Date.now(),s.lab_session_id,owner,retirement),env.DB.prepare('INSERT INTO guidance_streams(id,owner,session_id,capture_id,context_json,challenge,identity_json,created_at) VALUES(?,?,?,?,?,?,?,?)').bind(id,owner,s.lab_session_id,b.capture_session_id,gJSON(context),challenge,gJSON({public_key:identity.public_key,sessionId:identity.sessionId,capture_handle:identity.capture_handle}),Date.now())]);
  return json({connection_id:id,challenge,guidance_stream_id:id,model_contract:'lab-observer-drawing/v1',stream_contract:'lab-analysis-stream/v3',projection_contract:'committed-decision/v2',payload_contract:G_CONTRACT,controller_origin:url.origin,server_time_ms:Date.now(),max_clock_uncertainty_ms:250,max_capture_paint_reservation_ms:500});
 }
 const id=url.searchParams.get('connection')||request.headers.get('x-guidance-connection');const row=await gStream(env,id,owner,s.lab_session_id);
 if(kind==='events'&&request.method==='GET'){const after=Number(url.searchParams.get('after')||0);gNeed(Number.isSafeInteger(after)&&after>=0);const rows=await env.DB.prepare('SELECT message_json FROM guidance_outbox WHERE stream_id=? AND sequence>? ORDER BY sequence LIMIT 32').bind(id,after).all();return json({active:!!row.active,revision:s.revision,messages:rows.results.map(r=>JSON.parse(r.message_json))});}
 if(kind==='ack'&&request.method==='POST'){
  const b=await labJSON(request),ack=b.ack;validateGuidanceSchema(ack,DRAWING_SCHEMA);
  gNeed(ack.message_type==='delivery_ack'&&ack.guidance_stream_id===id&&ack.actual_surface!=='captured_frame'&&['live_rendered','text_only','cancelled','rejected'].includes(ack.status),'Invalid live exposure acknowledgement.');
  const message=await env.DB.prepare('SELECT message_json,created_at FROM guidance_outbox WHERE stream_id=? AND sequence=?').bind(id,ack.cue_sequence).first();gNeed(message,'Unknown exposure sequence.');
  const value=JSON.parse(message.message_json),cancel=value.message_type==='cancel';
  gNeed(ack.request_id===(cancel?null:value.analysis_request_id)&&ack.packet_id===(value.packet?.packet_id||null)&&ack.cancel_id===(cancel?value.cancel_id:null)&&gSame(ack.context,value.context),'Foreign exposure context.');
  if(ack.status!=='rejected'){
   const identity=JSON.parse(row.identity_json),key=await crypto.subtle.importKey('jwk',identity.public_key,{name:'ECDSA',namedCurve:'P-256'},false,['verify']);let signature;try{signature=Uint8Array.from(atob(b.signature||''),c=>c.charCodeAt(0));}catch{labError(422,'Invalid paint signature.');}
   gNeed(await crypto.subtle.verify({name:'ECDSA',hash:'SHA-256'},key,signature,new TextEncoder().encode(gJSON(ack))),'Paint acknowledgement signature failed.');
   if(!cancel){gNeed(ack.adapter_binding_id===value.source_binding.binding_id&&ack.transform_revision===value.source_binding.transform_revision&&gSame(ack.packet_context,value.context),'Foreign paint transform.');gNeed(Number.isFinite(Date.parse(ack.delivered_at))&&Date.parse(ack.delivered_at)<=Date.parse(value.validity.expires_at),'Paint occurred after expiry.');gNeed(ack.status===(value.outcome==='text_only'?'text_only':'live_rendered')&&ack.actual_surface===(value.outcome==='text_only'?'guide_panel':'live_workspace'),'Foreign paint surface.');}
  }
  // A signed exposure may arrive after a later context; recording history does
  // not authorize stale presentation, extend its expiry or mutate progress.

  const timing={schema:'guidance-delivery-timing/v1',request_id:ack.request_id,stream_id:id,sequence:ack.cue_sequence,sample_kind:env.GUIDANCE_SAMPLE_KIND||'live_provider',configuration_id:env.GUIDANCE_CONFIGURATION_ID||'drawing-integration-v1',source_revision:env.GUIDANCE_SOURCE_REVISION||'uncommitted',status:ack.status,commit_to_ack_ms:Date.now()-message.created_at,consumer_commit_to_paint_ms:Number.isFinite(b.commit_to_paint_ms)&&b.commit_to_paint_ms>=0?b.commit_to_paint_ms:null,consumer_delivered_at:ack.delivered_at,server_received_at:gNow(),late_context:s.revision!==value.context.lab_revision,paint_verified:['live_rendered','text_only'].includes(ack.status)};
  await env.DB.prepare('INSERT OR IGNORE INTO guidance_acks(ack_id,owner,stream_id,sequence,packet_id,received_at,ack_json,timing_json) VALUES(?,?,?,?,?,?,?,?)').bind(ack.ack_id,owner,id,ack.cue_sequence,ack.packet_id,Date.now(),gJSON(ack),gJSON(timing)).run();console.info(gJSON(timing));return json({recorded:true,assessment_effect:'none'});
 }
 labError(405,'Unsupported guidance operation.');
}
