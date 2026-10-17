// Local controlled provider only. Browser/Worker/extension code is real; vision
// and Chrome message dispatch are fixtures. This never calls a live provider.
import http from 'node:http';
import https from 'node:https';
import {readFileSync} from 'node:fs';
import worker from '../dist/server/index.js';
import {fixtureEnv,fixtureOrigin,seedCheckpoint} from './guidance-fixture.mjs';
const env=fixtureEnv();env.fixtureDelay=Number(process.env.GUIDANCE_FIXTURE_DELAY_MS||4200);
const live=process.env.GUIDANCE_FIXTURE_LIVE_MODEL==='1',offlineFetch=env.LAB_STREAM_FETCH;let liveRequests=0;
if(live){if(!process.env.GEMINI_API_KEY)throw Error('Configured runtime Gemini key is required.');env.GEMINI_API_KEY=process.env.GEMINI_API_KEY;env.GUIDANCE_SAMPLE_KIND='live_provider';env.GUIDANCE_CONFIGURATION_ID='controlled-live-mark-generation-v1';env.LAB_STREAM_FETCH=async(...args)=>{if(liveRequests>=1)throw Error('live_probe_budget_exhausted');liveRequests++;return fetch(...args);};}
const records=[];const prior=console.info;console.info=(value)=>{try{const r=JSON.parse(value);if(r.schema)records.push(r);}catch{}prior(value);};
const handler=async(req,res)=>{try{
 if(req.url==='/__fixture/evidence'){res.setHeader('Content-Type','application/json');res.end(JSON.stringify({records,live_model_requests:liveRequests,acks:(await env.DB.prepare('SELECT timing_json FROM guidance_acks').all()).results.map(r=>JSON.parse(r.timing_json))}));return;}
 const data=[];for await(const chunk of req)data.push(chunk);const bytes=Buffer.concat(data);
 const origin=req.headers.host==='localhost'?'https://localhost':fixtureOrigin;
 const request=new Request(origin+req.url,{method:req.method,headers:{...req.headers,'oai-authenticated-user-id':'guidance-offline-owner'},...(bytes.length?{body:bytes}:{})});
 const delay=Number(process.env.GUIDANCE_FIXTURE_CLOCK_DB_DELAY_MS||0);let selectedEnv=env;
 if(delay&&req.url.endsWith('/guidance/clock'))selectedEnv={...env,DB:{prepare(sql){const s=env.DB.prepare(sql);return {...s,bind(...values){const b=s.bind(...values);return {...b,async first(){await new Promise(r=>setTimeout(r,delay));return b.first();}};}};}}};
 // Only the unbound analysis uses the fixture model. Delivery ACKs are for
 // the real-model drawing request and must retain live_provider provenance.
 if(live&&req.url.endsWith('/check-stream')&&!request.headers.has('x-guidance-contract'))selectedEnv={...selectedEnv,LAB_STREAM_FETCH:offlineFetch,GUIDANCE_SAMPLE_KIND:'offline_replay'};
 let response=await worker.fetch(request,selectedEnv);
 if(process.env.GUIDANCE_FIXTURE_LEGACY_CLOCK==='1'&&req.url.endsWith('/guidance/clock')&&response.ok){const body=await response.json();delete body.server_received_ms;response=Response.json(body,{headers:response.headers});}
 if(req.url==='/lab-sessions'&&req.method==='POST'&&response.ok){const state=await seedCheckpoint(env,await response.json(),live?'CP-DSB-06':'CP-DSB-03');if(live){state.procedure_history=Object.fromEntries(['filter-create','filter-settings','gain-create'].map(a=>['CP-DSB-06/'+a,{count:2,scope:{visit_id:state.steps.find(s=>s.checkpoint_id==='CP-DSB-06').current_visit_id,workspace_id:state.workspace.id,capture_epoch:state.workspace.capture_epoch,parameter_revision:state.workspace.parameter_revision,condition:state.workspace.condition},last_seen_ms:Date.now(),last_evidence:'Explicit controlled setup precondition.'}]));await env.DB.prepare('UPDATE lab_sessions SET state_json=? WHERE id=?').bind(JSON.stringify(state),state.lab_session_id).run();}response=Response.json(state,{headers:response.headers});}
 res.writeHead(response.status,Object.fromEntries(response.headers));const reader=response.body.getReader();res.on('close',()=>reader.cancel().catch(()=>{}));while(true){const {value,done}=await reader.read();if(done)break;res.write(Buffer.from(value));}res.end();
}catch(err){console.error(err);if(!res.headersSent)res.writeHead(500);res.end('Controlled fixture failure');}};
const server=http.createServer(handler);
if(process.argv.includes('--tls'))https.createServer({key:readFileSync('../../work/guidance-integration/tls/key.pem'),cert:readFileSync('../../work/guidance-integration/tls/cert.pem')},handler).listen(443,'127.0.0.1');
server.listen(8872,'127.0.0.1',()=>console.log('Local integrated guidance fixture http://127.0.0.1:8872'));
