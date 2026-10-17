import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {providerRequest} from '../worker/provider.js';
import {localDB} from './local-db.mjs';
const hash=v=>createHash('sha256').update(v).digest('hex');
const clock=t=>t.mock.timers.enable({apis:['Date'],now:Date.UTC(2026,9,14)});
const config=['fixture-a','fixture-b','fixture-c'];
const ok=()=>Response.json({ok:true});

test('D1 cursor survives fresh Worker environments and rotates across models without storing keys',async t=>{
 clock(t);const DB=localDB();t.after(()=>DB.close());const calls=[];
 for(let i=0;i<7;i++)await providerRequest({DB,GEMINI_API_KEYS:JSON.stringify(config)},i%2?'model-a':'model-b',{},async(url,opt)=>{calls.push(opt.headers['x-goog-api-key']);return ok();});
 assert.deepEqual(calls,[...config,...config,'fixture-a']);
 const row=await DB.prepare('SELECT * FROM provider_rotation').first();assert.ok(!JSON.stringify(row).includes('fixture-'));assert.equal(row.lease_owner,null);
});
test('same-project 503 fails over immediately; next request starts on next distinct key',async t=>{
 clock(t);const calls=[],env={GEMINI_API_KEYS:JSON.stringify(config)};
 const fetcher=async(url,opt)=>{calls.push(opt.headers['x-goog-api-key']);return calls.length===1?new Response('private body',{status:503}):ok();};
 await providerRequest(env,'model',{},fetcher);await providerRequest(env,'model',{},fetcher);
 assert.deepEqual(calls,config);
});
test('full failed cycle is durable, waits 60 seconds and then recovers without repeating adjacent keys',async t=>{
 clock(t);const DB=localDB();t.after(()=>DB.close());let env={DB,GEMINI_API_KEYS:JSON.stringify(config)},healthy=false;const calls=[];
 const fetcher=async(url,opt)=>{calls.push(opt.headers['x-goog-api-key']);return healthy?ok():new Response('',{status:503});};
 await assert.rejects(providerRequest(env,'model',{},fetcher),e=>e.message==='provider_http_503'&&e.retry_after_ms===60000);
 assert.deepEqual(calls,config);env={DB,GEMINI_API_KEYS:JSON.stringify(config)};
 t.mock.timers.tick(59000);await assert.rejects(providerRequest(env,'model',{},fetcher));assert.equal(calls.length,3);
 t.mock.timers.tick(1000);healthy=true;await providerRequest(env,'model',{},fetcher);await providerRequest(env,'model',{},fetcher);assert.deepEqual(calls.slice(-2),['fixture-a','fixture-b']);
});
test('429 blocks siblings in one project, honors longer Retry-After and may use independent pool',async t=>{
 clock(t);const calls=[],env={GEMINI_API_KEYS:JSON.stringify([{key:'fixture-a',quota_pool:'p1'},{key:'fixture-b',quota_pool:'p1'},{key:'fixture-c',quota_pool:'p2'}])};
 await providerRequest(env,'model',{},async(url,opt)=>{const key=opt.headers['x-goog-api-key'];calls.push(key);return key==='fixture-a'?new Response('',{status:429,headers:{'Retry-After':'180'}}):ok();});
 assert.deepEqual(calls,['fixture-a','fixture-c']);
 await assert.rejects(providerRequest(env,'model',{},async()=>{throw Error('must not run');}),e=>e.retry_after_ms===180000);
 const same={GEMINI_API_KEYS:JSON.stringify(['fixture-a','fixture-b'])};let count=0;
 await assert.rejects(providerRequest(same,'model',{},async()=>{count++;return new Response('',{status:429,headers:{'Retry-After':'180'}});}),e=>e.retry_after_ms===180000);assert.equal(count,1);
});
test('concurrent isolates serialize selection with a lease and cancelled requests release it',async t=>{
 clock(t);const DB=localDB();t.after(()=>DB.close());const env={DB,GEMINI_API_KEYS:JSON.stringify(config)};let release,started;const gate=new Promise(r=>release=r),admitted=new Promise(r=>started=r);const calls=[];
 const pending=providerRequest(env,'model',{},async(url,opt)=>{calls.push(opt.headers['x-goog-api-key']);started();await gate;return ok();});
 await admitted;await assert.rejects(providerRequest({...env},'model',{},async()=>ok()),/provider_rotation_busy/);
 release();await pending;await providerRequest({...env},'model',{},async(url,opt)=>{calls.push(opt.headers['x-goog-api-key']);return ok();});assert.deepEqual(calls,['fixture-a','fixture-b']);
});
test('auth failure quarantines its key; malformed and duplicated credentials fail closed',async t=>{
 clock(t);const calls=[],env={GEMINI_API_KEYS:JSON.stringify(config)};
 await providerRequest(env,'model',{},async(url,opt)=>{const key=opt.headers['x-goog-api-key'];calls.push(key);return key==='fixture-a'?new Response('',{status:403}):ok();});
 assert.deepEqual(calls,['fixture-a','fixture-b']);
 for(const keys of [[],['fixture-a','fixture-a'],[''],null])await assert.rejects(providerRequest({GEMINI_API_KEYS:JSON.stringify(keys)},'model',{},async()=>ok()),/invalid_provider_configuration/);
});
test('unsupported payload/model is not sent through every key',async t=>{
 clock(t);let calls=0;await assert.rejects(providerRequest({GEMINI_API_KEYS:JSON.stringify(config)},'model',{},async()=>{calls++;return new Response('',{status:400});}),/provider_http_400/);assert.equal(calls,1);
});
test('crash reservation is respected until lease expiry, then picks the following key',async t=>{
 clock(t);const DB=localDB();t.after(()=>DB.close());const env={DB,GEMINI_API_KEYS:JSON.stringify(config)};
 await providerRequest(env,'model',{},async()=>ok());const row=await DB.prepare('SELECT * FROM provider_rotation').first();
 await DB.prepare('UPDATE provider_rotation SET lease_owner=?,lease_until=? WHERE router_id=?').bind('crashed',Date.now()+30000,row.router_id).run();
 await assert.rejects(providerRequest({...env},'model',{},async()=>ok()),/provider_rotation_busy/);
 t.mock.timers.tick(30001);let picked;await providerRequest({...env},'model',{},async(url,opt)=>{picked=opt.headers['x-goog-api-key'];return ok();});assert.equal(picked,'fixture-b');
});
test('20-second frame deadline preserves partial failed cycle for the next fresh request',async t=>{
 clock(t);const DB=localDB();t.after(()=>DB.close());const env={DB,GEMINI_API_KEYS:JSON.stringify(config)},calls=[];
 await assert.rejects(providerRequest(env,'model',{},async(url,opt)=>{calls.push(opt.headers['x-goog-api-key']);t.mock.timers.tick(20000);return new Response('',{status:503});}),e=>e.retry_after_ms===5000);
 assert.deepEqual(calls,['fixture-a']);
 await assert.rejects(providerRequest({...env},'model',{},async(url,opt)=>{calls.push(opt.headers['x-goog-api-key']);return new Response('',{status:503});}),e=>e.retry_after_ms===60000);
 assert.deepEqual(calls,config);
});
