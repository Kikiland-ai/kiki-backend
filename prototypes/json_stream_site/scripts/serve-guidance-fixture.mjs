// Local controlled provider only. Browser/Worker/extension code is real; vision
// and Chrome message dispatch are fixtures. This never calls a live provider.
import http from 'node:http';
import https from 'node:https';
import {readFileSync} from 'node:fs';
import worker from '../dist/server/index.js';
import {fixtureEnv,fixtureOrigin,seedCheckpoint} from './guidance-fixture.mjs';
const env=fixtureEnv();env.fixtureDelay=Number(process.env.GUIDANCE_FIXTURE_DELAY_MS||4200);
const records=[];const prior=console.info;console.info=(value)=>{try{const r=JSON.parse(value);if(r.schema)records.push(r);}catch{}prior(value);};
const handler=async(req,res)=>{try{
 if(req.url==='/__fixture/evidence'){res.setHeader('Content-Type','application/json');res.end(JSON.stringify({records,acks:(await env.DB.prepare('SELECT timing_json FROM guidance_acks').all()).results.map(r=>JSON.parse(r.timing_json))}));return;}
 const data=[];for await(const chunk of req)data.push(chunk);const bytes=Buffer.concat(data);
 const origin=req.headers.host==='localhost'?'https://localhost':fixtureOrigin;
 const request=new Request(origin+req.url,{method:req.method,headers:{...req.headers,'oai-authenticated-user-id':'guidance-offline-owner'},...(bytes.length?{body:bytes}:{})});
 let response=await worker.fetch(request,env);
 if(req.url==='/lab-sessions'&&req.method==='POST'&&response.ok){const state=await seedCheckpoint(env,await response.json());response=Response.json(state,{headers:response.headers});}
 res.writeHead(response.status,Object.fromEntries(response.headers));const reader=response.body.getReader();res.on('close',()=>reader.cancel().catch(()=>{}));while(true){const {value,done}=await reader.read();if(done)break;res.write(Buffer.from(value));}res.end();
}catch(err){console.error(err);if(!res.headersSent)res.writeHead(500);res.end('Controlled fixture failure');}};
const server=http.createServer(handler);
if(process.argv.includes('--tls'))https.createServer({key:readFileSync('../../work/guidance-integration/tls/key.pem'),cert:readFileSync('../../work/guidance-integration/tls/cert.pem')},handler).listen(443,'127.0.0.1');
server.listen(8872,'127.0.0.1',()=>console.log('Local integrated guidance fixture http://127.0.0.1:8872'));
