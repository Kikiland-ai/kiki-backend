// L2 local lab: the real reader Worker on http://localhost:8870 with a fixture
// provider, plus the controlled target page on http://localhost:8871.
// Any non-localhost fetch throws, so no live provider can be reached.
// Run from prototypes/json_stream_site after `node scripts/build.mjs`:
//   node ../floating_guidance/scripts/serve-local-lab.mjs
import http from 'node:http';
import {readFile} from 'node:fs/promises';
import {randomBytes} from 'node:crypto';
import worker from '../../json_stream_site/dist/server/index.js';
import {localDB} from '../../json_stream_site/scripts/local-db.mjs';

const realFetch=globalThis.fetch;let blockedNetwork=0;
globalThis.fetch=async(url,...rest)=>{const target=new URL(String(url?.url||url));
 if(!['localhost','127.0.0.1'].includes(target.hostname)){blockedNetwork++;throw Error('network_blocked_in_local_lab');}return realFetch(url,...rest);};
const fixture={mode:'unknown',model_calls:0,images:[],max_loop_lag_ms:0};
// Event-loop lag probe: a blocked server shows up here, not as a client timeout.
let tick=performance.now();setInterval(()=>{const lag=performance.now()-tick-250;tick=performance.now();if(lag>fixture.max_loop_lag_ms)fixture.max_loop_lag_ms=Math.round(lag);if(lag>1000)console.log(JSON.stringify({event:'loop_lag',ms:Math.round(lag)}));},250).unref();
function imageOf(body){for(const part of body.contents?.[0]?.parts||[]){const data=part.inlineData?.data||part.inline_data?.data;if(data)return data;}return null;}
function decide(body){
 const context=JSON.parse(body.contents[0].parts[0].text),status=fixture.mode==='match'?'match':'unknown';
 return {criteria:context.checkpoint.completion_criteria.map(c=>({criterion_id:c.id,status,evidence:`Local fixture reading (${status}); not real vision.`})),
  action_findings:context.procedure.map(a=>({action_id:a.id,status:a.kind==='visible'?status:'unknown',evidence:`Local fixture action (${status}).`})),uncertainties:[]};
}
async function provider(url,options){
 fixture.model_calls++;const body=JSON.parse(options.body),image=imageOf(body);
 if(image){fixture.images.push(image);if(fixture.images.length>6)fixture.images.shift();}
 if(fixture.mode==='429')return new Response('',{status:429,headers:{'Retry-After':'60'}});
 await new Promise(r=>setTimeout(r,600));
 return new Response('data: '+JSON.stringify({candidates:[{content:{parts:[{text:JSON.stringify(decide(body))}]},finishReason:'STOP'}],usageMetadata:{promptTokenCount:10,candidatesTokenCount:10,totalTokenCount:20}})+'\n\n',{headers:{'Content-Type':'text/event-stream'}});
}
const env={CAPTURE_RECEIPT_KEY:randomBytes(32).toString('hex'),DB:localDB(),GEMINI_API_KEY:'local-fixture-only',LAB_STREAM_FETCH:provider,
 LAB_ANALYSIS_FETCH:async(url,options)=>{const r=await provider(url,options);if(!r.ok)return r;const text=(await r.text()).slice(6);return Response.json(JSON.parse(text));}};
const read=req=>new Promise(resolve=>{const chunks=[];req.on('data',c=>chunks.push(c));req.on('end',()=>resolve(Buffer.concat(chunks)));});
http.createServer(async(req,res)=>{
 try{
  if(req.url.startsWith('/__fixture/')){
   const sent=(await read(req)).toString();
   if(req.method==='POST'&&req.url==='/__fixture/mode')fixture.mode=JSON.parse(sent||'{}').mode||fixture.mode;
   const image=/^\/__fixture\/image\?index=(-?\d+)$/.exec(req.url);
   // One raw model-bound JPEG per request, with an explicit length.
   const payload=image?Buffer.from(fixture.images.at(Number(image[1]))||'','base64'):Buffer.from(JSON.stringify({mode:fixture.mode,model_calls:fixture.model_calls,
    blocked_network_requests:blockedNetwork,image_count:fixture.images.length,max_loop_lag_ms:fixture.max_loop_lag_ms}));
   res.writeHead(image&&!payload.length?404:200,{'Content-Type':image?'image/jpeg':'application/json','Content-Length':payload.length,Connection:'close'});res.end(payload);return;
  }
  const body=await read(req),headers=new Headers(req.headers);headers.set('oai-authenticated-user-id','local-floating-lab');
  const result=await worker.fetch(new Request('http://localhost:8870'+req.url,{method:req.method,headers,...(['GET','HEAD'].includes(req.method)?{}:{body})}),env,{waitUntil(){}});
  res.writeHead(result.status,Object.fromEntries(result.headers));
  if(result.body){const reader=result.body.getReader();while(true){const {value,done}=await reader.read();if(done)break;res.write(value);}}
  res.end();
 }catch(error){res.writeHead(500);res.end(String(error));}
}).listen(8870,'127.0.0.1',()=>console.log('reader http://localhost:8870'));
const harness=new URL('../harness/',import.meta.url);
http.createServer(async(req,res)=>{
 const name=req.url==='/'||req.url.startsWith('/?')?'target.html':req.url.slice(1).split('?')[0];
 if(!['target.html','page.js'].includes(name)){res.writeHead(404);res.end();return;}
 res.writeHead(200,{'Content-Type':name.endsWith('.js')?'application/javascript':'text/html; charset=utf-8'});res.end(await readFile(new URL(name,harness)));
}).listen(8871,'127.0.0.1',()=>console.log('target http://localhost:8871 ready'));
