// L0: floating-guidance/v0.1 projection over real replayed tracker states.
// Mocked vision only; zero provider calls. Run after `node scripts/build.mjs`.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {replayLab} from './replay-lab.mjs';
import {projectSnapshot,acceptedFrom,screenContext,contentKey,currentScope,FG_LIMITS,OBSERVATION_FRESH_MS} from '../assets/floating-guidance.js';

const policy=JSON.parse(await readFile(new URL('../data/guided-policy.json',import.meta.url),'utf8'));
const definition=JSON.parse(await readFile(new URL('../data/experiment.json',import.meta.url),'utf8'));
const replayed=[];await replayLab({onState:value=>replayed.push(value)});

test('the committed projection carries capture_active for the window path',()=>{
 assert.ok(replayed.length>=24);
 // The replay sends no heartbeats, so later states correctly report false.
 for(const {committed,state} of replayed){assert.equal(typeof committed.runtime.capture_active,'boolean');assert.equal(committed.runtime.capture_active,state.runtime.capture_active);}
 assert.ok(replayed.some(v=>v.committed.runtime.capture_active===true));
});

test('Now and Next copy the tracker output exactly for every replayed state',()=>{
 let crossStage=0,within=0;
 for(const {state} of replayed){
  const body=projectSnapshot(state,{policy,definition}),guide=state.guidance;
  if(state.status==='completed'){assert.equal(body.instructions.next,null);continue;}
  assert.equal(body.instructions.now.title,guide.current_action?.title??guide.instruction);
  assert.equal(body.instructions.now.checkpoint_id,state.queue.current_checkpoint_id);
  if(guide.current_action){
   assert.equal(body.instructions.now.action_id,guide.current_action.id);
   assert.deepEqual(body.instructions.now.settings,guide.current_action.settings.map(({field,value})=>({field,value})));
   assert.deepEqual(body.instructions.now.how,guide.current_action.how);
  }
  if(guide.next_action){within++;assert.equal(body.instructions.next.title,guide.next_action.title);assert.equal(body.instructions.next.crosses_stage,false);}
  else if(guide.next_instruction){
   crossStage++;const upcoming=state.queue.upcoming_checkpoint_ids[0];
   assert.equal(body.instructions.next.title,guide.next_instruction);
   assert.equal(body.instructions.next.checkpoint_id,upcoming);
   assert.equal(body.instructions.next.action_id,policy.procedures[upcoming][0].id);
   assert.equal(body.instructions.next.crosses_stage,true);
  }
  assert.equal(body.instructions.basis,'authoritative_tracker');
  assert.equal(body.progress.checkpoint_total,12);
  assert.ok(JSON.stringify(body).length<FG_LIMITS.message_chars);
 }
 assert.ok(crossStage>0&&within>0,'replay must exercise both within-stage and cross-stage Next');
});

test('CP-DSB-06 gain settings keeps the authored text and exact value',()=>{
 const procedure=policy.procedures['CP-DSB-06'],index=procedure.findIndex(a=>a.id==='CP-DSB-06/gain-settings');
 const state=replayed.find(v=>v.state.queue.current_checkpoint_id==='CP-DSB-06').state;
 const synthetic={...state,guidance:{...state.guidance,current_action:procedure[index],next_action:procedure[index+1]||null}};
 const body=projectSnapshot(synthetic,{policy,definition});
 assert.equal(body.instructions.now.title,'Set Recovery gain to 2.');
 assert.equal(body.instructions.now.where,'Double-click Recovery gain.');
 assert.deepEqual(body.instructions.now.settings,[{field:'Gain',value:'2'}]);
 assert.equal(body.instructions.now.verification_only,false);
 assert.equal(body.instructions.next.title,procedure[index+1].title);
 assert.equal(body.progress.checkpoint_position,6);
});

const active=()=>structuredClone(replayed.find(v=>v.state.runtime.candidate&&v.state.status==='active').state);

test('screen context is fresh only for the current scope within the freshness budget',()=>{
 const state=active(),accepted=acceptedFrom(state);
 assert.ok(accepted);
 assert.equal(screenContext(state,accepted,{ageMs:1000}).status,'fresh');
 assert.equal(screenContext(state,accepted,{ageMs:1000}).fresh_for_ms,OBSERVATION_FRESH_MS-1000);
 assert.equal(screenContext(state,accepted,{ageMs:OBSERVATION_FRESH_MS}).status,'earlier');
 assert.equal(screenContext(state,accepted,{ageMs:null}).status,'earlier','unknown age never claims a current view');
 const moved=structuredClone(state);moved.workspace.view_revision++;
 assert.equal(screenContext(moved,accepted,{ageMs:1000}).status,'earlier','a view change retires the current-view claim');
});

test('waiting, pause, disconnect, provider wait and capture blocks keep instructions',()=>{
 const state=active(),accepted=acceptedFrom(state);
 const cases=[
  [s=>{s.status='paused';},'paused'],
  [s=>{s.runtime.capture_active=false;},'disconnected'],
  [s=>{s.runtime.analysis_status='waiting_for_provider';s.runtime.analysis_error='provider_http_400';},'unavailable'],
 ];
 for(const [change,status] of cases){
  const s=structuredClone(state);change(s);const body=projectSnapshot(s,{policy,definition,accepted,ageMs:500});
  assert.equal(body.screen_context.status,status);
  assert.equal(body.instructions.now.title,s.guidance.current_action?.title??s.guidance.instruction);
 }
 const blocked=projectSnapshot(state,{policy,definition,accepted,ageMs:500,blockedReason:'Share the tab where Kiki is shown.'});
 assert.equal(blocked.screen_context.status,'blocked');
 const none=projectSnapshot(state,{policy,definition,accepted:null});
 assert.equal(none.screen_context.status,'waiting');assert.equal(none.screen_context.summary,null);
});

test('accepted observation is retained after the candidate clears, never across labs',()=>{
 const state=active(),accepted=acceptedFrom(state);
 const cleared=structuredClone(state);cleared.runtime.candidate=null;
 assert.equal(acceptedFrom(cleared,accepted),accepted);
 const other=structuredClone(cleared);other.lab_session_id='another-lab';
 assert.equal(acceptedFrom(other,accepted),null);
 assert.deepEqual(accepted.admitted_context.lab_session_id,currentScope(state).lab_session_id);
});

test('text is bounded and summaries describing uncertainty are labelled as such',()=>{
 const state=active(),long='x'.repeat(5000);
 state.guidance.current_action={...state.guidance.current_action,title:long,how:Array(30).fill(long)};
 const accepted={...acceptedFrom(state),summary:'Not established: the dialog covers the wire.'};
 const body=projectSnapshot(state,{policy,definition,accepted,ageMs:0});
 assert.equal(body.instructions.now.title.length,FG_LIMITS.text);
 assert.equal(body.instructions.now.how.length,FG_LIMITS.list);
 assert.equal(body.screen_context.summary_kind,'uncertainty');
});

test('content identity ignores ageing but changes with shown content',()=>{
 const state=active(),accepted=acceptedFrom(state);
 const a=projectSnapshot(state,{policy,definition,accepted,ageMs:1000}),b=projectSnapshot(state,{policy,definition,accepted,ageMs:9000});
 assert.equal(contentKey(a),contentKey(b));
 assert.notEqual(contentKey(a),contentKey(projectSnapshot(state,{policy,definition,accepted,ageMs:OBSERVATION_FRESH_MS+1})));
 const paused=structuredClone(state);paused.status='paused';
 assert.notEqual(contentKey(a),contentKey(projectSnapshot(paused,{policy,definition,accepted,ageMs:1000})));
});
