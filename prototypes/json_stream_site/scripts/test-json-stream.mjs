import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {randomBytes} from 'node:crypto';
import worker from '../dist/server/index.js';
import {localDB} from './local-db.mjs';
import {FindingParserJS,SSEDecoderJS,streamStrictJSON} from '../worker/stream-core.js';
import {consumeAnalysisStream,startAnalysisStream} from '../assets/json-stream-client.js';
const definition=JSON.parse(await readFile('data/experiment.json','utf8')),policy=JSON.parse(await readFile('data/guided-policy.json','utf8'));
const cp=definition.checkpoints[4],actions=policy.procedures[cp.id];
const findings=(cp,actions,status='unknown')=>({criteria:cp.completion_criteria.map(c=>({criterion_id:c.id,status,evidence:'Controlled field: "pi/2", ଓଡ଼ିଆ; no real Simulink claim.'})),action_findings:actions.map(a=>({action_id:a.id,status,evidence:'Controlled action fixture.'})),uncertainties:[],summary:'Controlled fixture, not a real learner screen.'});
const valid=findings(cp,actions),text=JSON.stringify(valid);
test('every byte boundary including Unicode/escapes emits only complete stable-ID rows',()=>{
 const bytes=new TextEncoder().encode(text),decoder=new TextDecoder('utf-8',{fatal:true});const parser=new FindingParserJS(cp,actions);let events=[];
 for(const byte of bytes)events.push(...parser.feed(decoder.decode(new Uint8Array([byte]),{stream:true})));
 parser.feed(decoder.decode());assert.equal(events.length,cp.completion_criteria.length+actions.length);assert.deepEqual(JSON.parse(JSON.stringify(parser.finish())),valid);
});
test('a complete finding precedes closing arrays, summary and final response',()=>{
 const parser=new FindingParserJS(cp,actions),prefix='{"criteria":['+JSON.stringify(valid.criteria[0]);const events=parser.feed(prefix);
 assert.equal(events.length,1);assert.equal(parser.closed,false);assert.throws(()=>parser.finish());
});
test('duplicates, missing/foreign IDs, extra keys, truncation and trailing content are rejected',()=>{
 const cases=[text.slice(0,-1),text+'{}',text.replace('"status":"unknown"','"status":"match","status":"unknown"'),text.replace(valid.criteria[0].criterion_id,'FOREIGN'),JSON.stringify({...valid,criteria:[valid.criteria[0],valid.criteria[0]]}),JSON.stringify({...valid,action_findings:[]}),JSON.stringify({...valid,extra:true}),text.replace('"uncertainties":[]','"uncertainties":[],"uncertainties":[]')];
 for(const raw of cases)assert.throws(()=>{const parser=new FindingParserJS(cp,actions);parser.feed(raw);parser.finish();});
});
test('SSE framing handles fragmented UTF-8 and rejects unterminated provider events',()=>{
 const message='data: '+JSON.stringify({value:'ଓଡ଼ିଆ'})+'\r\n\r\n',bytes=new TextEncoder().encode(message),decoder=new SSEDecoderJS();let result=[];
 for(const byte of bytes)result.push(...decoder.feed(new Uint8Array([byte])));decoder.finish();assert.equal(streamStrictJSON(result[0]).value,'ଓଡ଼ିଆ');
 const incomplete=new SSEDecoderJS();incomplete.feed(new TextEncoder().encode('data: {}'));assert.throws(()=>incomplete.finish());
});
const image=Buffer.from(await readFile('scripts/fixtures/jpeg.txt','utf8'),'base64');
const meta={type:'frame',capture_epoch:1,view_revision:1,sequence:1,captured_elapsed_ms:20,width:96,height:54,source_width:96,source_height:54,byte_count:image.length,mime_type:'image/jpeg'};
const request=(path,method='GET',body=null,cookie=null,extra={})=>new Request('https://receiver.test'+path,{method,headers:{'oai-authenticated-user-id':'stream-owner',Origin:'https://receiver.test',...(cookie?{Cookie:cookie}:{}),...(body?{'Content-Type':'application/json'}:{}),...extra},...(body?{body:typeof body==='string'||body instanceof Uint8Array?body:JSON.stringify(body)}:{})});
const cookieOf=r=>r.headers.get('set-cookie').split(';')[0];
async function prepare(t){t.mock.timers.enable({apis:['Date'],now:Date.UTC(2026,9,15)});const env={DB:localDB(),CAPTURE_RECEIPT_KEY:randomBytes(32).toString('hex'),GEMINI_API_KEY:'fixture-only'};t.after(()=>env.DB.close());
 let r=await worker.fetch(request('/lab-sessions','POST',{operator_trial:true,model_name:'synthetic_stream_fixture',progression_mode:'screen_guided'}),env),state=await r.json();
 r=await worker.fetch(request('/screen-sessions','POST'),env);const capture=(await r.json()).session_id;let cookie=cookieOf(r);
 r=await worker.fetch(request(`/screen-sessions/${capture}/frame`,'POST',image,cookie,{'Content-Type':'image/jpeg','X-Capture-Frame':JSON.stringify(meta)}),env);const frame=JSON.parse(Buffer.from(r.headers.get('X-Capture-Observation'),'base64').toString()).observation.latest_frame;cookie=cookieOf(r);
 r=await worker.fetch(request(`/lab-sessions/${state.lab_session_id}/attach`,'POST',{revision:state.revision,capture_session_id:capture},cookie),env);state=await r.json();return {env,state,cookie,frame};
}
function fixtureTransport(env,{gate=null,finish='STOP'}={}){let call=0;env.LAB_STREAM_FETCH=async(url,options)=>{
 assert.match(url,/:streamGenerateContent\?alt=sse$/);const body=JSON.parse(options.body),context=JSON.parse(body.contents[0].parts[0].text),cp=context.checkpoint,actions=context.procedure;
 assert.deepEqual(Object.keys(body.generationConfig.responseJsonSchema.properties),['criteria','action_findings','uncertainties']);call++;
 const value=findings(cp,actions);delete value.summary;const whole=JSON.stringify(value),prefix='{"criteria":['+JSON.stringify(value.criteria[0]);const encoder=new TextEncoder();
 return new Response(new ReadableStream({async start(controller){
  const send=(text,stop=false)=>controller.enqueue(encoder.encode('data: '+JSON.stringify({candidates:[{content:{parts:[{text}]},...(stop?{finishReason:finish}:{})}]} )+'\n\n'));
  const abort=()=>controller.error(new DOMException('Cancelled','AbortError'));options.signal.addEventListener('abort',abort,{once:true});
  try{send(prefix);if(gate)await gate;send(whole.slice(prefix.length),true);controller.close();}catch{}finally{options.signal.removeEventListener('abort',abort);}
 }}),{headers:{'Content-Type':'text/event-stream'}});
 };return ()=>call;}
function streamRequest(s,cookie,m=meta){return request(`/lab-sessions/${s.lab_session_id}/check-stream`,'POST',image,cookie,{'Content-Type':'image/jpeg','X-Capture-Frame':JSON.stringify(m)});}
function events(raw){return raw.split('\n\n').filter(Boolean).map(s=>JSON.parse(s.slice(6)));}
test('real tracker stream sends trusted admission and tentative row before generation finishes; guidance precedes snapshot',async t=>{
 const p=await prepare(t);let release;const gate=new Promise(resolve=>release=resolve);fixtureTransport(p.env,{gate});
 const response=await worker.fetch(streamRequest(p.state,p.cookie),p.env),reader=response.body.getReader();let prefix='';
 while(!prefix.includes('provisional_findings'))prefix+=new TextDecoder().decode((await reader.read()).value);
 const first=events(prefix);assert.equal(first[0].type,'admitted');assert.ok(first[0].frame.sha256);
 const during=await(await worker.fetch(request(`/lab-sessions/${p.state.lab_session_id}`),p.env)).json();assert.equal(during.runtime.analysis_status,'checking');assert.equal(during.queue.done_checkpoint_ids.length,0);assert.equal(during.runtime.candidate,null);
 release();let suffix='';while(true){const {value,done}=await reader.read();if(done)break;suffix+=new TextDecoder().decode(value);}
 const all=events(prefix+suffix),types=all.map(e=>e.type);assert.ok(types.indexOf('guidance_committed')<types.indexOf('state_snapshot'));assert.equal(types.at(-1),'stream_complete');
 const result=all.find(e=>e.type==='state_snapshot').state;assert.equal(result.runtime.candidate.prompt_version,'dsb-step-observer/v4-short-decision1');assert.equal(result.queue.done_checkpoint_ids.length,0);assert.ok(result.runtime.last_analysis_timing.first_finding_ms!==null);
});
test('short decision rejects summary injection and is complete without model prose',()=>{
 const value=structuredClone(valid);delete value.summary;const parser=new FindingParserJS(cp,actions,true);parser.feed(JSON.stringify(value));assert.deepEqual(JSON.parse(JSON.stringify(parser.finish())),value);
 assert.throws(()=>{const bad=new FindingParserJS(cp,actions,true);bad.feed(text);bad.finish();});
});
test('committed core starts another owned check while the old auxiliary tail is blocked',async t=>{
 const p=await prepare(t);fixtureTransport(p.env);let release;const gate=new Promise(resolve=>release=resolve);let tails=0;
 p.env.LAB_STREAM_AUXILIARY=async()=>{if(++tails===1)await gate;};
 const r=await worker.fetch(streamRequest(p.state,p.cookie),p.env),seen=[];
 const pipe=startAnalysisStream(r,{expectedFrame:p.frame,expectedContext:{lab_session_id:p.state.lab_session_id},onEvent:e=>seen.push(e.type)});
 const core=await pipe.committed;assert.equal(core.projection,'committed-decision/v1');assert.ok(!('evidence' in core));assert.ok(!seen.includes('stream_complete'));
 assert.equal((await p.env.DB.prepare('SELECT lease_owner FROM provider_rotation').first()).lease_owner,null);
 t.mock.timers.tick(3100);const m={...meta,sequence:2,captured_elapsed_ms:3120};let response=await worker.fetch(request(`/screen-sessions/${core.workspace.capture_session_id}/frame`,'POST',image,p.cookie,{'Content-Type':'image/jpeg','X-Capture-Frame':JSON.stringify(m)}),p.env);const cookie=cookieOf(response);
 const next=events(await(await worker.fetch(streamRequest(core,cookie,m),p.env)).text()).find(e=>e.type==='guidance_committed').state;
 assert.ok(next.revision>core.revision);release();const old=await pipe.completion;assert.equal(old.revision,core.revision);
 const current=await(await worker.fetch(request(`/lab-sessions/${core.lab_session_id}`),p.env)).json();assert.equal(current.revision,next.revision);
});
test('failure of auxiliary delivery cannot reject or roll back the committed core',async t=>{
 const p=await prepare(t);fixtureTransport(p.env);p.env.LAB_STREAM_AUXILIARY=async()=>{throw Error('controlled_tail_failure');};
 const pipe=startAnalysisStream(await worker.fetch(streamRequest(p.state,p.cookie),p.env),{expectedFrame:p.frame,expectedContext:{lab_session_id:p.state.lab_session_id},onEvent(){}});
 const core=await pipe.committed;await assert.rejects(pipe.completion);const current=await(await worker.fetch(request(`/lab-sessions/${core.lab_session_id}`),p.env)).json();assert.equal(current.revision,core.revision);assert.equal(current.runtime.analysis_status,'available');
});
test('non-STOP response never becomes evidence or canonical guidance',async t=>{
 const p=await prepare(t);fixtureTransport(p.env,{finish:'MAX_TOKENS'});const all=events(await(await worker.fetch(streamRequest(p.state,p.cookie),p.env)).text());
 assert.ok(!all.some(e=>e.type==='guidance_committed'));const current=await(await worker.fetch(request(`/lab-sessions/${p.state.lab_session_id}`),p.env)).json();assert.equal(current.runtime.candidate,null);assert.equal(current.runtime.analysis_status,'waiting_for_provider');
});
test('a changed visit discards the entire result including stale text',async t=>{
 const p=await prepare(t);let release;fixtureTransport(p.env,{gate:new Promise(resolve=>release=resolve)});const r=await worker.fetch(streamRequest(p.state,p.cookie),p.env),reader=r.body.getReader();let raw='';while(!raw.includes('provisional_findings'))raw+=new TextDecoder().decode((await reader.read()).value);
 let current=await(await worker.fetch(request(`/lab-sessions/${p.state.lab_session_id}`),p.env)).json();await worker.fetch(request(`/lab-sessions/${p.state.lab_session_id}/action`,'POST',{revision:current.revision,action:'revisit',checkpoint_id:'CP-DSB-01'}),p.env);release();
 while(true){const next=await reader.read();if(next.done)break;raw+=new TextDecoder().decode(next.value);}
 const all=events(raw);assert.ok(all.some(e=>e.type==='discarded'));assert.ok(!all.some(e=>e.type==='guidance_committed'));
});
test('disconnect fences results and releases the checking state',async t=>{
 const p=await prepare(t);let release;fixtureTransport(p.env,{gate:new Promise(resolve=>release=resolve)});const r=await worker.fetch(streamRequest(p.state,p.cookie),p.env),reader=r.body.getReader();let raw='';while(!raw.includes('provisional_findings'))raw+=new TextDecoder().decode((await reader.read()).value);await reader.cancel();release();
 await new Promise(resolve=>setTimeout(resolve,20));const current=await(await worker.fetch(request(`/lab-sessions/${p.state.lab_session_id}`),p.env)).json();assert.equal(current.runtime.analysis_status,'cancelled');assert.equal(current.runtime.candidate,null);
});
test('503 changes to the next key and all-failed sweep waits a minute',async t=>{
 const p=await prepare(t);p.env.GEMINI_API_KEYS=JSON.stringify(['key-one','key-two']);const keys=[];p.env.LAB_STREAM_FETCH=async(url,options)=>{keys.push(options.headers['x-goog-api-key']);return new Response('unavailable',{status:503});};
 const all=events(await(await worker.fetch(streamRequest(p.state,p.cookie),p.env)).text());assert.deepEqual(keys,['key-one','key-two']);assert.ok(all.some(e=>e.type==='attempt_reset'));const result=all.find(e=>e.type==='analysis_waiting').state;assert.ok(result.runtime.retry_after_ms>=60000);
});
test('the browser rejects foreign frame provenance and deduplicates old sequence numbers',async()=>{
 const frame={frame_id:'frame',sha256:'hash',width:1,height:1,byte_count:1,view_revision:1},context={visit_id:'visit'},base={schema:'lab-analysis-stream/v1',request_id:'request',server_time:'fixture'};
 const packets=[{...base,event_sequence:1,type:'admitted',frame,context},{...base,event_sequence:1,type:'provisional_findings'},{...base,event_sequence:2,type:'state_snapshot',state:{revision:1}},{...base,event_sequence:3,type:'stream_complete'}];
 const response=()=>new Response(packets.map(e=>'data: '+JSON.stringify(e)+'\n\n').join(''),{headers:{'Content-Type':'text/event-stream'}});const seen=[];
 await consumeAnalysisStream(response(),{expectedFrame:frame,expectedContext:context,onEvent:e=>seen.push(e.type)});assert.deepEqual(seen,['admitted','state_snapshot','stream_complete']);
 await assert.rejects(consumeAnalysisStream(response(),{expectedFrame:{...frame,sha256:'foreign'},expectedContext:context,onEvent(){}}));
});
