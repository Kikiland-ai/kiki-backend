// Replay actual model generations from a controlled screenshot, not authored marks.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {DrawingFindingParserJS} from '../worker/guidance.js';
const load=name=>JSON.parse(readFileSync(new URL(name,import.meta.url)));
const sample=load('./fixtures/generated-gain-guidance.json'),definition=load('../data/experiment.json'),policy=load('../data/guided-policy.json'),cp=definition.checkpoints.find(c=>c.id===sample.checkpoint_id);
for(const c of sample.cases)test('actual model generation '+c.variant,()=>{
 const p=new DrawingFindingParserJS(cp,policy.procedures[cp.id],{eligible_actions:sample.eligible_actions});for(const ch of JSON.stringify(c.model))p.feed(ch);
 if(c.valid){const value=p.finish(),candidate=value.screen_guidance.find(c=>c.action_id==='CP-DSB-06/gain-settings');assert.equal(candidate.mode,'annotate');assert.equal(candidate.marks[0].kind,'box');assert.equal(candidate.marks[1].kind,'text');assert.ok(candidate.marks[1].anchor);assert.ok(['canonical_instruction','action_title'].includes(candidate.marks[1].text_ref));}
 else assert.throws(()=>p.finish(),new RegExp(c.validation_reason));
});
