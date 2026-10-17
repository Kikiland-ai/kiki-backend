// floating-guidance/v0.1 projection. Deterministic and pure: it copies the
// tracker's current/next text and the accepted observation into bounded window
// content. It never selects an action, invents screen facts or stamps frame
// provenance; those come from the authoritative reader state.
export const FG_SCHEMA='floating-guidance/v0.1';
export const FG_LIMITS={text:600,short:160,list:8,settings:12,facts:3,uncertainties:2,message_chars:24000};
export const OBSERVATION_FRESH_MS=20000;
const SCOPE=['lab_session_id','checkpoint_id','visit_id','workspace_id','capture_epoch','view_revision','parameter_revision','condition'];
const text=(value,max=FG_LIMITS.text)=>typeof value==='string'&&value.trim()?value.trim().slice(0,max):null;
const texts=(value,max=FG_LIMITS.list,size=FG_LIMITS.text)=>Array.isArray(value)?value.map(v=>text(typeof v==='string'?v:v?.text,size)).filter(Boolean).slice(0,max):[];
const step=state=>Array.isArray(state?.steps)?state.steps.find(s=>s.checkpoint_id===state.queue?.current_checkpoint_id):null;

export function currentScope(state){
 const s=step(state);
 return {lab_session_id:state.lab_session_id,checkpoint_id:state.queue?.current_checkpoint_id||null,visit_id:s?.current_visit_id||null,
  workspace_id:state.workspace?.id||null,capture_epoch:state.workspace?.capture_epoch??null,view_revision:state.workspace?.view_revision??null,
  parameter_revision:state.workspace?.parameter_revision??null,condition:state.workspace?.condition||null};
}
function actionView(action,checkpointId){
 if(!action)return null;
 return {action_id:text(action.id,FG_LIMITS.short),checkpoint_id:checkpointId,title:text(action.title),where:text(action.where),how:texts(action.how),
  settings:(Array.isArray(action.settings)?action.settings:[]).slice(0,FG_LIMITS.settings).map(v=>({field:text(v?.field,120),value:text(v?.value,120)})).filter(v=>v.field&&v.value),
  expected_result:text(action.expected_result),already_done_help:text(action.already_done_help),verification_only:action.verification_only===true};
}
function nextView(state,policy){
 const guide=state.guidance||{},cp=state.queue?.current_checkpoint_id||null;
 if(guide.next_action)return {...actionView(guide.next_action,cp),crosses_stage:false};
 const title=text(guide.next_instruction);if(!title)return null;
 // The tracker's next_instruction falls back to the next stage's first action.
 const upcoming=state.queue?.upcoming_checkpoint_ids?.[0]||null,first=upcoming?policy?.procedures?.[upcoming]?.[0]:null;
 return {action_id:first&&first.title===guide.next_instruction?text(first.id,FG_LIMITS.short):null,checkpoint_id:upcoming,title,crosses_stage:true};
}
// The caller retains the last accepted candidate (it is nulled on advance/pause)
// together with the scope it was admitted under. Age is server-measured.
export function acceptedFrom(state,previous=null){
 const c=state?.runtime?.candidate;
 if(c&&state.runtime.analysis_status==='available'&&c.observation_id&&previous?.observation_id!==c.observation_id)
  return {observation_id:c.observation_id,summary:c.summary,criteria:c.criteria||[],action_findings:c.action_findings||[],uncertainties:c.uncertainties||[],
   source_frame:{frame_id:c.source_frame?.frame_id??null,sha256:c.source_frame?.sha256??null,server_received_at:c.source_frame?.server_received_at??null,server_received_unix_ms:c.source_frame?.server_received_unix_ms??null},
   admitted_context:c.admitted_context||null,accepted_at:c.completed_at||null};
 return previous&&previous.admitted_context?.lab_session_id===state?.lab_session_id?previous:null;
}
function facts(accepted){
 const rows=[...accepted.criteria,...accepted.action_findings].filter(r=>typeof r?.evidence==='string'&&r.evidence.trim());
 const pick=status=>rows.filter(r=>r.status===status).map(r=>text(r.evidence,220));
 return {visible:[...new Set(pick('match'))].slice(0,FG_LIMITS.facts),check:[...new Set(pick('mismatch'))].slice(0,FG_LIMITS.facts)};
}
// ageMs: server-measured observation age plus the caller's monotonic aging.
export function screenContext(state,accepted,{ageMs=null,blockedReason=null}={}){
 const runtime=state.runtime||{},scope=currentScope(state);
 const base={status:'waiting',reason:null,observation_id:null,source_frame:null,observed_context:null,summary:null,summary_kind:null,visible:[],check:[],uncertainties:[],age_ms:null,fresh_for_ms:0};
 if(state.status==='paused')base.status='paused';
 else if(state.status==='completed')base.status='ended';
 else if(!runtime.capture_active)base.status='disconnected';
 else if(blockedReason)Object.assign(base,{status:'blocked',reason:text(blockedReason,220)});
 else if(runtime.analysis_status==='waiting_for_provider')Object.assign(base,{status:'unavailable',reason:text(runtime.analysis_error,80)});
 if(!accepted)return base;
 const age=Number.isFinite(ageMs)?Math.max(0,ageMs):null,matches=SCOPE.every(k=>accepted.admitted_context?.[k]===scope[k]);
 const summary=text(accepted.summary,300),kind=summary?.startsWith('Visible:')?'visible':summary?.startsWith('Check this:')?'check':'uncertainty';
 const fresh=base.status==='waiting'&&matches&&age!==null&&age<OBSERVATION_FRESH_MS;
 return {...base,status:fresh?'fresh':base.status==='waiting'?'earlier':base.status,observation_id:accepted.observation_id,
  source_frame:accepted.source_frame,observed_context:accepted.admitted_context?Object.fromEntries(SCOPE.map(k=>[k,accepted.admitted_context[k]??null])):null,
  summary,summary_kind:kind,...facts(accepted),uncertainties:texts(accepted.uncertainties,FG_LIMITS.uncertainties,220),
  context_matches:matches,age_ms:age,fresh_for_ms:fresh?OBSERVATION_FRESH_MS-age:0,accepted_at:accepted.accepted_at};
}
// Window body for one replace_snapshot. Transport fields are added by the publisher.
export function projectSnapshot(state,{policy=null,definition=null,accepted=null,ageMs=null,reading=false,retryAfterMs=null,blockedReason=null}={}){
 const guide=state.guidance||{},cp=state.queue?.current_checkpoint_id||null,order=definition?.checkpoints?.find(c=>c.id===cp)?.order??null;
 // A completed lab has no current action; the tracker's fallback copy is not an instruction.
 const now=state.status==='completed'?null:actionView(guide.current_action,cp)||(guide.instruction?{action_id:null,checkpoint_id:cp,title:text(guide.instruction),where:null,how:[],settings:[],expected_result:null,already_done_help:null,verification_only:false}:null);
 return {
  context:currentScope(state),lab_revision:state.revision,
  lab:{status:state.status,guidance_state:guide.state||null},
  instructions:{basis:'authoritative_tracker',procedure_version:text(guide.procedure_version,80),now,next:state.status==='completed'?null:nextView(state,policy),
   why:text(policy?.stage_explanations?.[cp])||null,already_tracked:text(guide.already_tracked)},
  screen_context:screenContext(state,accepted,{ageMs,blockedReason}),
  runtime:{capture_active:Boolean(state.runtime?.capture_active),analysis_status:state.runtime?.analysis_status||null,reading:Boolean(reading),
   retry_after_ms:Number.isFinite(retryAfterMs)&&retryAfterMs>0?Math.round(retryAfterMs):null},
  progress:{checkpoint_position:order,checkpoint_total:definition?.checkpoints?.length??null,action_position:guide.current_action?guide.action_position??null:null,
   action_total:Array.isArray(guide.procedure)?guide.procedure.length:null,stages_tracked:state.queue?.done_checkpoint_ids?.length??0}};
}
// Stable content identity: changes when anything shown changes, not as age ticks.
export function contentKey(body){
 const {screen_context:sc,runtime,...rest}=body;
 return JSON.stringify({...rest,runtime:{...runtime,retry_after_ms:runtime.retry_after_ms===null?null:Math.ceil(runtime.retry_after_ms/5000)},screen_context:{...sc,age_ms:null,fresh_for_ms:null}});
}
