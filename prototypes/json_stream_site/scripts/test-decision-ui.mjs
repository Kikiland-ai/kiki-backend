// DOM stubs exercise the actual UI scheduler; this is not browser capture QA.
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFile} from 'node:fs/promises';
import {randomBytes} from 'node:crypto';
import worker from '../dist/server/index.js';
import {localDB} from './local-db.mjs';
import {verificationCadence,sameScreenContent} from '../assets/lab-cadence.js';
import {startAnalysisStream} from '../assets/json-stream-client.js';

test('actual guide UI releases busy at commit and ignores an older auxiliary snapshot',async t=>{
 t.mock.timers.enable({apis:['Date'],now:Date.UTC(2026,9,15)});
 const env={DB:localDB(),GEMINI_API_KEY:'fixture',CAPTURE_RECEIPT_KEY:randomBytes(32).toString('hex')};t.after(()=>env.DB.close());
 const owner='ui-test-owner',origin='https://receiver.test';let cookie=null,checkCalls=0;
 const request=(path,options={})=>new Request(origin+path,{...options,headers:{'oai-authenticated-user-id':owner,Origin:origin,...(cookie?{Cookie:cookie}:{}),...options.headers}});
 const fetcher=async(path,options={})=>{if(path.endsWith('/check-stream'))checkCalls++;return worker.fetch(request(path,options),env);};
 const post=(path,body)=>fetcher(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 let state=await(await post('/lab-sessions',{operator_trial:true,model_name:'ui_fixture',progression_mode:'screen_guided'})).json();
 let response=await post('/screen-sessions',{});const capture=(await response.json()).session_id;cookie=response.headers.get('set-cookie').split(';')[0];
 const image=Buffer.from(await readFile('scripts/fixtures/jpeg.txt','utf8'),'base64');
 const meta={type:'frame',capture_epoch:1,view_revision:1,sequence:1,captured_elapsed_ms:20,width:96,height:54,source_width:96,source_height:54,byte_count:image.length,mime_type:'image/jpeg'};
 async function frame(m){const r=await fetcher(`/screen-sessions/${capture}/frame`,{method:'POST',headers:{'Content-Type':'image/jpeg','X-Capture-Frame':JSON.stringify(m)},body:image});cookie=r.headers.get('set-cookie').split(';')[0];return JSON.parse(Buffer.from(r.headers.get('X-Capture-Observation'),'base64').toString()).observation.latest_frame;}
 const firstFrame=await frame(meta);state=await(await post(`/lab-sessions/${state.lab_session_id}/attach`,{revision:state.revision,capture_session_id:capture})).json();
 env.LAB_STREAM_FETCH=async(url,options)=>{const ctx=JSON.parse(JSON.parse(options.body).contents[0].parts[0].text);const value={criteria:ctx.checkpoint.completion_criteria.map(c=>({criterion_id:c.id,status:'match',evidence:'Controlled fixture.'})),action_findings:ctx.procedure.map(a=>({action_id:a.id,status:'match',evidence:'Controlled fixture.'})),uncertainties:[]};return new Response('data: '+JSON.stringify({candidates:[{content:{parts:[{text:JSON.stringify(value)}]},finishReason:'STOP'}]})+'\n\n',{headers:{'Content-Type':'text/event-stream'}});};
 let release;const gate=new Promise(resolve=>release=resolve);let tails=0;env.LAB_STREAM_AUXILIARY=async()=>{if(++tails===1)await gate;};
 const nodes=new Map();const element=()=>({hidden:false,textContent:'',value:'',disabled:false,checked:false,attrs:{},addEventListener(){},replaceChildren(){},setAttribute(k,v){this.attrs[k]=v;},getAttribute(k){return this.attrs[k];},removeAttribute(k){delete this.attrs[k];},querySelector(){return element();}});
 const document={getElementById(id){if(!nodes.has(id))nodes.set(id,element());return nodes.get(id);},createElement:element};
 const context={document,window:{addEventListener(){}},localStorage:{getItem:()=>state.lab_session_id,setItem(){},removeItem(){}},fetch:fetcher,verificationCadence,sameScreenContent,startAnalysisStream,performance,AbortController,AbortSignal,Date,Event,console,Blob,URL,navigator:{},setTimeout(){}};
 vm.createContext(context);const source=(await readFile('assets/lab.js','utf8')).replace(/^import .*;\n/gm,'');vm.runInContext(source,context);
 const until=async predicate=>{const deadline=performance.now()+2000;while(performance.now()<deadline){if(predicate())return;await new Promise(resolve=>setTimeout(resolve,1));}assert.fail('Controlled UI condition did not settle: '+JSON.stringify({checks:checkCalls,tails,budget:document.getElementById('lab-budget').textContent,status:document.getElementById('lab-status').textContent}));};
 await until(()=>document.getElementById('lab-budget').textContent.includes('0 screen reads'));
 context.window.KikiLab.onFrame(new Blob([image]),meta,firstFrame);
 await until(()=>document.getElementById('lab-budget').textContent.includes('1 screen reads'));
 assert.equal(tails,1);assert.equal(checkCalls,1);
 t.mock.timers.tick(3100);const secondMeta={...meta,sequence:2,captured_elapsed_ms:3120},secondFrame=await frame(secondMeta);
 context.window.KikiLab.onFrame(new Blob([image]),secondMeta,secondFrame);
 await until(()=>document.getElementById('lab-budget').textContent.includes('2 screen reads'));
 assert.equal(checkCalls,2,'A blocked auxiliary tail must not keep the verification slot busy');
 release();await new Promise(resolve=>setImmediate(resolve));assert.ok(document.getElementById('lab-budget').textContent.includes('2 screen reads'),'Late old snapshot cannot restore the first state');
});
