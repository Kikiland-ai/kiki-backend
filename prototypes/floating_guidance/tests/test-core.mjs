// L0: extension receiver rules. Runs the real classic script in a VM context.
// Run from prototypes/json_stream_site after `node scripts/build.mjs`:
//   node --test ../floating_guidance/tests/test-core.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFile} from 'node:fs/promises';
import {replayLab} from '../../json_stream_site/scripts/replay-lab.mjs';
import {projectSnapshot,acceptedFrom,FG_SCHEMA} from '../../json_stream_site/assets/floating-guidance.js';

const sandbox={};vm.createContext(sandbox);
vm.runInContext(await readFile(new URL('../extension/core.js',import.meta.url),'utf8'),sandbox);
const core=sandbox.KikiFloatingCore;
const reader=new URL('../../json_stream_site/data/',import.meta.url);
const policy=JSON.parse(await readFile(new URL('guided-policy.json',reader),'utf8')),definition=JSON.parse(await readFile(new URL('experiment.json',reader),'utf8'));
const states=[];await replayLab({onState:v=>states.push(v.state)});
const wrap=(body,{sequence=1,generation=1,stream_id='stream-aaaa-1111'}={})=>({schema:FG_SCHEMA,type:'replace_snapshot',stream_id,sequence,generation,body});
const plain=v=>JSON.parse(JSON.stringify(v));

test('every projected replay snapshot passes the extension validator',()=>{
 let accepted=null;
 for(const state of states){accepted=acceptedFrom(state,accepted);
  const result=core.validate(wrap(projectSnapshot(state,{policy,definition,accepted,ageMs:1000})));
  assert.equal(result.ok,true,`${state.queue.current_checkpoint_id}: ${result.reason}`);}
});

const sample=()=>{const state=states.find(s=>s.runtime.candidate&&s.runtime.capture_active);return wrap(projectSnapshot(state,{policy,definition,accepted:acceptedFrom(state),ageMs:1000}));};

test('unknown versions, unsafe shapes and invented freshness are rejected',()=>{
 const cases=[
  [m=>{m.schema='floating-guidance/v9';},'unknown_schema'],
  [m=>{m.type='draw_shapes';},'unknown_type'],
  [m=>{m.sequence=0;},'bad_sequence'],
  [m=>{m.stream_id='x';},'bad_stream'],
  [m=>{m.body.instructions.basis='model';},'bad_instructions'],
  [m=>{m.body.instructions.now.settings=[{field:'Gain',value:2}];},'bad_instructions'],
  [m=>{m.body.screen_context.status='certain';},'bad_screen_context'],
  [m=>{m.body.screen_context.status='fresh';m.body.screen_context.source_frame=null;},'fresh_without_provenance'],
  [m=>{m.body.lab.status='mastered';},'bad_lab'],
  [m=>{m.body.instructions.why='x'.repeat(30000);},'too_large'],
 ];
 for(const [change,reason] of cases){const m=plain(sample());change(m);assert.equal(core.validate(m).reason,reason);}
 assert.equal(core.validate(null).reason,'not_object');
});

test('ordering rejects old generations, foreign streams, reorders and flags duplicates',()=>{
 const hw={generation:3,stream_id:'stream-aaaa-1111',sequence:10},m=(o)=>({generation:3,stream_id:'stream-aaaa-1111',sequence:11,...o});
 assert.equal(core.order(null,m()),'accept');
 assert.equal(core.order(hw,m()),'accept');
 assert.equal(core.order(hw,m({sequence:10})),'duplicate');
 assert.equal(core.order(hw,m({sequence:9})),'out_of_order');
 assert.equal(core.order(hw,m({generation:2,sequence:99})),'stale_generation');
 assert.equal(core.order(hw,m({stream_id:'stream-bbbb-2222'})),'foreign_stream');
 assert.equal(core.order(hw,m({generation:4,stream_id:'stream-bbbb-2222',sequence:1})),'accept');
});

test('a fresh view ages locally into an earlier view and never refreshes from delivery',()=>{
 const m=plain(sample());assert.equal(m.body.screen_context.status,'fresh');
 const budget=m.body.screen_context.fresh_for_ms;
 assert.equal(core.viewModel(m,{receivedAt:0,now:1000}).screen.status,'fresh');
 assert.equal(core.viewModel(m,{receivedAt:0,now:budget-core.TRANSPORT_AGE_BOUND_MS}).screen.status,'earlier');
 assert.equal(core.viewModel(m,{receivedAt:0,now:1000}).guide.label,'Current step');
});

test('instructions survive provider waits, pauses and a lost connection with honest labels',()=>{
 const base=plain(sample()),title=base.body.instructions.now.title;
 const wait=plain(base);wait.body.runtime.analysis_status='waiting_for_provider';wait.body.runtime.retry_after_ms=900000;wait.body.screen_context.status='unavailable';
 const vw=core.viewModel(wait,{receivedAt:0,now:1000});
 assert.equal(vw.guide.now.title,title);assert.match(vw.status.text,/retries in 15 min/);assert.equal(vw.screen.heading,'Screen reading is waiting');
 assert.equal(vw.screen.reason,'Kiki will read your screen again in 15 min. Your step is saved.');assert.doesNotMatch(JSON.stringify(vw.screen),/provider_http/);
 const paused=plain(base);paused.body.lab.status='paused';paused.body.screen_context.status='paused';
 const vp=core.viewModel(paused,{receivedAt:0,now:1000});
 assert.equal(vp.guide.label,'Guidance paused');assert.equal(vp.pause.label,'Resume guidance');assert.equal(vp.pause.command,'resume');
 const lost=core.viewModel(base,{receivedAt:0,now:core.LEASE_MS+1,lastMessageAt:0});
 assert.equal(lost.guide.now.title,title);assert.equal(lost.guide.label,'Saved step · not live');assert.equal(lost.screen.status,'earlier');assert.equal(lost.pause.disabled,true);
 assert.equal(core.viewModel(base,{receivedAt:0,now:500,connection:'disconnected'}).status.text,'Not connected to the Kiki tracker');
});

test('a pending pause disables the control until the authoritative state arrives',()=>{
 const v=core.viewModel(plain(sample()),{receivedAt:0,now:100,pending:'pause'});
 assert.equal(v.pause.label,'Pausing…');assert.equal(v.pause.disabled,true);
 assert.equal(core.viewModel(null,{connection:'reconnecting'}).status.text,'Reconnecting to the Kiki tracker…');
});
