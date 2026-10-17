// Pure consumer compatibility; actual compositor/native-capture checks are separate.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import '../assets/guidance-protocol.js';
import '../assets/writing-protocol.js';
const P=globalThis.KikiGuidanceProtocol;
const load=()=>JSON.parse(readFileSync(new URL('./fixtures/guidance-renderer.json',import.meta.url))).state;
test('drawing clock excludes slow server processing and conservatively bounds asymmetric transit',()=>{
 const s=globalThis.KikiWritingProtocol.clockSample(1000,1940,{clock_authority:'observer_server_utc',server_received_ms:501120,server_time_ms:501820});
 assert.equal(s.server_processing_ms,700);assert.equal(s.uncertainty,121);assert.ok(s.upper>=500000);assert.ok(s.upper-2*s.uncertainty<=500000);
 const asymmetric=globalThis.KikiWritingProtocol.clockSample(1000,2020,{clock_authority:'observer_server_utc',server_received_ms:501020,server_time_ms:501720});assert.equal(asymmetric.uncertainty,161);assert.ok(asymmetric.upper>=500000);
});
test('drawing clock still rejects excess network uncertainty, impossible timing and foreign authority',()=>{
 const f=globalThis.KikiWritingProtocol.clockSample;
 assert.throws(()=>f(1000,2300,{clock_authority:'observer_server_utc',server_received_ms:501300,server_time_ms:502000}),/250 ms/);
 assert.throws(()=>f(1000,1100,{clock_authority:'observer_server_utc',server_received_ms:501000,server_time_ms:501700}),/250 ms/);
 assert.throws(()=>f(1000,1100,{clock_authority:'observer_server_utc',server_received_ms:501100,server_time_ms:501000}),/Invalid/);
 assert.throws(()=>f(1000,1100,{clock_authority:'foreign',server_time_ms:501000}),/Invalid/);
 assert.equal(f(1000,1200,{clock_authority:'observer_server_utc',server_time_ms:501100}).uncertainty,101);
});
test('actual committed state is accepted and compiles only supplied marks',()=>{const state=load(),e=state.screen_guidance;P.validate(e,state);const ops=P.compile(e);assert.deepEqual(ops[0].region,e.packet.resolved_targets[0].region);assert.equal(ops[1].text,state.guidance.instruction);assert.equal(ops.length,2);});
for(const key of ['view_revision','parameter_revision','capture_epoch','condition'])test('obsolete '+key+' rejects the whole cue',()=>{const state=load(),e=structuredClone(state.screen_guidance);state.workspace[key]=key==='condition'?'phase_fault':99;assert.throws(()=>P.validate(e,state),/Stale/);});
test('foreign action, observation and fallback are rejected',()=>{for(const which of ['action','observation','instruction']){const state=load();if(which==='action')state.screen_guidance.action_id='CP-DSB-03/carrier-settings';if(which==='observation')state.screen_guidance.frame.observation_id='foreign';if(which==='instruction')state.screen_guidance.packet.fallback.instruction='Invented next action';assert.throws(()=>P.validate(state.screen_guidance,state),/Stale|Foreign/);}});
test('arrow coordinates are target-relative and out-of-frame geometry is rejected',()=>{const state=load(),e=state.screen_guidance,first=e.packet.resolved_targets[0];e.packet.resolved_targets.push({...first,target_id:'carrier.frequency',region:{x:.6,y:.2,width:.1,height:.1}});e.packet.operations=[{kind:'arrow',cue_id:'compare',meaning:'lab',accessible_label:'Compare',from:{target_id:first.target_id,u:1,v:.5},to:{target_id:'carrier.frequency',u:0,v:.5}}];const arrow=P.compile(e)[0];assert.equal(arrow.anchors[1].x,.6);first.region.x=.99;assert.throws(()=>P.compile(e),/Unresolved/);});
test('text-only has no anchored marks and stale text is rejected',()=>{const state=load(),e=state.screen_guidance;e.outcome='text_only';e.packet.operations=[];e.packet.fallback.reason='unresolved_required_target';e.packet.resolved_targets[0].status='unresolved';e.packet.resolved_targets[0].region=null;P.validate(e,state);state.revision++;assert.throws(()=>P.validate(e,state),/Stale/);});
