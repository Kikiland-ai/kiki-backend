// Real extension scripts under deterministic Chrome/window boundaries; no provider.
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFile} from 'node:fs/promises';
import {webcrypto} from 'node:crypto';
import {createRequire} from 'node:module';
import {resolve} from 'node:path';

const background=await readFile(new URL('../extension/background.js',import.meta.url),'utf8');
const content=await readFile(new URL('../extension/content.js',import.meta.url),'utf8');
const bridge=await readFile(new URL('../extension/bridge.js',import.meta.url),'utf8');
const CFG={readers:['http://127.0.0.1:5174'],targets:['https://matlab.mathworks.com'],dev:true,version:'test'};
const copy=v=>structuredClone(v),tick=()=>new Promise(resolve=>setImmediate(resolve));
const sender=(tabId=1,documentId='document-a')=>({id:'extension-fixture',frameId:0,documentId,tab:{id:tabId},url:CFG.readers[0]+'/labs/test'});

function worker(storage={},options={}){
 const messages=[],calls=[],listeners={},injections=[];let installed=!options.targetAbsent;
 const chrome={runtime:{id:'extension-fixture',getURL:path=>'chrome-extension://extension-fixture/'+path,
   onMessage:{addListener:fn=>listeners.message=fn}},
  storage:{session:{get:async key=>copy({[key]:storage[key]}),set:async value=>Object.assign(storage,copy(value))}},
  tabs:{get:async id=>({id,url:CFG.targets[0]+'/'}),update:async(id,props)=>({id,windowId:1,...props}),
   sendMessage:async(tabId,message)=>{messages.push({tabId,message:copy(message)});if(message.type==='fg_bound'&&options.boundDeliveryFails)throw new Error('Target unloaded');if(message.type==='fg_probe'&&options.neverReady)return new Promise(()=>{});if(message.to==='target'&&!installed)throw new Error('Receiving end does not exist');return {ok:true,ready:installed,result:'displayed'};},
   onRemoved:{addListener:fn=>listeners.removed=fn},onUpdated:{addListener:fn=>listeners.updated=fn}},
  windows:{update:async()=>({})},
  scripting:{executeScript:async spec=>{injections.push(copy(spec));if(spec.files){if(options.failInjection)throw new Error('Injection denied');installed=true;}return [{result:true}];}}};
 const context=vm.createContext({chrome,KIKI_FG_CONFIG:CFG,URL,setTimeout,clearTimeout,crypto:webcrypto,importScripts:()=>{},console:{info:()=>{}}});
 vm.runInContext(background,context);
 const send=(message,from=sender())=>new Promise(resolve=>listeners.message(message,from,result=>{calls.push({message:copy(message),result:copy(result)});resolve(copy(result));}));
 return {send,messages,calls,storage,context,injections,bind:()=>context.kikiTest.bind(99)};
}

test('duplicate hello for one reader stream preserves the acknowledged generation',async()=>{
 const w=worker();await w.bind();
 const first=await w.send({type:'reader_hello',stream_id:'stream-aaaa-1111'});
 const duplicate=await w.send({type:'reader_hello',stream_id:'stream-aaaa-1111'});
 assert.equal(duplicate.generation,first.generation);
 const sent=await w.send({type:'reader_snapshot',message:{stream_id:'stream-aaaa-1111',generation:first.generation}});
 assert.equal(sent.ok,true,'an in-flight snapshot must survive a duplicate handshake');
});

test('replacing a reader document or stream advances the generation and rejects stale snapshots',async()=>{
 const w=worker();await w.bind();
 const first=await w.send({type:'reader_hello',stream_id:'stream-aaaa-1111'});
 const next=await w.send({type:'reader_hello',stream_id:'stream-bbbb-2222'});
 assert.ok(next.generation>first.generation);
 const stale=await w.send({type:'reader_snapshot',message:{stream_id:'stream-aaaa-1111',generation:first.generation}});
 assert.equal(stale.ok,false);
 const replacement=await w.send({type:'reader_hello',stream_id:'stream-bbbb-2222'},sender(1,'document-b'));
 assert.ok(replacement.generation>next.generation);
 const oldDocument=await w.send({type:'reader_snapshot',message:{stream_id:'stream-bbbb-2222',generation:replacement.generation}},sender());
 assert.equal(oldDocument.ok,false,'a departed document must never act for its replacement');
});

test('late identity-bearing bye and command result cannot act for a new same-tab reader',async()=>{
 const w=worker();await w.bind();
 const old=await w.send({type:'reader_hello',stream_id:'stream-aaaa-1111'});
 const current=await w.send({type:'reader_hello',stream_id:'stream-bbbb-2222'});
 for(const type of ['reader_command_result','reader_bye']){
  const result=await w.send({type,stream_id:'stream-aaaa-1111',generation:old.generation,ok:true,request_id:'old-command'});
  assert.equal(result.ok,false);
 }
 const snapshot=await w.send({type:'reader_snapshot',message:{stream_id:'stream-bbbb-2222',generation:current.generation}});
 assert.equal(snapshot.ok,true);
});

test('other tabs are superseded and worker suspension retains one stream generation',async()=>{
 const storage={},w=worker(storage);await w.bind();
 await w.send({type:'reader_hello',stream_id:'stream-aaaa-1111'});
 const second=await w.send({type:'reader_hello',stream_id:'stream-bbbb-2222'},sender(2,'document-b'));
 assert.ok(w.messages.some(v=>v.tabId===1&&v.message.type==='fg_superseded'));
 assert.equal((await w.send({type:'reader_bye'})).ok,false);
 const resumed=worker(storage);
 const again=await resumed.send({type:'reader_hello',stream_id:'stream-bbbb-2222'},sender(2,'document-b'));
 assert.equal(again.generation,second.generation);
});

test('sender and stream validation still reject foreign origin, iframe and malformed hello',async()=>{
 const w=worker();
 for(const from of [{...sender(),url:'https://foreign.invalid/'},{...sender(),frameId:2},{...sender(),id:'foreign'}]){
  assert.equal((await w.send({type:'reader_hello',stream_id:'stream-aaaa-1111'},from)).ok,false);
 }
 assert.equal((await w.send({type:'reader_hello',stream_id:'bad'})).error,'bad_stream');
});

function pageBridge(){
 const pending=[],posted=[],listeners=new Map();
 const window={postMessage:value=>posted.push(copy(value)),addEventListener:(name,fn)=>listeners.set(name,fn)};
 window.top=window;
 const chrome={runtime:{id:'extension-fixture',sendMessage:message=>new Promise(resolve=>pending.push({message:copy(message),resolve})),
  onMessage:{addListener:()=>{}}}};
 const context=vm.createContext({window,location:{origin:CFG.readers[0]},KIKI_FG_CONFIG:CFG,chrome,addEventListener:()=>{}});
 vm.runInContext(bridge,context);
 const send=message=>listeners.get('message')({source:window,origin:CFG.readers[0],data:{channel:'kiki-floating-guidance',direction:'page',...message}});
 return {send,pending,posted};
}

test('late hello response cannot resolve a replacement publisher using the same bridge ID',async()=>{
 const p=pageBridge();
 p.send({type:'reader_hello',stream_id:'stream-aaaa-1111',bridge_id:1});
 p.send({type:'reader_hello',stream_id:'stream-bbbb-2222',bridge_id:1});
 p.pending[0].resolve({ok:true,generation:1});await tick();
 assert.equal(p.posted.filter(m=>m.type==='response').length,0,'old response must not escape into new publisher');
 p.pending[1].resolve({ok:true,generation:2});await tick();
 const responses=p.posted.filter(m=>m.type==='response');
 assert.equal(responses.length,1);assert.equal(responses[0].result.generation,2);
});

test('old in-flight snapshot responses are fenced after a new publisher hello',async()=>{
 const p=pageBridge();
 p.send({type:'reader_hello',stream_id:'stream-aaaa-1111',bridge_id:1});
 p.pending[0].resolve({ok:true,generation:1});await tick();
 p.send({type:'reader_snapshot',message:{stream_id:'stream-aaaa-1111',generation:1},bridge_id:2});
 p.send({type:'reader_hello',stream_id:'stream-bbbb-2222',bridge_id:2});
 p.pending[1].resolve({ok:false,error:'stale_stream_or_generation'});await tick();
 assert.equal(p.posted.filter(m=>m.type==='response'&&m.bridge_id===2).length,0);
 p.pending[2].resolve({ok:true,generation:2});await tick();
 assert.equal(p.posted.filter(m=>m.type==='response'&&m.bridge_id===2)[0].result.generation,2);
});

test('actual web publisher survives StrictMode-style mount replacement and overlapping rechecks',
 {skip:!process.env.KIKI_WEB_CHECKOUT},async()=>{
 const root=resolve(process.env.KIKI_WEB_CHECKOUT),require=createRequire(import.meta.url);
 const ts=require(resolve(root,'apps/web/node_modules/typescript/lib/typescript.js'));
 const w=worker();await w.bind();
 const listeners=new Map(),timers=new Map();let timer=0;
 const window={addEventListener:(name,fn)=>{if(!listeners.has(name))listeners.set(name,new Set());listeners.get(name).add(fn);},
  removeEventListener:(name,fn)=>listeners.get(name)?.delete(fn),
  postMessage:data=>queueMicrotask(()=>{for(const fn of listeners.get('message')||[])fn({source:window,origin:CFG.readers[0],data});}),
  setTimeout:fn=>{timers.set(++timer,fn);return timer;},clearTimeout:id=>timers.delete(id),
  setInterval:()=>++timer};window.top=window;
 const chrome={runtime:{id:'extension-fixture',sendMessage:message=>w.send(message),onMessage:{addListener:()=>{}}}};
 const context=vm.createContext({window,chrome,location:{origin:CFG.readers[0]},crypto:webcrypto,performance,
  KIKI_FG_CONFIG:CFG,addEventListener:window.addEventListener,clearTimeout:window.clearTimeout,clearInterval:()=>{}});
 vm.runInContext(bridge,context);
 const modules={};
 for(const name of ['floating-guidance','floating-bridge']){
  const source=await readFile(resolve(root,'apps/web/src/features/labs/'+name+'.ts'),'utf8');
  const compiled=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
  context.exports={};context.require=path=>{assert.equal(path,'./floating-guidance');return modules['floating-guidance'];};
  vm.runInContext('(function(exports,require){'+compiled+'\n})(exports,require)',context);modules[name]=context.exports;
 }
 const create=modules['floating-bridge'].createFloatingPublisher;
 const abandoned=create({onCommand:async()=>{}});abandoned.dispose();
 const publisher=create({onCommand:async()=>{}});
 try{
  for(let i=0;i<15;i++)await tick();
  const state=JSON.parse(await readFile(resolve(root,'apps/web/src/features/labs/__fixtures__/python-execution.json'),'utf8')).start;
  state.runtime.capture_active=false;
  publisher.source(()=>({state}));publisher.changed();
  for(let i=0;i<10;i++)await tick();
  publisher.recheck();publisher.recheck();
  for(let i=0;i<15;i++)await tick();
  assert.equal(publisher.status().present,true);assert.equal(publisher.status().bound,true);
  const snapshots=w.calls.filter(v=>v.message.type==='reader_snapshot');
  assert.ok(snapshots.length>=2,'both initial and rechecked snapshots reach the real worker');
  assert.ok(snapshots.every(v=>v.result.ok),JSON.stringify(snapshots.map(v=>v.result)));
  assert.ok(w.messages.some(v=>v.message.type==='fg_snapshot'));
 }finally{publisher.dispose();}
});


test('confirmation handoff carries current publisher identity and rejects stale targets',async()=>{
 const w=worker();await w.bind();
 const hello=await w.send({type:'reader_hello',stream_id:'stream-aaaa-1111'});
 const target={id:'extension-fixture',frameId:0,tab:{id:99},url:CFG.targets[0]+'/'};
 const request={type:'fg_command',command:'focus_confirmation',command_version:1,stream_id:'stream-aaaa-1111',generation:hello.generation,context:{visit_id:'visit-current'},lab_revision:5};
 assert.equal((await w.send({...request,generation:hello.generation-1},target)).ok,false);
 assert.equal((await w.send({...request,command_version:0},target)).ok,false);
 assert.equal((await w.send(request,target)).ok,true);
 const forwarded=w.messages.filter(m=>m.message.type==='fg_command').at(-1);
 assert.equal(forwarded.tabId,1);assert.deepEqual(forwarded.message.context,request.context);
 assert.equal(forwarded.message.command_version,1);assert.equal(forwarded.message.lab_revision,5);
});


test('explicit binding backfills top-frame content scripts in an already-open MATLAB tab',async()=>{
 const w=worker({}, {targetAbsent:true});
 const result=await w.bind();
 assert.equal(result.ok,true);
 const source=w.injections.find(spec=>spec.files);
 assert.deepEqual(source?.target,{tabId:99,frameIds:[0]});
 assert.deepEqual(source?.files,['config.js','core.js','ui.js','content.js']);
 assert.equal(w.storage.kiki_fg.binding.tabId,99);
 assert(w.messages.some(m=>m.message.type==='fg_bound'));
});

test('binding an already-ready target avoids duplicate script injection',async()=>{
 const w=worker();assert.equal((await w.bind()).ok,true);
 assert.equal(w.injections.filter(spec=>spec.files).length,0);
});

test('failed content injection cannot advertise a bound target to the reader',async()=>{
 const w=worker({}, {targetAbsent:true,failInjection:true});
 assert.equal((await w.bind()).ok,false);
 assert.equal(w.storage.kiki_fg?.binding??null,null);
 assert.equal(w.messages.filter(m=>m.message.type==='fg_target_bound').length,0);
});


test('an unanswered readiness handshake times out without binding or notification',async()=>{
 const w=worker({}, {neverReady:true});
 assert.equal((await w.bind()).ok,false);
 assert.equal(w.storage.kiki_fg?.binding??null,null);
 assert.equal(w.messages.filter(m=>m.message.type==='fg_target_bound').length,0);
});

test('content readiness waits for UI initialization and repeated injection creates only one UI',async()=>{
 let finish,created=0,hosts=0;const listeners=[];
 const host={isConnected:false,style:{},attachShadow:()=>({})};
 const document={querySelectorAll:()=>[],createElement:()=>{hosts++;return host;},documentElement:{append:node=>{node.isConnected=true;}}};
 const window={};window.top=window;
 const chrome={runtime:{id:'fixture',onMessage:{addListener:fn=>listeners.push(fn)},sendMessage:async()=>({bound:false})},
  storage:{local:{get:()=>new Promise(resolve=>{finish=resolve;}),set:async()=>{}}}};
 const context=vm.createContext({window,document,chrome,KIKI_FG_CONFIG:CFG,location:{origin:CFG.targets[0]},performance,
  MutationObserver:class{observe(){}},addEventListener:()=>{},setInterval:()=>{},clearTimeout:()=>{},
  KikiFloatingCore:{},KikiFloatingUI:{installRouter:()=>{},create:()=>{created++;return {};}}});
 vm.runInContext(content,context);vm.runInContext(content,context);
 assert.equal(hosts,1);assert.equal(listeners.length,1);assert.equal(created,0);
 let response;assert.equal(listeners[0]({to:'target',type:'fg_probe'},{id:'fixture'},value=>response=value),true);
 await tick();assert.equal(response,undefined);
 finish({});await tick();
 assert.equal(created,1);assert.equal(response.ready,true);assert.equal(response.ok,true);
});

test('core and UI scripts can be injected again without lexical global redeclaration',async()=>{
 const context=vm.createContext({});
 for(const name of ['core','ui']){
  const source=await readFile(new URL('../extension/'+name+'.js',import.meta.url),'utf8');
  vm.runInContext(source,context);vm.runInContext(source,context);
 }
 assert.equal(typeof context.KikiFloatingCore.validate,'function');
 assert.equal(typeof context.KikiFloatingUI.create,'function');
});


test('target disappearance between ready probe and show cannot leave an advertised binding',async()=>{
 const w=worker({}, {boundDeliveryFails:true});
 assert.equal((await w.bind()).ok,false);
 assert.equal(w.storage.kiki_fg.binding,null);
 assert.equal(w.messages.filter(m=>m.message.type==='fg_target_bound').length,0);
});

test('popup preserves the actionable bind failure after refreshing status',async()=>{
 const source=await readFile(new URL('../extension/popup.js',import.meta.url),'utf8');
 const nodes=Object.fromEntries(['bind','unbind','state'].map(id=>[id,{hidden:false,textContent:''}]));
 const chrome={tabs:{query:async()=>[{id:99}]},runtime:{sendMessage:async message=>message.type==='bind_tab'?{ok:false,error:'Reload the MATLAB tab, then show Kiki again.'}:{bindable:true,bound:false,tracker_open:true}}};
 const context=vm.createContext({chrome,document:{getElementById:id=>nodes[id]}});
 vm.runInContext(source,context);await tick();await nodes.bind.onclick();
 assert.equal(nodes.state.textContent,'Reload the MATLAB tab, then show Kiki again.');
 assert.equal(nodes.bind.hidden,false);
});
