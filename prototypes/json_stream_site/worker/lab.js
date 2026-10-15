const labError=(status,detail)=>{throw {status,detail};};
const clone=value=>structuredClone(value);
const nowISO=()=>new Date().toISOString();
const checkpoint=s=>LAB_DEFINITION.checkpoints.find(c=>c.id===s.queue.current_checkpoint_id);
function labDB(env){if(!env.DB)labError(503,'Lab storage is not configured. Capture can still run.');return env.DB;}
async function labLoad(env,id,owner){
 const row=await labDB(env).prepare('SELECT state_json,capture_heartbeat,last_frame_id FROM lab_sessions WHERE id=? AND owner=?').bind(id,owner).first();
 if(!row)labError(404,'Lab session not found.');const s=JSON.parse(row.state_json);s.runtime.last_capture_heartbeat_ms=row.capture_heartbeat;s.observation.latest_frame_id=row.last_frame_id||s.observation.latest_frame_id;return s;
}
function labTiming(s){
 const step=s.steps.find(v=>v.checkpoint_id===s.queue.current_checkpoint_id);
 const elapsed=Math.max(0,Date.now()-(s.runtime.last_accounted_ms||Date.now()));
 if(step){step.timing.wall_ms+=elapsed;
  if(s.status==='paused')step.timing.paused_ms+=elapsed;
  else if(!s.runtime.capture_active)step.timing.disconnected_ms+=elapsed;
  else {step.timing.tracking_active_ms+=elapsed;
   const observed=Date.parse(s.observation.source_received_at||'');
   if(Number.isFinite(observed))step.timing.valid_observation_ms+=Math.max(0,Math.min(Date.now(),observed+20000)-Math.max(s.runtime.last_accounted_ms||Date.now(),observed));
  }
 }
 s.runtime.last_accounted_ms=Date.now();
}
function labProjection(s){
 const value=clone(s);labTiming(value);value.runtime.retry_after_ms=Math.max(0,(value.runtime.retry_at_ms||0)-Date.now());
 if(value.runtime.capture_active && Date.now()-(value.runtime.last_capture_heartbeat_ms||0)>20000)value.runtime.capture_active=false;
 if(value.observation.source_received_at){value.observation.age_ms=Math.max(0,Date.now()-Date.parse(value.observation.source_received_at));
  if(value.observation.age_ms>20000)value.observation.status='stale';}
 const cp=checkpoint(value);const current=value.steps.find(v=>v.checkpoint_id===cp?.id);
 value.guidance={state:value.status==='completed'?'ended':value.status==='paused'?'paused':!value.runtime.capture_active?'disconnected':
  value.observation.status!=='available'?'waiting_for_observation':'current_step',
  now_checkpoint_id:cp?.id||null,next_checkpoint_id:value.queue.upcoming_checkpoint_ids[0]||null,
  instruction:value.progression_mode==='screen_guided'?guidedInstruction(value):cp?.instruction.en||'Experiment complete. Export your journal.',reason:cp?.why.en||null,
  based_on_observation_id:value.observation.observation_id,based_on_visit_id:current?.current_visit_id||null,
  ...(value.progression_mode==='screen_guided'?guidedProcedure(value):{}),valid_until:new Date(Date.now()+8000).toISOString(),pointer_active:false,next_instruction:value.progression_mode==='screen_guided'?guidedNext(value):null};
 return value;
}
async function labSave(env,s,expected,eventType,payload={},eventId=crypto.randomUUID(),image=null){
 const db=labDB(env);labTiming(s);s.revision=expected+1;
 s.history.last_event_sequence=s.revision;s.history.event_count=s.revision;
 const event={schema:'lab-event/v1',event_id:eventId,event_sequence:s.revision,lab_session_id:s.lab_session_id,
  event_type:eventType,received_at:nowISO(),actor_type:eventType.startsWith('analysis_')?'system':'student',checkpoint_id:payload.origin_checkpoint_id||s.queue.current_checkpoint_id,
  visit_id:payload.origin_visit_id||s.steps.find(v=>v.checkpoint_id===s.queue.current_checkpoint_id)?.current_visit_id||null,
  workspace_id:s.workspace.id,capture_epoch:s.workspace.capture_epoch,parameter_revision:s.workspace.parameter_revision,
  condition:s.workspace.condition,payload};
 const statements=[db.prepare('UPDATE lab_sessions SET revision=?,mutation_id=?,state_json=?,updated_at=? WHERE id=? AND owner=? AND revision=?')
  .bind(s.revision,eventId,JSON.stringify(s),Date.now(),s.lab_session_id,s.owner_id,expected),
  db.prepare('INSERT INTO lab_events(session_id,event_id,sequence,event_json) SELECT id,?,?,? FROM lab_sessions WHERE id=? AND owner=? AND mutation_id=?')
   .bind(eventId,s.revision,JSON.stringify(event),s.lab_session_id,s.owner_id,eventId)];
 if(image)statements.push(db.prepare('INSERT OR REPLACE INTO lab_images(session_id,owner,frame_id,observation_id,received_at,jpeg) SELECT id,?,?,?,?,? FROM lab_sessions WHERE id=? AND owner=? AND mutation_id=?')
  .bind(s.owner_id,image.frame.frame_id,image.observation_id,image.frame.server_received_unix_ms,image.bytes.buffer,s.lab_session_id,s.owner_id,eventId));
 if(eventType==='capture_detached'||eventType==='session_paused'||payload.advanced||payload.action==='revisit'||s.status==='completed')statements.push(db.prepare('DELETE FROM lab_images WHERE session_id=? AND EXISTS (SELECT 1 FROM lab_sessions WHERE id=? AND mutation_id=?)').bind(s.lab_session_id,s.lab_session_id,eventId));
 const result=await db.batch(statements);
 if(!result[0].meta.changes)labError(409,'Lab changed while this request was running. Refresh its state.');
 return labProjection(s);
}
async function labCreate(env,owner,body){
 if(body.operator_trial!==true||typeof body.model_name!=='string'||!body.model_name.trim()||body.model_name.length>160)labError(422,'Enter your saved model name and select the builder trial.');
 const s=clone(LAB_TEMPLATE),id=crypto.randomUUID();
 s.schema='lab-demo/v1';s.synthetic=false;s.owner_id=owner;s.lab_session_id=id;s.revision=1;s.status='active';s.evidence=[];
 if(body.progression_mode&&!['reviewed','screen_guided'].includes(body.progression_mode))labError(422,'Invalid progression mode.');
 s.progression_mode=body.progression_mode||'reviewed';s.auto_tracking={};
 s.readiness.override_reason='User selected builder integration trial; prerequisite readiness remains unassessed.';
 s.queue={current_checkpoint_id:'CP-DSB-01',upcoming_checkpoint_ids:LAB_DEFINITION.checkpoints.slice(1).map(c=>c.id),done_checkpoint_ids:[],support_items:[]};
 s.workspace={id:crypto.randomUUID(),software:'simulink_online',confirmed:false,external_project_ref:'model-name:'+body.model_name.trim(),capture_session_id:null,capture_epoch:0,view_revision:1,geometry_detection:'dimensions_and_manual_reports_only',parameter_revision:0,condition:'baseline'};
 s.observation={observation_id:null,source_frame_id:null,latest_frame_id:null,capture_epoch:0,view_revision:1,source_received_at:null,age_ms:null,status:'awaiting_frame'};
 for(const step of s.steps){step.status=step.checkpoint_id==='CP-DSB-01'?'in_progress':'upcoming';
  step.current_visit_id=step.status==='in_progress'?crypto.randomUUID():null;step.visits=step.current_visit_id?[step.current_visit_id]:[];step.attempt_count=step.visits.length;
  step.timing={entered_at:step.current_visit_id?nowISO():null,wall_ms:0,tracking_active_ms:0,paused_ms:0,disconnected_ms:0,valid_observation_ms:0};
  for(const c of step.criteria){c.state='unknown';c.evidence_ids=[];c.review_basis=null;c.parameter_revision=null;}}
 s.history={last_event_sequence:1,event_count:1,event_log_ref:`/lab-sessions/${id}/events`,coverage:'sampled_frames',capture_gap_count:0,truncated:false};
 s.runtime={capture_active:false,last_accounted_ms:Date.now(),analysis_attempts:0,last_analysis_started_ms:0,analysis_status:'not_checked',candidate:null,answers:[],notes:[]};
 const eventId=crypto.randomUUID();
 await labDB(env).batch([
  labDB(env).prepare('INSERT INTO lab_sessions(id,owner,revision,mutation_id,state_json,updated_at) VALUES(?,?,?,?,?,?)').bind(id,owner,1,eventId,JSON.stringify(s),Date.now()),
  labDB(env).prepare('INSERT INTO lab_events(session_id,event_id,sequence,event_json) VALUES(?,?,?,?)').bind(id,eventId,1,JSON.stringify({schema:'lab-event/v1',event_id:eventId,event_sequence:1,lab_session_id:id,event_type:'session_started',received_at:nowISO(),payload:{mode:'operator_trial',model_name:body.model_name}}))]);
 return labProjection(s);
}
async function labJSON(request){
 const text=await request.text();if(text.length>12000)labError(413,'Lab request is too large.');
 try {const body=JSON.parse(text);if(!body||typeof body!=='object'||Array.isArray(body))throw Error();return body;}catch{labError(422,'Expected a JSON object.');}
}
function labExpected(s,body){if(!Number.isInteger(body.revision)||body.revision!==s.revision)labError(409,'Lab revision changed. Refresh before editing.');}
async function labEvents(env,id,owner,after=0,limit=100){await labLoad(env,id,owner);const result=await labDB(env).prepare('SELECT event_json FROM lab_events WHERE session_id=? AND sequence>? ORDER BY sequence LIMIT ?').bind(id,after,limit).all();return result.results.map(r=>JSON.parse(r.event_json));}
async function labMutation(env,s,body){
 labExpected(s,body);const expected=s.revision;const step=s.steps.find(v=>v.checkpoint_id===s.queue.current_checkpoint_id);const cp=checkpoint(s);
 const action=body.action;const origin={origin_checkpoint_id:cp?.id||null,origin_visit_id:step?.current_visit_id||null};
 let advanced=false,responseRecord=null;
 if(action==='note'||action==='answer'||action==='help'){
  if(typeof body.text!=='string'||!body.text.trim()||body.text.length>2000)labError(422,'Enter a bounded text response.');
  const record={id:crypto.randomUUID(),checkpoint_id:cp?.id||null,visit_id:step?.current_visit_id||null,text:body.text.trim(),at:nowISO()};
  responseRecord=record;
  if(action==='answer'){s.runtime.answers.push(record);if(step)step.telemetry.answer_count++;}
  else {s.runtime.notes.push(record);if(action==='help'&&step)step.telemetry.help_request_count++;}
  if(action==='answer'&&s.progression_mode==='screen_guided'){
   for(const c of step?.criteria||[])if(GUIDED_POLICY.responses[c.criterion_id])Object.assign(c,{state:'satisfied',completion_basis:'student_report_unassessed',review_basis:'student_report_unassessed',evidence_ids:[record.id],parameter_revision:s.workspace.parameter_revision});
   advanced=guidedFinish(s);
  }
 }else if(action==='enable_guided'){
  s.progression_mode='screen_guided';guidedClear(s);s.runtime.candidate=null;s.workspace.condition=GUIDED_POLICY.conditions[cp.id];s.workspace.condition_basis='checkpoint_intent_not_verified_model_state';
 }else if(action==='pause'||action==='resume'){
  labTiming(s);if(s.status==='completed')labError(409,'Lab is completed.');s.status=action==='pause'?'paused':'active';if(action==='pause')s.runtime.candidate=null;
 }else if(action==='view_changed'){
  if(!Number.isInteger(body.view_revision)||body.view_revision<=s.workspace.view_revision||body.view_revision>Number.MAX_SAFE_INTEGER)labError(422,'View revision must increase.');
  s.workspace.view_revision=body.view_revision;s.runtime.candidate=null;s.observation.status='awaiting_frame';
 }else if(action==='parameters_changed'){
  s.workspace.parameter_revision++;s.runtime.candidate=null;
  for(const c of step?.criteria||[]){c.state='unknown';c.evidence_ids=[];c.review_basis=null;c.parameter_revision=null;}
 }else if(action==='condition'){
  if(!['baseline','phase_fault','restored_baseline'].includes(body.condition))labError(422,'Invalid experiment condition.');
  const allowed=cp?.id==='CP-DSB-11'?['phase_fault']:cp?.id==='CP-DSB-12'?['restored_baseline']:['baseline'];
  if(!allowed.includes(body.condition))labError(409,'This condition belongs to another checkpoint.');
  if(s.workspace.condition!==body.condition){s.workspace.condition=body.condition;s.workspace.parameter_revision++;s.runtime.candidate=null;}
 }else if(action==='review'){
  if(s.status!=='active'||!s.runtime.capture_active)labError(409,'Resume lab and screen sharing before review.');
  const candidate=s.runtime.candidate;
  if(!candidate||candidate.visit_id!==step.current_visit_id||candidate.capture_epoch!==s.workspace.capture_epoch||candidate.parameter_revision!==s.workspace.parameter_revision)labError(409,'Check this step again before review.');
  if(Date.now()-candidate.source_frame.server_received_unix_ms>20000)labError(409,'The checked image is old. Check this step again.');
  if(!Array.isArray(body.criterion_ids)||!body.criterion_ids.length||body.criterion_ids.some(id=>!step.criteria.some(c=>c.criterion_id===id)))labError(422,'Select valid criteria.');
  if(typeof body.review_note!=='string'||body.review_note.trim().length<8||body.review_note.length>1000)labError(422,'Describe the evidence you personally reviewed.');
  const ids=[...new Set(body.criterion_ids)];
  if(ids.some(id=>id.endsWith(':explanation')||id.endsWith(':observation_record')||id.endsWith(':phase_fault_observation'))&&!s.runtime.answers.some(a=>a.visit_id===step.current_visit_id))labError(422,'Record your prediction/observation/explanation before reviewing this criterion.');
  const evidenceId=crypto.randomUUID();
  s.evidence.push({id:evidenceId,kind:cp.source_evidence_kind,origin:'reviewer',captured_at:nowISO(),capture_epoch:s.workspace.capture_epoch,
   workspace_id:s.workspace.id,parameter_revision:s.workspace.parameter_revision,checkpoint_id:cp.id,visit_id:step.current_visit_id,
   observation_id:candidate.observation_id,frame_ids:[candidate.source_frame.frame_id],review_status:'accepted',reviewed_by:s.owner_id,synthetic:false,summary:body.review_note.trim()});
  for(const c of step.criteria)if(ids.includes(c.criterion_id)){c.state='satisfied';c.evidence_ids.push(evidenceId);c.review_basis='reviewed_visual';c.parameter_revision=s.workspace.parameter_revision;if(s.progression_mode==='screen_guided')c.completion_basis='student_confirmation_unassessed';}
  if(s.progression_mode==='screen_guided')advanced=guidedFinish(s);
  else if(step.criteria.every(c=>c.state==='satisfied')){
   labTiming(s);step.status='done';s.queue.done_checkpoint_ids.push(cp.id);s.queue.current_checkpoint_id=s.queue.upcoming_checkpoint_ids.shift()||null;s.runtime.candidate=null;
   if(cp.id==='CP-DSB-01')s.workspace.confirmed=true;
   const next=s.steps.find(v=>v.checkpoint_id===s.queue.current_checkpoint_id);
   if(next){next.status='in_progress';next.current_visit_id=crypto.randomUUID();next.visits.push(next.current_visit_id);next.attempt_count++;next.timing.entered_at=nowISO();}
   else s.status='completed';
  }
 }else if(action==='revisit'){
  if(!step)labError(409,'Start another lab run to revisit a completed experiment.');
  const wanted=LAB_DEFINITION.checkpoints.findIndex(v=>v.id===body.checkpoint_id);const current=LAB_DEFINITION.checkpoints.findIndex(v=>v.id===cp.id);
  if(wanted<0||wanted>current)labError(409,'Revisit the current step or an earlier checkpoint.');
  labTiming(s);
  for(let i=wanted;i<s.steps.length;i++){const v=s.steps[i];v.status=i===wanted?'in_progress':'upcoming';v.current_visit_id=i===wanted?crypto.randomUUID():null;
   if(i===wanted){v.visits.push(v.current_visit_id);v.attempt_count++;v.timing.entered_at=nowISO();}
   for(const c of v.criteria){c.state='unknown';c.evidence_ids=[];c.review_basis=null;c.parameter_revision=null;}}
  s.queue.current_checkpoint_id=LAB_DEFINITION.checkpoints[wanted].id;s.queue.done_checkpoint_ids=LAB_DEFINITION.checkpoints.slice(0,wanted).map(v=>v.id);
  s.queue.upcoming_checkpoint_ids=LAB_DEFINITION.checkpoints.slice(wanted+1).map(v=>v.id);s.runtime.candidate=null;s.workspace.condition='baseline';s.workspace.parameter_revision++;s.observation={...s.observation,observation_id:null,source_frame_id:null,source_received_at:null,status:'awaiting_frame'};
 }else labError(422,'Unknown lab action.');
 if(['pause','resume','parameters_changed','condition','revisit'].includes(action))guidedClear(s,['pause','resume'].includes(action));
 s.runtime.answers=s.runtime.answers.slice(-100);s.runtime.notes=s.runtime.notes.slice(-100);s.runtime.response_projection='latest_100_per_kind_full_history_in_events';
 return labSave(env,s,expected,action==='pause'?'session_paused':`lab_${action}`,{...body,...origin,advanced,...(responseRecord?{response:responseRecord}:{})});
}
async function labDiscardCheck(env,current,working,reason){
 if(current.runtime.analysis_status==='checking'&&current.runtime.last_analysis_started_ms===working.runtime.last_analysis_started_ms){
  current.runtime.analysis_status='discarded';
  await labSave(env,current,current.revision,'analysis_discarded',{reason,admitted_checkpoint_id:working.queue.current_checkpoint_id});
 }
}
async function labAnalyze(env,s,request,owner,metadata,capture,emit=null){
 if(s.status!=='active'||!s.runtime.capture_active||s.workspace.capture_session_id!==capture.id)labError(409,'Attach an active screen share to this lab.');
 if(!providerConfigured(env))labError(503,'Gemini is not configured.');
 if(s.runtime.retry_at_ms>Date.now())return labProjection(s);
 if(s.runtime.analysis_status==='checking'&&Date.now()-s.runtime.last_analysis_started_ms<25000)throw {status:429,detail:'The current frame check is still running.',code:'lab_check_in_flight',retry_after_ms:1000};
 const interval=GUIDED_POLICY.fast_interval_ms||3000,remaining=interval-(Date.now()-s.runtime.last_analysis_started_ms);
 if(remaining>0)throw {status:429,detail:'Wait for the next verification frame.',code:'lab_check_interval',retry_after_ms:remaining,headers:{'Retry-After':String(Math.ceil(remaining/1000))}};
 const bytes=await boundedImage(request);const digest=hex(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)));
 if(!capture.latest||capture.latest.sha256!==digest||Object.keys(metadata).some(k=>k!=='type'&&metadata[k]!==capture.latest[k]))labError(409,'A newer frame arrived. Check the next received image.');
 if(Date.now()-capture.latest.server_received_unix_ms>6000)labError(409,'The received frame is old. Wait for a new capture frame.');
 if(metadata.view_revision!==s.workspace.view_revision)labError(409,'View changed. Wait for its context update before checking.');
 const expected=s.revision;s.runtime.analysis_attempts++;s.runtime.last_analysis_started_ms=Date.now();s.runtime.analysis_status='checking';
 const working=await labSave(env,s,expected,'analysis_started',{frame_id:capture.latest.frame_id});
 const cp=checkpoint(working),step=working.steps.find(v=>v.checkpoint_id===cp.id);let output;
 try{if(emit)await emit({type:'admitted',context:streamContext(working),frame:capture.latest,admitted_at:new Date(working.runtime.last_analysis_started_ms).toISOString()});output=emit?await analyzeLabFrameStream(bytes,cp,working,env,emit):await analyzeLabFrame(bytes,cp,working,env);}
 catch(error){const current=await labLoad(env,s.lab_session_id,owner);
  if(current.revision!==working.revision){await labDiscardCheck(env,current,working,'stale_context');labError(409,'Lab changed during analysis; result ignored.');}
  if(emit?.signal.aborted){current.runtime.analysis_status='cancelled';delete current.runtime.retry_at_ms;return labSave(env,current,current.revision,'analysis_cancelled');}
  current.runtime.retry_at_ms=error.retry_at_ms||Date.now()+10000;current.runtime.analysis_status='waiting_for_provider';current.runtime.analysis_error=/^(provider_[a-z0-9_]+|invalid_provider_configuration|invalid_model_configuration|invalid_output|incomplete_output)$/.test(error.message)?error.message:'provider_timeout_or_network_error';
  current.runtime.last_analysis_timing={...error.provider_metrics,...emit?.metrics,frame_id:capture.latest.frame_id,total_ms:Date.now()-working.runtime.last_analysis_started_ms,received_to_result_ms:Date.now()-capture.latest.server_received_unix_ms,status:'failed'};
  current.steps.find(v=>v.checkpoint_id===cp.id).telemetry.analysis_failure_count++;
  return labSave(env,current,current.revision,'analysis_failed',{error:current.runtime.analysis_error});}
 const current=await labLoad(env,s.lab_session_id,owner);
 if(current.revision!==working.revision){await labDiscardCheck(env,current,working,'stale_context');labError(409,'Lab changed during analysis; result ignored.');}
 if(emit?.signal.aborted||!current.runtime.capture_active||current.status!=='active'||Date.now()-capture.latest.server_received_unix_ms>20000){await labDiscardCheck(env,current,working,'capture_changed_or_expired');labError(409,'Capture changed or frame expired during analysis.');}
 current.runtime.last_analysis_timing={...output.timing,frame_id:capture.latest.frame_id,status:'available',total_ms:Date.now()-working.runtime.last_analysis_started_ms,received_to_result_ms:Date.now()-capture.latest.server_received_unix_ms};
 const observationId=crypto.randomUUID();current.runtime.analysis_status='available';delete current.runtime.analysis_error;delete current.runtime.retry_at_ms;
 current.runtime.candidate={...output.result,observation_id:observationId,source_frame:capture.latest,visit_id:step.current_visit_id,
  capture_epoch:current.workspace.capture_epoch,view_revision:metadata.view_revision,admitted_context:{lab_session_id:working.lab_session_id,experiment_id:working.experiment_id,checkpoint_id:cp.id,visit_id:step.current_visit_id,lab_revision:working.revision,workspace_id:current.workspace.id,capture_epoch:current.workspace.capture_epoch,view_revision:metadata.view_revision,parameter_revision:current.workspace.parameter_revision,condition:current.workspace.condition},admitted_at:new Date(working.runtime.last_analysis_started_ms).toISOString(),completed_at:nowISO(),frame_handle:{handle_id:observationId,expires_at:new Date(Math.min(Date.now()+8000,capture.latest.server_received_unix_ms+20000)).toISOString(),media_type:'image/jpeg',access_policy:'same_owner_ephemeral'},parameter_revision:current.workspace.parameter_revision,model:output.model,prompt_version:emit?'dsb-step-observer/v4-short-decision1':GUIDED_POLICY.observer_prompt_version};
 current.observation={observation_id:observationId,source_frame_id:capture.latest.frame_id,latest_frame_id:capture.latest.frame_id,
  capture_epoch:current.workspace.capture_epoch,view_revision:metadata.view_revision,source_received_at:capture.latest.server_received_at,age_ms:0,status:'available'};
 const candidate=current.runtime.candidate,advanced=guidedObserve(current,candidate);
 return labSave(env,current,current.revision,'analysis_completed',{candidate,advanced,origin_checkpoint_id:cp.id,origin_visit_id:step.current_visit_id},crypto.randomUUID(),advanced?null:{bytes,frame:capture.latest,observation_id:observationId});
}
async function labRoute(request,env,owner){
 const url=new URL(request.url);
 if(!url.pathname.startsWith('/lab-'))return null;
 if(url.pathname==='/lab-definition'&&request.method==='GET')return json(LAB_DEFINITION);
 if(url.pathname==='/lab-guidance-policy'&&request.method==='GET')return json(GUIDED_POLICY);
 if(url.pathname==='/lab-sessions'&&request.method==='GET'){
  const r=await labDB(env).prepare('SELECT state_json FROM lab_sessions WHERE owner=? ORDER BY updated_at DESC LIMIT 8').bind(owner).all();
  return json(r.results.map(v=>{const s=JSON.parse(v.state_json);return {id:s.lab_session_id,status:s.status,model:s.workspace.external_project_ref,current_checkpoint_id:s.queue.current_checkpoint_id};}));}
 if(url.pathname==='/lab-sessions'&&request.method==='POST')return json(await labCreate(env,owner,await labJSON(request)),201);
 const match=/^\/lab-sessions\/([a-f0-9-]{36})(?:\/(events|check|action|attach|detach|image|heartbeat|frame-handles\/[a-f0-9-]{36}))?$/.exec(url.pathname);if(!match)labError(404,'Lab route not found.');
 const [,id,action]=match;const s=await labLoad(env,id,owner);
 if(request.method==='GET'){
  if(action?.startsWith('frame-handles/')){
   const candidate=s.runtime.candidate,handle=action.slice('frame-handles/'.length);
   if(!candidate||candidate.frame_handle.handle_id!==handle||Date.now()>=Date.parse(candidate.frame_handle.expires_at)||candidate.view_revision!==s.workspace.view_revision||!s.runtime.capture_active||s.status!=='active')labError(410,'Frame handle expired, replaced or invalidated. Request a new check.');
   const row=await labDB(env).prepare('SELECT jpeg,frame_id,observation_id FROM lab_images WHERE session_id=? AND owner=?').bind(id,owner).first();
   if(!row||row.frame_id!==candidate.source_frame.frame_id||row.observation_id!==candidate.observation_id)labError(410,'Frame handle no longer resolves to that observation.');
   return response(new Uint8Array(row.jpeg),200,{'Content-Type':'image/jpeg','X-Frame-Provenance':base64(enc.encode(JSON.stringify({source_frame:candidate.source_frame,admitted_context:candidate.admitted_context,admitted_at:candidate.admitted_at,frame_handle:candidate.frame_handle})))});
  }
  if(action==='events'){const after=Number(url.searchParams.get('after')||0),limit=Number(url.searchParams.get('limit')||100);if(!Number.isSafeInteger(after)||after<0||!Number.isInteger(limit)||limit<1||limit>100)labError(422,'Invalid journal page.');return json(await labEvents(env,id,owner,after,limit));}
  if(action==='image'){
   const row=await labDB(env).prepare('SELECT jpeg FROM lab_images WHERE session_id=? AND owner=?').bind(id,owner).first();
   if(!row)labError(404,'No checked image is retained.');return response(new Uint8Array(row.jpeg),200,{'Content-Type':'image/jpeg'});}
  if(!action)return json(labProjection(s));}
 if(request.method==='DELETE'&&!action){await labDB(env).batch([labDB(env).prepare('DELETE FROM lab_images WHERE session_id=? AND owner=?').bind(id,owner),labDB(env).prepare('DELETE FROM lab_events WHERE session_id=?').bind(id),labDB(env).prepare('DELETE FROM lab_sessions WHERE id=? AND owner=?').bind(id,owner)]);return json({deleted:true});}
 if(request.method==='POST'&&action==='heartbeat'){
  const capture=await readState(request,env,s.workspace.capture_session_id,owner);
  if(capture.status!=='sharing'||!capture.latest||Date.now()-capture.latest.server_received_unix_ms>6000)labError(409,'A fresh capture receipt is needed.');
  await labDB(env).prepare('UPDATE lab_sessions SET capture_heartbeat=?,last_frame_id=? WHERE id=? AND owner=?').bind(Date.now(),capture.latest.frame_id,id,owner).run();return json({ok:true});
 }
 if(request.method==='POST'&&action==='check'){
  const capture=await readState(request,env,s.workspace.capture_session_id,owner);if(capture.status!=='sharing')labError(409,'Capture is paused or ended.');
  return json(await labAnalyze(env,s,request,owner,metadata(request.headers.get('x-capture-frame')),capture));}
 if(request.method==='POST'){
  const body=await labJSON(request);labExpected(s,body);
  if(action==='action')return json(await labMutation(env,s,body));
  if(action==='attach'){
   const capture=await readState(request,env,body.capture_session_id,owner);if(capture.status!=='sharing')labError(409,'Start screen sharing first.');
   labTiming(s);guidedClear(s,true);s.workspace.capture_session_id=capture.id;s.workspace.capture_epoch++;s.runtime.capture_active=true;s.runtime.last_capture_heartbeat_ms=Date.now();s.runtime.candidate=null;
   s.observation.status='awaiting_frame';s.history.capture_gap_count++;const value=await labSave(env,s,s.revision,'capture_attached',{capture_session_id:capture.id});await labDB(env).prepare('UPDATE lab_sessions SET capture_heartbeat=? WHERE id=? AND owner=?').bind(Date.now(),id,owner).run();return json(value);}
  if(action==='detach'){labTiming(s);guidedClear(s,true);s.runtime.capture_active=false;s.runtime.candidate=null;s.observation.status='disconnected';return json(await labSave(env,s,s.revision,'capture_detached'));}}
 labError(405,'Lab method not allowed.');
}
async function labMCP(request,env,owner){
 const rpc=await labJSON(request);const ok=result=>json({jsonrpc:'2.0',id:rpc.id,result});
 if(rpc.method==='initialize')return ok({protocolVersion:'2024-11-05',capabilities:{tools:{}},serverInfo:{name:'kiki-dsb-lab',version:'0.1.0'}});
 if(rpc.method==='notifications/initialized')return new Response(null,{status:202});
 if(rpc.method==='tools/list')return ok({tools:[{name:'reset_lab_session',description:'Return an owned active or paused lab to step 1. Preserves its journal and earlier evidence; does not alter the Simulink model. Use only when the user requests a reset. Read the current revision first.',annotations:{readOnlyHint:false,destructiveHint:false,idempotentHint:false},inputSchema:{type:'object',properties:{lab_session_id:{type:'string'},revision:{type:'integer',minimum:1}},required:['lab_session_id','revision'],additionalProperties:false}},{name:'list_lab_sessions',description:'List this authenticated user\'s DSB-SC prototype sessions.',inputSchema:{type:'object',properties:{},additionalProperties:false}},
  {name:'read_lab_session',description:'Read owned current/next checkpoints, reviewed progress and checked screen observation.',inputSchema:{type:'object',properties:{lab_session_id:{type:'string'}},required:['lab_session_id'],additionalProperties:false}},
  {name:'read_checked_frame',description:'Read the retained latest checked image for this user\'s lab; may be older than the current screen.',inputSchema:{type:'object',properties:{lab_session_id:{type:'string'}},required:['lab_session_id'],additionalProperties:false}}]});
 if(rpc.method==='tools/call'){
  if(!owner)labError(401,'Sign in before reading private lab data.');
  const {name,arguments:args={}}=rpc.params||{};
  if(name==='list_lab_sessions'){
   const r=await labDB(env).prepare('SELECT state_json FROM lab_sessions WHERE owner=? ORDER BY updated_at DESC LIMIT 8').bind(owner).all();
   return ok({content:[{type:'text',text:JSON.stringify(r.results.map(v=>{const s=JSON.parse(v.state_json);return {lab_session_id:s.lab_session_id,status:s.status,current_checkpoint_id:s.queue.current_checkpoint_id};}))}]});}
  const s=await labLoad(env,args.lab_session_id,owner);
  if(name==='reset_lab_session'){if(Object.keys(args).some(k=>!['lab_session_id','revision'].includes(k)))labError(422,'Invalid reset fields.');const value=await labMutation(env,s,{revision:args.revision,action:'revisit',checkpoint_id:'CP-DSB-01'});return ok({content:[{type:'text',text:JSON.stringify(value)}]});}
  if(name==='read_lab_session')return ok({content:[{type:'text',text:JSON.stringify(labProjection(s))}]});
  if(name==='read_checked_frame'){
   const row=await labDB(env).prepare('SELECT frame_id,observation_id,received_at,jpeg FROM lab_images WHERE session_id=? AND owner=?').bind(s.lab_session_id,owner).first();
   if(!row)return ok({isError:true,content:[{type:'text',text:'No checked frame retained. Ask the user to check the current step.'}]});
   return ok({content:[{type:'text',text:JSON.stringify({frame_id:row.frame_id,observation_id:row.observation_id,age_ms:Date.now()-row.received_at,is_latest_checked_image:true,continuous_live_video:false})},
    {type:'image',mimeType:'image/jpeg',data:imageBase64(new Uint8Array(row.jpeg))}]});}
  return ok({isError:true,content:[{type:'text',text:'Unknown tool.'}]});}
 return json({jsonrpc:'2.0',id:rpc.id,error:{code:-32601,message:'Method not found'}},400);
}
