// Pure floating-guidance/v0.1 receiver rules shared by the content script, the
// harness and node tests: validation, ordering and the window view model.
// Nothing here completes a step, reads the screen or touches the page.
(() => {
 const SCHEMA='floating-guidance/v0.1';
 const LIMITS={chars:24000,text:600,list:8,settings:12};
 const SCREEN=new Set(['waiting','fresh','earlier','paused','ended','disconnected','blocked','unavailable']);
 const LAB=new Set(['active','paused','completed']);
 const TRANSPORT_AGE_BOUND_MS=1000,LEASE_MS=15000;
 const fail=reason=>({ok:false,reason});
 const str=(v,max=LIMITS.text)=>v===null||(typeof v==='string'&&v.length<=max);
 const strs=(v,max=LIMITS.list)=>Array.isArray(v)&&v.length<=max&&v.every(x=>typeof x==='string'&&x.length<=LIMITS.text);
 const num=v=>v===null||(typeof v==='number'&&Number.isFinite(v)&&v>=0);
 function action(a,full){
  if(a===null)return true;if(!a||typeof a!=='object'||typeof a.title!=='string'||!a.title||!str(a.title)||!str(a.action_id??null,160)||!str(a.checkpoint_id??null,80))return false;
  if(!full)return typeof a.crosses_stage==='boolean'||a.crosses_stage===undefined;
  return str(a.where)&&strs(a.how)&&str(a.expected_result)&&str(a.already_done_help)&&typeof a.verification_only==='boolean'&&
   Array.isArray(a.settings)&&a.settings.length<=LIMITS.settings&&a.settings.every(s=>s&&typeof s.field==='string'&&typeof s.value==='string'&&s.field.length<=120&&s.value.length<=120);
 }
 function validate(message){
  if(!message||typeof message!=='object'||Array.isArray(message))return fail('not_object');
  if(message.schema!==SCHEMA)return fail('unknown_schema');
  if(message.type!=='replace_snapshot')return fail('unknown_type');
  let size;try{size=JSON.stringify(message).length;}catch{return fail('not_serializable');}
  if(size>LIMITS.chars)return fail('too_large');
  if(typeof message.stream_id!=='string'||!/^[A-Za-z0-9-]{8,64}$/.test(message.stream_id))return fail('bad_stream');
  if(!Number.isSafeInteger(message.sequence)||message.sequence<1)return fail('bad_sequence');
  if(!Number.isSafeInteger(message.generation)||message.generation<1)return fail('bad_generation');
  const b=message.body;if(!b||typeof b!=='object')return fail('bad_body');
  if(!b.lab||!LAB.has(b.lab.status))return fail('bad_lab');
  if(!Number.isSafeInteger(b.lab_revision))return fail('bad_revision');
  const i=b.instructions;if(!i||i.basis!=='authoritative_tracker'||!action(i.now??null,true)||!action(i.next??null,false)||!str(i.why??null)||!str(i.already_tracked??null))return fail('bad_instructions');
  const s=b.screen_context;if(!s||!SCREEN.has(s.status)||!str(s.summary??null,300)||!strs(s.visible||[],3)||!strs(s.check||[],3)||!strs(s.uncertainties||[],2)||!num(s.age_ms??null)||!num(s.fresh_for_ms??0)||!str(s.reason??null,220))return fail('bad_screen_context');
  if(s.status==='fresh'&&!(s.observation_id&&s.source_frame&&Number.isFinite(s.age_ms)&&s.fresh_for_ms>0))return fail('fresh_without_provenance');
  const r=b.runtime;if(!r||typeof r.capture_active!=='boolean'||typeof r.reading!=='boolean'||!num(r.retry_after_ms??null))return fail('bad_runtime');
  const p=b.progress||{};if(![p.checkpoint_position,p.checkpoint_total,p.action_position,p.action_total].every(v=>v===null||v===undefined||Number.isSafeInteger(v)))return fail('bad_progress');
  return {ok:true};
 }
 // High-water per attachment generation. The background increments the
 // generation on each new reader stream/document; hello retries reuse it.
 function order(highWater,message){
  if(!highWater)return 'accept';
  if(message.generation<highWater.generation)return 'stale_generation';
  if(message.generation>highWater.generation)return 'accept';
  if(message.stream_id!==highWater.stream_id)return 'foreign_stream';
  if(message.sequence===highWater.sequence)return 'duplicate';
  return message.sequence<highWater.sequence?'out_of_order':'accept';
 }
 const seconds=ms=>{const s=Math.max(0,Math.round(ms/1000));return s<60?`${s} s`:`${Math.round(s/60)} min`;};
 // now/receivedAt/lastMessageAt are monotonic (performance.now) on this device.
 function viewModel(message,{receivedAt=0,now=0,lastMessageAt=receivedAt,connection='live',pending=null}={}){
  if(!message)return {empty:true,connection,status:{text:connection==='reconnecting'?'Reconnecting to the Kiki tracker…':'Open the Kiki tracker and share this tab.',live:false}};
  const b=message.body,live=connection==='live'&&now-lastMessageAt<=LEASE_MS,lab=b.lab.status,sc=b.screen_context,since=Math.max(0,now-receivedAt);
  let screen=sc.status;
  if(screen==='fresh'&&since+TRANSPORT_AGE_BOUND_MS>=sc.fresh_for_ms)screen='earlier';
  if(!live&&screen==='fresh')screen='earlier';
  const age=Number.isFinite(sc.age_ms)?sc.age_ms+since:null;
  const headings={fresh:'What I can see',earlier:'Earlier view',waiting:'Waiting for a screen read',unavailable:'Screen reading is waiting',paused:'Guidance paused',ended:'Experiment complete',disconnected:'Screen sharing is off',blocked:'Screen read paused'};
  const guideLabel=!live?'Saved step · not live':lab==='completed'?'Experiment complete':lab==='paused'?'Guidance paused':!b.runtime.capture_active?'Saved step · share this tab to continue':screen==='fresh'&&sc.context_matches!==false?'Current step':'Saved step · not yet checked on screen';
  const retry=b.runtime.retry_after_ms===null?null:Math.max(0,b.runtime.retry_after_ms-since);
  const statusText=connection==='superseded'?'Another Kiki tracker tab took over':!live?'Not connected to the Kiki tracker':lab==='paused'?'Connected · paused':lab==='completed'?'Connected · experiment complete':!b.runtime.capture_active?'Connected · sharing is off':b.runtime.reading?'Connected · reading screen':b.runtime.analysis_status==='waiting_for_provider'?`Connected · screen reading retries${retry?` in ${seconds(retry)}`:' soon'}`:'Connected';
  const p=b.progress||{},stage=p.checkpoint_position&&p.checkpoint_total?`Stage ${p.checkpoint_position} of ${p.checkpoint_total}`:null,act=p.action_position&&p.action_total?`Action ${p.action_position} of ${p.action_total}`:null;
  const pausing=pending==='pause'||pending==='resume';
  return {empty:false,connection,live,
   header:[stage,act].filter(Boolean).join(' · ')||'Kiki',
   guide:{label:guideLabel,now:b.instructions.now,next:b.instructions.next,why:b.instructions.why,already:b.instructions.already_tracked},
   // Provider error codes stay in logs; the learner sees what happens next.
   screen:{status:screen,heading:headings[screen],summary:sc.summary,kind:sc.summary_kind,check:sc.check||[],uncertainties:sc.uncertainties||[],
    reason:screen==='blocked'?sc.reason||null:screen==='unavailable'?`Kiki will read your screen again${retry?` in ${seconds(retry)}`:' soon'}. Your step is saved.`:null,
    age:age===null?null:screen==='fresh'?`Checked ${seconds(age)} ago`:`From ${seconds(age)} ago`},
   status:{text:statusText,live},
   pause:{label:pending==='pause'?'Pausing…':pending==='resume'?'Resuming…':lab==='paused'?'Resume guidance':'Pause guidance',
    command:lab==='paused'?'resume':'pause',disabled:!live||lab==='completed'||pausing}};
 }
 const api={SCHEMA,LIMITS,LEASE_MS,TRANSPORT_AGE_BOUND_MS,validate,order,viewModel};
 if(typeof globalThis!=='undefined')globalThis.KikiFloatingCore=api;
})();
