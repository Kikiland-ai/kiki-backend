import test from 'node:test';
import assert from 'node:assert/strict';
import {benchmarkProviderIO} from './benchmark-provider-io.mjs';
import {providerRequest} from '../worker/provider.js';
import {localDB} from './local-db.mjs';

test('healthy routing is four DB operations for 1, 4 and 16 keys, with identical control results',async()=>{
 for(const keyCount of [1,4,16]){const report=await benchmarkProviderIO({rttMs:0,repeats:1,keyCount});assert.equal(report.summary.batched.db_operations,4);assert.equal(report.summary.batched.before_http_operations,3);assert.equal(report.summary.serial.db_operations,3*keyCount+5);}
});
test('a batched health snapshot is refreshed after 429, so sibling keys are never sent',async t=>{
 const DB=localDB();t.after(()=>DB.close());const keys=[{key:'fixture-a',quota_pool:'one'},{key:'fixture-b',quota_pool:'one'},{key:'fixture-c',quota_pool:'two'}],seen=[];
 const env={DB,GEMINI_API_KEYS:JSON.stringify(keys),KIKI_PROVIDER_IO:'batched'};
 await providerRequest(env,'fixture',{},async(url,options)=>{const key=options.headers['x-goog-api-key'];seen.push(key);return key==='fixture-a'?new Response('',{status:429,headers:{'Retry-After':'60'}}):Response.json({ok:true});});
 assert.deepEqual(seen,['fixture-a','fixture-c']);
});
test('atomic acquisition across DB-backed callers never dispatches a second concurrent request',async t=>{
 const DB=localDB();t.after(()=>DB.close());const env={DB,GEMINI_API_KEYS:'["fixture-a","fixture-b"]',KIKI_PROVIDER_IO:'batched'};let start,release;
 const ready=new Promise(resolve=>start=resolve),gate=new Promise(resolve=>release=resolve);let calls=0;
 const first=providerRequest(env,'fixture',{},async()=>{calls++;start();await gate;return Response.json({ok:true});});await ready;
 await assert.rejects(providerRequest({...env},'fixture',{},async()=>{calls++;return Response.json({ok:true});}),/provider_rotation_busy/);
 release();await first;assert.equal(calls,1);assert.equal((await DB.prepare('SELECT lease_owner FROM provider_rotation').first()).lease_owner,null);
});
test('routing phase telemetry reports actual database operations without credentials',async t=>{
 const DB=localDB();t.after(()=>DB.close());let metrics;
 await providerRequest({DB,GEMINI_API_KEYS:'["fixture-a","fixture-b"]'},'fixture',{},async()=>Response.json({fixture:true}),{signal:new AbortController().signal,async reset(){},async consume(r){return r.json();},onMetrics(value){metrics=value;}});
 assert.equal(metrics.provider_db_operations,4);assert.equal(metrics.provider_http_attempts,1);assert.equal(metrics.provider_io_mode,'batched');assert.ok(metrics.provider_first_dispatch_ms>=0);assert.ok(metrics.provider_headers_ms>=0);assert.ok(!JSON.stringify(metrics).includes('fixture-a'));
});
