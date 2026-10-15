import test from 'node:test';
import assert from 'node:assert/strict';
import worker from '../dist/server/index.js';
const env={KIKI_FASTAPI_ORIGIN:'https://python-backend.test',KIKI_PROXY_SECRET:'controlled-test-proxy-key-at-least-32'};
const request=(path,method='GET',headers={},body)=>new Request('https://receiver.test'+path,{method,headers:{'oai-authenticated-user-id':'real-site-owner',Origin:'https://receiver.test',...headers},...(body?{body}: {})});
test('fixed Python proxy preserves request body and overrides caller identity/secrets',async()=>{
 let forwarded;
 const r=await worker.fetch(request('/lab-sessions','POST',{'Content-Type':'application/json','x-kiki-owner':'forged-owner','x-kiki-proxy-key':'forged','Cookie':'untrusted=1'},'{"operator_trial":true,"model_name":"fixture"}'),{...env,PYTHON_PROXY_FETCH:async req=>{forwarded=req;return Response.json({backend:'python'});}});
 assert.equal(r.status,200);assert.equal(forwarded.url,'https://python-backend.test/lab-sessions');
 assert.equal(forwarded.headers.get('x-kiki-owner'),'real-site-owner');assert.equal(forwarded.headers.get('x-kiki-proxy-key'),env.KIKI_PROXY_SECRET);
 assert.equal(forwarded.headers.get('origin'),'https://python-backend.test');assert.equal(forwarded.headers.get('cookie'),null);
 assert.equal(forwarded.headers.get('authorization'),null);assert.equal(JSON.parse(await forwarded.text()).model_name,'fixture');
});
test('foreign browser mutations and unauthenticated lab reads never call Python',async()=>{
 let calls=0;const e={...env,PYTHON_PROXY_FETCH:async()=>{calls++;return Response.json({});}};
 assert.equal((await worker.fetch(request('/lab-sessions','POST',{Origin:'https://foreign.test'},'{}'),e)).status,403);
 assert.equal((await worker.fetch(request('/lab-sessions','GET',{'oai-authenticated-user-id':''}),e)).status,401);
 assert.equal(calls,0);
});
test('WebSocket handoff forwards trusted owner/key and same-origin upgrade',async()=>{
 let forwarded;const handshake={status:101,webSocket:{controlledFixture:true}};
 const r=await worker.fetch(request('/screen-sessions/01234567890123456789012345678901/stream','GET',{Upgrade:'websocket','Sec-WebSocket-Key':'test-key','Sec-WebSocket-Version':'13'}),{...env,PYTHON_PROXY_FETCH:async req=>{forwarded=req;return handshake;}});
 assert.equal(r,handshake);assert.equal(forwarded.headers.get('upgrade'),'websocket');assert.equal(forwarded.headers.get('x-kiki-owner'),'real-site-owner');
 assert.equal((await worker.fetch(request('/screen-sessions/id/stream','GET',{Upgrade:'websocket',Origin:'https://foreign.test'}),env)).status,403);
});
test('bad origins, missing secrets, redirects and unavailable Python fail closed',async()=>{
 for(const origin of ['http://unsafe.test','https://user:password@unsafe.test','https://unsafe.test/path','https://receiver.chatgpt.site'])
  assert.equal((await worker.fetch(request('/'),{...env,KIKI_FASTAPI_ORIGIN:origin})).status,503);
 assert.equal((await worker.fetch(request('/'),{...env,KIKI_PROXY_SECRET:''})).status,503);
 assert.equal((await worker.fetch(request('/lab-sessions'),{...env,PYTHON_PROXY_FETCH:async()=>Response.redirect('https://foreign.test')})).status,502);
 assert.equal((await worker.fetch(request('/lab-sessions'),{...env,PYTHON_PROXY_FETCH:async()=>{throw Error('private upstream body');}})).status,502);
});
test('MCP discovery can proxy without an owner but does not invent one',async()=>{
 let owner='unset';const r=await worker.fetch(request('/mcp','POST',{'oai-authenticated-user-id':'',Origin:''},'{"method":"tools/list"}'),{...env,PYTHON_PROXY_FETCH:async req=>{owner=req.headers.get('x-kiki-owner');return Response.json({});}});
 assert.equal(r.status,200);assert.equal(owner,null);
});
