import test from 'node:test';
import assert from 'node:assert/strict';
import {randomBytes, createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import worker from '../dist/server/index.js';

const env = {CAPTURE_RECEIPT_KEY: randomBytes(32).toString('hex')};
const image = Buffer.from(await readFile('scripts/fixtures/jpeg.txt','utf8'),'base64');
const meta = {type:'frame',capture_epoch:1,view_revision:1,sequence:1,captured_elapsed_ms:20,
  width:96,height:54,source_width:96,source_height:54,byte_count:image.length,mime_type:'image/jpeg'};
const cookieOf = result => result.headers.get('set-cookie').split(';')[0];
function request(path,method='GET',cookie=null,body=null,extra={}) {
  return new Request('https://receiver.test'+path,{method,headers:{
    'oai-authenticated-user-id':'fixture-owner', 'Origin':'https://receiver.test',
    ...(cookie ? {Cookie:cookie}:{}), ...extra,
  },...(body===null ? {} : {body})});
}
async function session() {
  const result=await worker.fetch(request('/screen-sessions','POST'),env);
  assert.equal(result.status,201);
  return {id:(await result.json()).session_id,cookie:cookieOf(result)};
}
function frame(s,m=meta,bytes=image) {
  return worker.fetch(request(`/screen-sessions/${s.id}/frame`,'POST',s.cookie,bytes,
    {'Content-Type':'image/jpeg','X-Capture-Frame':JSON.stringify(m)}),env);
}

test('server receives and returns exact JPEG bytes with signed provenance',async()=>{
  const s=await session();const result=await frame(s);
  assert.equal(result.status,200);
  assert.deepEqual(Buffer.from(await result.arrayBuffer()),image);
  const snapshot=JSON.parse(Buffer.from(result.headers.get('X-Capture-Observation'),'base64').toString());
  assert.equal(snapshot.received_frame_count,1);
  assert.equal(snapshot.observation.latest_frame.sha256,createHash('sha256').update(image).digest('hex'));
  assert.equal(snapshot.observation.analysis_status,'not_enabled');
  assert.equal(snapshot.observation.summary,null);
  assert.equal(snapshot.evidence.server_image_archive,false);
  assert.match(result.headers.get('Set-Cookie'),/HttpOnly; Secure; SameSite=Strict/);
  const latest=await worker.fetch(request(`/screen-sessions/${s.id}/observation`,'GET',cookieOf(result)),env);
  assert.equal((await latest.json()).received_frame_count,1);
});
test('identity and same-origin guards reject unauthorized writes',async()=>{
  const noIdentity=new Request('https://receiver.test/screen-sessions',{method:'POST',headers:{Origin:'https://receiver.test'}});
  assert.equal((await worker.fetch(noIdentity,env)).status,401);
  assert.equal((await worker.fetch(request('/screen-sessions','POST',null,null,{Origin:'https://foreign.test'}),env)).status,403);
  const s=await session();
  assert.equal((await worker.fetch(request(`/screen-sessions/${s.id}/observation`,'GET',s.cookie,null,{'oai-authenticated-user-id':'other-owner'}),env)).status,404);
});
test('receipt tampering is rejected',async()=>{
  const s=await session();const parts=s.cookie.split('=');
  const value=s.cookie.slice(s.cookie.indexOf('=')+1);
  const altered=(value[0]==='A'?'B':'A')+value.slice(1);
  const result=await worker.fetch(request(`/screen-sessions/${s.id}/observation`,'GET',parts[0]+'='+altered),env);
  assert.equal(result.status,401);
});
test('strict metadata, bounded size and JPEG dimensions',async()=>{
  const s=await session();
  assert.equal((await frame(s,{...meta,sequence:true})).status,422);
  assert.equal((await frame(s,{...meta,byte_count:1000001})).status,422);
  assert.equal((await frame(s,{...meta,width:160,height:90})).status,422);
  assert.equal((await frame(s,{...meta,byte_count:5},Buffer.from('hello'))).status,422);
});
test('pause, resume and stop are honored by the signed current receipt',async()=>{
  const s=await session();
  let result=await worker.fetch(request(`/screen-sessions/${s.id}/pause`,'POST',s.cookie),env);
  s.cookie=cookieOf(result);assert.equal((await result.json()).capture_status,'paused');
  assert.equal((await frame(s)).status,409);
  result=await worker.fetch(request(`/screen-sessions/${s.id}/resume`,'POST',s.cookie),env);
  s.cookie=cookieOf(result);assert.equal((await result.json()).capture_status,'sharing');
  result=await frame(s);assert.equal(result.status,200);s.cookie=cookieOf(result);
  result=await worker.fetch(request(`/screen-sessions/${s.id}/stop`,'POST',s.cookie),env);
  s.cookie=cookieOf(result);assert.equal((await result.json()).capture_status,'ended');
  assert.equal((await frame(s,{...meta,sequence:2,captured_elapsed_ms:2020})).status,409);
});
test('ordering and sample admission are bounded',async()=>{
  const s=await session();const result=await frame(s);s.cookie=cookieOf(result);
  assert.equal((await frame(s)).status,409);
  const limited = await frame(s,{...meta,sequence:2,captured_elapsed_ms:2020});
  assert.equal(limited.status,429);
  assert.ok(Number(limited.headers.get('Retry-After')) > 0);
  const problem = await limited.json();
  assert.equal(problem.code,'sampling_rate_limited');
  assert.ok(problem.retry_after_ms > 0 && problem.retry_after_ms <= 1800);
});
test('health and asset routes work without exposing image storage',async()=>{
  const health=await worker.fetch(new Request('https://receiver.test/health'),env);
  assert.equal((await health.json()).image_storage,'none');
  const page=await worker.fetch(new Request('https://receiver.test/'),env);
  assert.match(await page.text(),/Share screen/);
});
test('same sharing session receives over 1000 frames and continues beyond thirty minutes',async t=>{
 t.mock.timers.enable({apis:['Date'],now:Date.UTC(2026,9,14)});
 const s=await session();let result;
 for(let sequence=1;sequence<=1002;sequence++){
  t.mock.timers.tick(2000);result=await frame(s,{...meta,sequence,captured_elapsed_ms:sequence*2000});assert.equal(result.status,200);s.cookie=cookieOf(result);
 }
 const value=JSON.parse(Buffer.from(result.headers.get('X-Capture-Observation'),'base64').toString());
 assert.equal(value.received_frame_count,1002);assert.equal(value.capture_status,'sharing');assert.match(result.headers.get('Set-Cookie'),/Max-Age=2592000/);
});
