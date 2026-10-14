import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {randomBytes} from 'node:crypto';
import worker from '../dist/server/index.js';
import {localDB} from './local-db.mjs';
const image=Buffer.from(await readFile('scripts/fixtures/jpeg.txt','utf8'),'base64');
const meta={type:'frame',capture_epoch:1,view_revision:1,sequence:1,captured_elapsed_ms:20,width:96,height:54,source_width:96,source_height:54,byte_count:image.length,mime_type:'image/jpeg'};
const request=(path,method='GET',body=null,cookie=null,extra={})=>new Request('https://receiver.test'+path,{method,headers:{'oai-authenticated-user-id':'lab-owner',Origin:'https://receiver.test',...(cookie?{Cookie:cookie}:{}),...(body?{'Content-Type':'application/json'}:{}),...extra},...(body?{body:typeof body==='string'||body instanceof Uint8Array?body:JSON.stringify(body)}:{})});
const cookieOf=r=>r.headers.get('set-cookie').split(';')[0];
function setup(t){t.mock.timers.enable({apis:['Date'],now:Date.UTC(2026,9,14)});
 const env={DB:localDB(),CAPTURE_RECEIPT_KEY:randomBytes(32).toString('hex'),GEMINI_API_KEY:'local-test'};
 env.LAB_ANALYSIS_FETCH=async(url,options)=>{const ctx=JSON.parse(JSON.parse(options.body).contents[0].parts[0].text);return Response.json({candidates:[{finishReason:'STOP',content:{parts:[{text:JSON.stringify({summary:'Controlled fixture candidate',criteria:ctx.checkpoint.completion_criteria.map(c=>({criterion_id:c.id,status:'unknown',evidence:'Synthetic test image; human review required.'})),uncertainties:[]})}]}}]});};
 t.after(()=>env.DB.close());return env;}
async function create(env,progression_mode='reviewed'){const r=await worker.fetch(request('/lab-sessions','POST',{operator_trial:true,model_name:'dsb_sc_test',progression_mode}),env);assert.equal(r.status,201);return r.json();}
async function prepare(env,s){let r=await worker.fetch(request('/screen-sessions','POST'),env);const id=(await r.json()).session_id;let cookie=cookieOf(r);
 r=await worker.fetch(request(`/screen-sessions/${id}/frame`,'POST',image,cookie,{'Content-Type':'image/jpeg','X-Capture-Frame':JSON.stringify(meta)}),env);assert.equal(r.status,200);cookie=cookieOf(r);
 r=await worker.fetch(request(`/lab-sessions/${s.lab_session_id}/attach`,'POST',{revision:s.revision,capture_session_id:id},cookie),env);assert.equal(r.status,200);return {state:await r.json(),cookie,id};}
async function check(env,s,cookie,m=meta){return worker.fetch(request(`/lab-sessions/${s.lab_session_id}/check`,'POST',image,cookie,{'Content-Type':'image/jpeg','X-Capture-Frame':JSON.stringify(m)}),env);}
async function action(env,s,body){return worker.fetch(request(`/lab-sessions/${s.lab_session_id}/action`,'POST',{revision:s.revision,...body}),env);}

test('real session initializes no synthetic readiness and survives independent capture attachment',async t=>{
 const env=setup(t);const s=await create(env);assert.equal(s.synthetic,false);assert.equal(s.evidence.length,0);assert.equal(s.readiness.required_concept_gate,'unknown');
 assert.ok(s.learner_state.concepts.every(c=>c.theory_check==='unknown'));assert.equal(s.queue.current_checkpoint_id,'CP-DSB-01');assert.equal(s.queue.done_checkpoint_ids.length,0);
 const prepared=await prepare(env,s);assert.equal(prepared.state.workspace.capture_epoch,1);assert.equal(prepared.state.queue.current_checkpoint_id,'CP-DSB-01');
 const r=await worker.fetch(request(`/lab-sessions/${s.lab_session_id}`),env);assert.equal((await r.json()).workspace.capture_session_id,prepared.id);
});
test('model candidates do not finish steps; reviewed complete bundle advances exactly once',async t=>{
 const env=setup(t),initial=await create(env),prepared=await prepare(env,initial);let r=await check(env,prepared.state,prepared.cookie);assert.equal(r.status,200);let s=await r.json();
 assert.equal(s.queue.done_checkpoint_ids.length,0);assert.equal(s.runtime.candidate.criteria[0].status,'unknown');
 const ids=s.steps[0].criteria.map(c=>c.criterion_id);r=await action(env,s,{action:'review',criterion_ids:[ids[0]],review_note:'I reviewed the workspace title in the supplied frame.'});assert.equal(r.status,200);s=await r.json();assert.equal(s.queue.current_checkpoint_id,'CP-DSB-01');
 const before=s;const body={action:'review',criterion_ids:[ids[1]],review_note:'I reviewed the model save reference in the supplied frame.'};r=await action(env,s,body);assert.equal(r.status,200);s=await r.json();
 assert.equal(s.queue.current_checkpoint_id,'CP-DSB-02');assert.deepEqual(s.queue.done_checkpoint_ids,['CP-DSB-01']);
 assert.equal((await action(env,before,body)).status,409,'Duplicate request cannot advance twice');
 const rows=(await env.DB.prepare('SELECT event_json FROM lab_events WHERE session_id=? ORDER BY sequence').bind(s.lab_session_id).all()).results.map(x=>JSON.parse(x.event_json));
 assert.equal(rows.at(-1).checkpoint_id,'CP-DSB-01','Completion event must refer to completed step, not next step');
});
test('foreign ownership, old revisions and expired checked evidence are rejected',async t=>{
 const env=setup(t);const p=await prepare(env,await create(env));let r=await check(env,p.state,p.cookie);const s=await r.json();
 assert.equal((await worker.fetch(request(`/lab-sessions/${s.lab_session_id}`,'GET',null,null,{'oai-authenticated-user-id':'other-user'}),env)).status,404);
 assert.equal((await action(env,p.state,{action:'pause'})).status,409);
 t.mock.timers.tick(21000);
 assert.equal((await action(env,s,{action:'review',criterion_ids:[s.steps[0].criteria[0].criterion_id],review_note:'Workspace reviewed in old image.'})).status,409);
});
test('pause deletes the retained image; detach and new share preserve checkpoint state',async t=>{
 const env=setup(t);const p=await prepare(env,await create(env));let r=await check(env,p.state,p.cookie);let s=await r.json();
 const pixels=await worker.fetch(request(`/lab-sessions/${s.lab_session_id}/image`),env);assert.deepEqual(Buffer.from(await pixels.arrayBuffer()),image);
 r=await action(env,s,{action:'pause'});s=await r.json();assert.equal(s.status,'paused');
 assert.equal((await worker.fetch(request(`/lab-sessions/${s.lab_session_id}/image`),env)).status,404);
 r=await action(env,s,{action:'resume'});s=await r.json();
 r=await worker.fetch(request(`/lab-sessions/${s.lab_session_id}/detach`,'POST',{revision:s.revision}),env);s=await r.json();
 assert.equal(s.runtime.capture_active,false);assert.equal(s.queue.current_checkpoint_id,'CP-DSB-01');
 const rebound=await prepare(env,s);assert.equal(rebound.state.workspace.capture_epoch,2);assert.equal(rebound.state.runtime.analysis_attempts,1);
});
test('late analysis cannot replace a revised step visit; consumed attempt persists',async t=>{
 const env=setup(t);let release;const gate=new Promise(resolve=>release=resolve);const normal=env.LAB_ANALYSIS_FETCH;
 env.LAB_ANALYSIS_FETCH=async(...args)=>{await gate;return normal(...args);};const p=await prepare(env,await create(env));
 const pending=check(env,p.state,p.cookie);await new Promise(resolve=>setTimeout(resolve,20));
 let s=await (await worker.fetch(request(`/lab-sessions/${p.state.lab_session_id}`),env)).json();
 const revisited=await action(env,s,{action:'revisit',checkpoint_id:'CP-DSB-01'});assert.equal(revisited.status,200);s=await revisited.json();
 release();assert.equal((await pending).status,409);assert.equal(s.runtime.analysis_attempts,1);assert.equal(s.runtime.candidate,null);
 const latest=await (await worker.fetch(request(`/lab-sessions/${s.lab_session_id}`),env)).json();assert.equal(latest.runtime.analysis_status,'discarded','Stale response must release the checking latch');
});
test('MCP discovery contains no data; read tools enforce owner and return checked pixels',async t=>{
 const env=setup(t);let r=await worker.fetch(new Request('https://receiver.test/mcp',{method:'POST',body:JSON.stringify({jsonrpc:'2.0',id:1,method:'tools/list'})}),env);
 assert.equal(r.status,200);assert.equal((await r.json()).result.tools.length,4);
 const p=await prepare(env,await create(env));const s=await (await check(env,p.state,p.cookie)).json();
 const rpc={jsonrpc:'2.0',id:2,method:'tools/call',params:{name:'read_checked_frame',arguments:{lab_session_id:s.lab_session_id}}};
 r=await worker.fetch(request('/mcp','POST',rpc),env);const content=(await r.json()).result.content;
 assert.equal(content[1].type,'image');assert.deepEqual(Buffer.from(content[1].data,'base64'),image);
 r=await worker.fetch(request('/mcp','POST',rpc,null,{'oai-authenticated-user-id':'other'}),env);assert.equal(r.status,404);
});
test('ephemeral frame handle binds pixels/view and fails after invalidation or expiry',async t=>{
 const env=setup(t),p=await prepare(env,await create(env));let s=await (await check(env,p.state,p.cookie)).json();
 const handle=s.runtime.candidate.frame_handle.handle_id;
 const path=`/lab-sessions/${s.lab_session_id}/frame-handles/${handle}`;
 let r=await worker.fetch(request(path),env);assert.equal(r.status,200);assert.deepEqual(Buffer.from(await r.arrayBuffer()),image);
 const provenance=JSON.parse(Buffer.from(r.headers.get('X-Frame-Provenance'),'base64').toString());assert.equal(provenance.admitted_context.view_revision,1);
 r=await action(env,s,{action:'view_changed',view_revision:2});s=await r.json();assert.equal(s.workspace.view_revision,2);assert.equal(s.runtime.candidate,null);
 assert.equal((await worker.fetch(request(path),env)).status,410);
 t.mock.timers.tick(11000);
 assert.equal((await check(env,s,p.cookie)).status,409,'Old-view frame cannot be admitted');
});
test('screen-guided mode advances visible steps after distinct matching frames without claiming mastery',async t=>{
 const env=setup(t),p=await prepare(env,await create(env,'screen_guided'));
 let s=await(await check(env,p.state,p.cookie)).json();
 let r=await action(env,s,{action:'review',criterion_ids:s.steps[0].criteria.map(c=>c.criterion_id),review_note:'Student explicitly confirms the model was created and saved.'});s=await r.json();
 env.LAB_ANALYSIS_FETCH=async(url,options)=>{const ctx=JSON.parse(JSON.parse(options.body).contents[0].parts[0].text);return Response.json({candidates:[{finishReason:'STOP',content:{parts:[{text:JSON.stringify({summary:'Controlled visible source-block fixture.',criteria:ctx.checkpoint.completion_criteria.map(c=>({criterion_id:c.id,status:'match',evidence:'Controlled fixture; screen-inferred only.'})),uncertainties:[]})}]}}]});};
 let cookie=p.cookie;
 for(let sequence=2;sequence<=3;sequence++){
  t.mock.timers.tick(11000);const m={...meta,sequence,captured_elapsed_ms:sequence*11000};
  r=await worker.fetch(request(`/screen-sessions/${p.id}/frame`,'POST',image,cookie,{'Content-Type':'image/jpeg','X-Capture-Frame':JSON.stringify(m)}),env);assert.equal(r.status,200);cookie=cookieOf(r);
  r=await check(env,s,cookie,m);assert.equal(r.status,200);s=await r.json();
  assert.equal(s.queue.current_checkpoint_id,sequence===2?'CP-DSB-02':'CP-DSB-03');
 }
 assert.equal(s.steps[1].completion_basis,'screen_inferred_or_student_report');assert.equal(s.steps[1].assessment_status,'unassessed');
 assert.ok(s.evidence.some(e=>e.review_status==='unreviewed'));assert.ok(s.learner_state.concepts.every(c=>c.understanding==='unknown'));
 const events=(await worker.fetch(request(`/lab-sessions/${s.lab_session_id}/events`),env)).json();assert.equal((await events).at(-1).checkpoint_id,'CP-DSB-02');
 assert.equal((await worker.fetch(request(`/lab-sessions/${s.lab_session_id}/image`),env)).status,404);
});
test('journal and responses cross previous caps, retain full paginated history, and keep recent model context bounded',async t=>{
 const env=setup(t);let s=await create(env);
 for(let i=0;i<510;i++){const r=await action(env,s,{action:'note',text:'Controlled response '+i});assert.equal(r.status,200);s=await r.json();}
 assert.equal(s.revision,511);assert.equal(s.runtime.notes.length,100);
 const events=[];let after=0;
 while(true){const page=await(await worker.fetch(request(`/lab-sessions/${s.lab_session_id}/events?after=${after}&limit=100`),env)).json();events.push(...page);if(page.length<100)break;after=page.at(-1).event_sequence;}
 assert.equal(events.length,511);assert.equal(events[1].payload.response.text,'Controlled response 0');assert.equal(events.at(-1).payload.response.text,'Controlled response 509');
 assert.equal(new Set(events.map(e=>e.event_id)).size,511);
});
test('provider pool cooldown persists across Worker environments while capture can continue',async t=>{
 const env=setup(t),p=await prepare(env,await create(env));let calls=0;env.LAB_ANALYSIS_FETCH=async()=>{calls++;return new Response('',{status:429,headers:{'Retry-After':'60'}});};
 let s=await(await check(env,p.state,p.cookie)).json();assert.equal(s.runtime.analysis_status,'waiting_for_provider');assert.equal(s.runtime.capture_active,true);
 const other=await prepare(env,await create(env));const cold={...env};s=await(await check(cold,other.state,other.cookie)).json();assert.equal(calls,1);assert.equal(s.runtime.analysis_status,'waiting_for_provider');
 const r=await check(env,s,other.cookie);assert.equal(r.status,200);assert.equal(calls,1);
});
test('receiver guidance starts with creating the third source and only advances instruction actions on supported evidence',async t=>{
 const env=setup(t),p=await prepare(env,await create(env,'screen_guided'));
 const row=await env.DB.prepare('SELECT state_json FROM lab_sessions WHERE id=?').bind(p.state.lab_session_id).first();let raw=JSON.parse(row.state_json);
 raw.queue.current_checkpoint_id='CP-DSB-05';raw.queue.done_checkpoint_ids=['CP-DSB-01','CP-DSB-02','CP-DSB-03','CP-DSB-04'];
 raw.queue.upcoming_checkpoint_ids=raw.queue.upcoming_checkpoint_ids.filter(id=>id>'CP-DSB-05');
 raw.steps[4].status='in_progress';raw.steps[4].current_visit_id=crypto.randomUUID();
 await env.DB.prepare('UPDATE lab_sessions SET state_json=? WHERE id=?').bind(JSON.stringify(raw),raw.lab_session_id).run();
 let s=await(await worker.fetch(request(`/lab-sessions/${raw.lab_session_id}`),env)).json();assert.equal(s.guidance.current_action.id,'CP-DSB-05/local-create');assert.equal(s.guidance.next_action.id,'CP-DSB-05/local-settings');assert.match(s.guidance.already_tracked,/transmitter Product/);
 env.LAB_ANALYSIS_FETCH=async(url,options)=>{const ctx=JSON.parse(JSON.parse(options.body).contents[0].parts[0].text);return Response.json({candidates:[{finishReason:'STOP',content:{parts:[{text:JSON.stringify({summary:'The Local carrier block is visible.',criteria:ctx.checkpoint.completion_criteria.map(c=>({criterion_id:c.id,status:'unknown',evidence:''})),action_findings:ctx.procedure.map(a=>({action_id:a.id,status:a.id.endsWith('/local-create')?'match':'unknown',evidence:a.id.endsWith('/local-create')?'Named Local carrier is visible.':''})),uncertainties:[]})}]}}]});};
 let r=await check(env,s,p.cookie);s=await r.json();assert.equal(s.guidance.current_action.id,'CP-DSB-05/local-create');
 t.mock.timers.tick(11000);const m={...meta,sequence:2,captured_elapsed_ms:11020};r=await worker.fetch(request(`/screen-sessions/${p.id}/frame`,'POST',image,p.cookie,{'Content-Type':'image/jpeg','X-Capture-Frame':JSON.stringify(m)}),env);const cookie=cookieOf(r);
 r=await check(env,s,cookie,m);s=await r.json();assert.equal(s.guidance.current_action.id,'CP-DSB-05/local-settings');assert.equal(s.guidance.next_action.id,'CP-DSB-05/receiver-create');assert.equal(s.queue.current_checkpoint_id,'CP-DSB-05');assert.equal(s.steps[4].criteria[0].state,'unknown');
 assert.equal(s.runtime.candidate.prompt_version,'dsb-step-observer/v3');
});
test('historical receiver actions survive a long view gap and resume without creating duplicate blocks',async t=>{
 const env=setup(t),p=await prepare(env,await create(env,'screen_guided'));
 const row=await env.DB.prepare('SELECT state_json FROM lab_sessions WHERE id=?').bind(p.state.lab_session_id).first();let raw=JSON.parse(row.state_json);
 raw.queue.current_checkpoint_id='CP-DSB-05';raw.steps[4].status='in_progress';raw.steps[4].current_visit_id=crypto.randomUUID();
 const scope={visit_id:raw.steps[4].current_visit_id,workspace_id:raw.workspace.id,parameter_revision:0,condition:'baseline',capture_epoch:1};
 raw.procedure_history=Object.fromEntries(['CP-DSB-05/local-create','CP-DSB-05/local-settings'].map(id=>[id,{scope,count:2,last_seen_ms:Date.now()-200000,frame_ids:['fixture-old-1','fixture-old-2'],last_evidence:'Prior controlled Local carrier observation.'}]));
 await env.DB.prepare('UPDATE lab_sessions SET state_json=? WHERE id=?').bind(JSON.stringify(raw),raw.lab_session_id).run();
 let s=await(await worker.fetch(request(`/lab-sessions/${raw.lab_session_id}`),env)).json();assert.equal(s.guidance.current_action.id,'CP-DSB-05/receiver-create');assert.equal(s.steps[4].criteria[0].state,'unknown');
 s=await(await action(env,s,{action:'pause'})).json();s=await(await action(env,s,{action:'resume'})).json();assert.equal(s.guidance.current_action.id,'CP-DSB-05/receiver-create');
 s=await(await action(env,s,{action:'parameters_changed'})).json();assert.equal(s.guidance.current_action.id,'CP-DSB-05/local-create');
});
test('owned MCP reset returns to step one with a new visit and full journal preserved',async t=>{
 const env=setup(t),p=await prepare(env,await create(env));let s=await(await check(env,p.state,p.cookie)).json();
 s=await(await action(env,s,{action:'review',criterion_ids:s.steps[0].criteria.map(c=>c.criterion_id),review_note:'Controlled explicit model confirmation.'})).json();assert.equal(s.queue.current_checkpoint_id,'CP-DSB-02');
 const oldVisit=s.steps[0].visits[0],previousEventCount=s.history.event_count;
 const rpc={jsonrpc:'2.0',id:17,method:'tools/call',params:{name:'reset_lab_session',arguments:{lab_session_id:s.lab_session_id,revision:s.revision}}};
 const foreign=await worker.fetch(request('/mcp','POST',rpc,null,{'oai-authenticated-user-id':'foreign-owner'}),env);assert.equal(foreign.status,404);
 const r=await worker.fetch(request('/mcp','POST',rpc),env);assert.equal(r.status,200);const value=JSON.parse((await r.json()).result.content[0].text);
 assert.equal(value.queue.current_checkpoint_id,'CP-DSB-01');assert.deepEqual(value.queue.done_checkpoint_ids,[]);assert.equal(value.queue.upcoming_checkpoint_ids.length,11);assert.notEqual(value.steps[0].current_visit_id,oldVisit);assert.ok(value.steps[0].visits.includes(oldVisit));assert.ok(value.evidence.length>0);assert.equal(value.runtime.candidate,null);assert.equal(value.observation.observation_id,null);assert.equal(value.history.event_count,previousEventCount+1);
 assert.equal((await worker.fetch(request('/mcp','POST',rpc),env)).status,409,'Replaying an old revision cannot reset again');
});
test('lab model override uses compatible generation config and actual observation provenance',async t=>{
 const env=setup(t);env.GEMINI_LAB_MODEL='gemini-3.8-flash';const normal=env.LAB_ANALYSIS_FETCH;let body,url;
 env.LAB_ANALYSIS_FETCH=async(u,opt)=>{url=u;body=JSON.parse(opt.body);return normal(u,opt);};
 const p=await prepare(env,await create(env));const s=await (await check(env,p.state,p.cookie)).json();
 assert.ok(url.includes('/gemini-3.8-flash:generateContent'));assert.equal(body.generationConfig.thinkingConfig.thinkingLevel,'low');assert.ok(!('temperature' in body.generationConfig));assert.equal(s.runtime.candidate.model,'gemini-3.8-flash');
});
test('provider timing is recorded outside unchanged canonical model findings',async t=>{
 const env=setup(t),normal=env.LAB_ANALYSIS_FETCH;
 env.LAB_ANALYSIS_FETCH=async(...args)=>{const response=await normal(...args),value=await response.json();value.usageMetadata={candidatesTokenCount:101};return Response.json(value);};
 const p=await prepare(env,await create(env));const s=await (await check(env,p.state,p.cookie)).json();
 assert.equal(s.runtime.last_analysis_timing.output_tokens,101);assert.equal(s.runtime.last_analysis_timing.wire_format,'lab-observer-json/v3');assert.equal(s.runtime.candidate.prompt_version,'dsb-step-observer/v3');
});
test('three-second admission permits the second reading sooner, still refuses one-frame completion and duplicate concurrent checks',async t=>{
 const env=setup(t);const p=await prepare(env,await create(env));let s=await (await check(env,p.state,p.cookie)).json();
 assert.equal(s.queue.current_checkpoint_id,'CP-DSB-01');t.mock.timers.tick(2000);
 let r=await check(env,s,p.cookie);assert.equal(r.status,429);assert.equal((await r.json()).retry_after_ms,1000);
 t.mock.timers.tick(1000);r=await check(env,s,p.cookie);assert.equal(r.status,200);
 let release,admit;const gate=new Promise(resolve=>release=resolve),started=new Promise(resolve=>admit=resolve),normal=env.LAB_ANALYSIS_FETCH;
 env.LAB_ANALYSIS_FETCH=async(...args)=>{admit();await gate;return normal(...args);};t.mock.timers.tick(3000);
 const pending=check(env,s,p.cookie);await started;const competing=await check(env,s,p.cookie);assert.equal(competing.status,429);assert.equal((await competing.json()).code,'lab_check_in_flight');release();assert.equal((await pending).status,200);
});
