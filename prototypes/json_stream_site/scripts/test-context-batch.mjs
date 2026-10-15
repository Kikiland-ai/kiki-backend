import test from 'node:test';
import assert from 'node:assert/strict';
import {streamContextBatch} from '../worker/context-batch.js';
import {benchmarkContextBatch} from './benchmark-context-batch.mjs';

test('chunk shapes preserve every finding and have bounded reads, including no-win fragmented control',async()=>{const report=await benchmarkContextBatch({rttMs:0,repeats:1});assert.ok(report.passed);assert.equal(report.summary[0].per_chunk.reads,1);assert.equal(report.summary[2].per_chunk.reads,7);});
test('a new batch never reuses a prior context snapshot',async()=>{
 let valid=true,reads=0;const shown=[],gate=streamContextBatch({signal:new AbortController().signal,read:async()=>{reads++;return valid;},valid:v=>v,push:e=>shown.push(e)});
 await gate.batch([{id:1},{id:2}]);valid=false;await assert.rejects(gate.batch([{id:3},{id:4}]),/stale_context/);assert.equal(reads,2);assert.deepEqual(shown,[{id:1},{id:2}]);
});
test('changed visit/view/condition/workspace/revision and inactive capture reject the whole batch',async()=>{
 const trusted={visit:'visit',view:1,condition:'baseline',workspace:'workspace',revision:5,active:true,capture:true};
 for(const key of Object.keys(trusted)){
  const current={...trusted,[key]:typeof trusted[key]==='boolean'?false:'changed'},shown=[];
  const gate=streamContextBatch({signal:new AbortController().signal,read:async()=>current,valid:s=>JSON.stringify(s)===JSON.stringify(trusted),push:e=>shown.push(e)});
  await assert.rejects(gate.batch([{id:1},{id:2}]),/stale_context/);assert.deepEqual(shown,[]);
 }
});
test('disconnect during context read publishes nothing from the pending batch',async()=>{
 const controller=new AbortController(),shown=[];let release,entered;const ready=new Promise(r=>entered=r),wait=new Promise(r=>release=r);
 const gate=streamContextBatch({signal:controller.signal,read:async()=>{entered();await wait;return true;},valid:v=>v,push:e=>shown.push(e)}),pending=gate.batch([{id:1},{id:2}]);await ready;controller.abort();release();await assert.rejects(pending,/analysis_cancelled/);assert.deepEqual(shown,[]);
});
test('empty transport fragments do not trigger DB reads and oversized batches fail closed',async()=>{
 let reads=0;const gate=streamContextBatch({signal:new AbortController().signal,read:async()=>{reads++;return true;},valid:v=>v,push(){}});await gate.batch([]);assert.equal(reads,0);await assert.rejects(gate.batch(Array(65).fill({})),/invalid_output/);
});
