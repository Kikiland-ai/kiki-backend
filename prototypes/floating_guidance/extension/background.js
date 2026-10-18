// MV3 worker: binds one MATLAB tab, accepts one reader tab as controller and
// routes floating-guidance/v0.1 messages between them. All routing state lives
// in storage.session, so a suspended worker resumes without resurrecting stale
// content: each new reader stream/document starts a generation; retries reuse it.
importScripts('config.js');
const CFG=globalThis.KIKI_FG_CONFIG,KEY='kiki_fg';
const READER=new Set(['reader_hello','reader_snapshot','reader_command_result','reader_bye']);
const TARGET=new Set(['target_hello','fg_command','fg_rects']);
const POPUP=new Set(['popup_status','bind_tab','unbind']);
let queue=Promise.resolve();
const locked=fn=>{const run=queue.then(fn,fn);queue=run.catch(()=>{});return run;};
const originOf=url=>{try{return new URL(url).origin;}catch{return null;}};
async function load(){return (await chrome.storage.session.get(KEY))[KEY]||{generation:0,binding:null,controller:null,log:[]};}
const save=s=>chrome.storage.session.set({[KEY]:s});
function log(s,event,detail={}){s.log=[...(s.log||[]).slice(-99),{at:new Date().toISOString(),event,...detail}];console.info('[Kiki windows]',event,JSON.stringify(detail));}
async function sendTab(tabId,message){try{return await chrome.tabs.sendMessage(tabId,message,{frameId:0});}catch(error){return {ok:false,error:String(error?.message||error)};}}
const toReader=(s,m)=>s.controller?sendTab(s.controller.tabId,{to:'reader',...m}):Promise.resolve({ok:false,error:'tracker_not_open'});
const toTarget=(s,m)=>s.binding?sendTab(s.binding.tabId,{to:'target',...m}):Promise.resolve({ok:false,error:'no_target'});
async function setHandle(tabId,handle,origins){
 try{const [r]=await chrome.scripting.executeScript({target:{tabId,frameIds:[0]},world:'MAIN',args:[handle,origins],
  func:(value,permitted)=>{try{navigator.mediaDevices?.setCaptureHandleConfig?.({handle:value,exposeOrigin:Boolean(value),permittedOrigins:permitted});return true;}catch(e){return String(e);}}});
  return r?.result===true;}catch{return false;}
}
function kind(sender){
 if(sender.id!==chrome.runtime.id)return null;
 if(!sender.tab)return sender.url?.startsWith(chrome.runtime.getURL('popup.html'))?'popup':null;
 if(sender.frameId!==0)return null;
 const origin=originOf(sender.url);
 return CFG.readers.includes(origin)?'reader':CFG.targets.includes(origin)?'target':null;
}
async function bind(s,tabId){
 const tab=await chrome.tabs.get(tabId),origin=originOf(tab.url);
 if(!CFG.targets.includes(origin))return {ok:false,error:'Open MATLAB Online in this tab first.'};
 if(s.binding&&s.binding.tabId!==tabId){await toTarget(s,{type:'fg_unbound'});await setHandle(s.binding.tabId,'',[]);}
 s.binding={tabId,origin,handle:'kiki-fg-'+crypto.randomUUID(),bound_at:Date.now()};
 const handled=await setHandle(tabId,s.binding.handle,CFG.readers);log(s,'target_bound',{origin,capture_handle_set:handled});await save(s);
 await toTarget(s,{type:'fg_bound',connected:Boolean(s.controller)});
 await toReader(s,{type:'fg_target_bound',handle:s.binding.handle,target_origin:origin});
 return {ok:true,capture_handle_set:handled};
}
async function unbind(s,reason){
 if(!s.binding)return {ok:true};
 await toTarget(s,{type:'fg_unbound'});await setHandle(s.binding.tabId,'',[]);
 await toReader(s,{type:'fg_target_closed',reason});s.binding=null;log(s,'target_unbound',{reason});await save(s);return {ok:true};
}
async function handle(k,m,sender){
 const s=await load(),tabId=sender.tab?.id;
 if(k==='reader'){
  if(m.type==='reader_hello'){
   if(typeof m.stream_id!=='string'||!/^[A-Za-z0-9-]{8,64}$/.test(m.stream_id))return {ok:false,error:'bad_stream'};
   const old=s.controller,document_id=sender.documentId||null;
   // Mount/load/recheck may overlap. A second hello for the same publisher is
   // a retry, not a takeover: invalidating its in-flight snapshots strands it.
   if(old?.tabId===tabId&&old.stream_id===m.stream_id&&(old.document_id||null)===document_id)
    return {ok:true,generation:old.generation,binding:s.binding?{handle:s.binding.handle,target_origin:s.binding.origin}:null};
   s.generation++;
   s.controller={tabId,origin:originOf(sender.url),document_id,stream_id:m.stream_id,generation:s.generation};
   if(old&&old.tabId!==tabId)await sendTab(old.tabId,{to:'reader',type:'fg_superseded'});
   log(s,'reader_hello',{generation:s.generation});await save(s);
   if(s.binding)await toTarget(s,{type:'fg_controller',generation:s.generation});
   return {ok:true,generation:s.generation,binding:s.binding?{handle:s.binding.handle,target_origin:s.binding.origin}:null};
  }
  if(!s.controller||s.controller.tabId!==tabId||(s.controller.document_id||null)!==(sender.documentId||null))
   return {ok:false,error:'not_current_controller'};
  // Additive identity fencing for control messages; the content bridge supplies
  // it for existing page clients too. A late same-tab publisher cannot close or
  // acknowledge commands on behalf of its replacement.
  if((m.stream_id!==undefined||m.generation!==undefined)&&
    (m.stream_id!==s.controller.stream_id||m.generation!==s.controller.generation))
   return {ok:false,error:'stale_stream_or_generation'};
  if(m.type==='reader_snapshot'){
   const message=m.message;
   if(message?.stream_id!==s.controller.stream_id||message?.generation!==s.controller.generation)return {ok:false,error:'stale_stream_or_generation'};
   if(!s.binding)return {ok:false,error:'no_target'};
   const result=await toTarget(s,{type:'fg_snapshot',message});return {ok:result?.result==='displayed'||result?.result==='duplicate',result};
  }
  if(m.type==='reader_command_result'){await toTarget(s,{type:'fg_command_result',request_id:m.request_id,ok:Boolean(m.ok),error:m.error||null});return {ok:true};}
  if(m.type==='reader_bye'){s.controller=null;log(s,'reader_closed');await save(s);await toTarget(s,{type:'fg_disconnect',reason:'reader_closed'});return {ok:true};}
 }
 if(k==='target'){
  const mine=s.binding&&s.binding.tabId===tabId&&s.binding.origin===originOf(sender.url);
  if(m.type==='target_hello'){
   if(!mine)return {bound:false,dev:CFG.dev};
   // A reload keeps the binding (host permission) but needs a new capture
   // handle and a fresh snapshot; cached content is never treated as live.
   const handled=await setHandle(tabId,s.binding.handle,CFG.readers);log(s,'target_reloaded',{capture_handle_set:handled});await save(s);
   if(s.controller)await toReader(s,{type:'fg_snapshot_request',reason:'target_loaded'});
   return {bound:true,connected:Boolean(s.controller),dev:CFG.dev};
  }
  if(!mine)return {ok:false,error:'not_bound'};
  if(m.type==='fg_rects'){if(s.controller)void toReader(s,{type:'fg_rects',rects:m.rects,viewport:m.viewport,moving:Boolean(m.moving)});return {ok:true};}
  if(m.type==='fg_command'){
   if(!s.controller)return {ok:false,error:'tracker_not_open'};
   if(m.command==='focus_confirmation'){
    if(m.command_version!==1||m.stream_id!==s.controller.stream_id||m.generation!==s.controller.generation)return {ok:false,error:'stale_stream_or_generation'};
    await toReader(s,{type:'fg_command',command:m.command,command_version:1,stream_id:m.stream_id,generation:m.generation,context:m.context,lab_revision:m.lab_revision});
    const tab=await chrome.tabs.update(s.controller.tabId,{active:true});await chrome.windows.update(tab.windowId,{focused:true}).catch(()=>{});return {ok:true};
   }
   if(m.command==='open_tracker'){const tab=await chrome.tabs.update(s.controller.tabId,{active:true});await chrome.windows.update(tab.windowId,{focused:true}).catch(()=>{});return {ok:true};}
   if(!['pause','resume'].includes(m.command)||typeof m.request_id!=='string')return {ok:false,error:'unknown_command'};
   log(s,'command',{command:m.command});await save(s);
   const r=await toReader(s,{type:'fg_command',command:m.command,request_id:m.request_id});return {ok:r?.ok!==false,forwarded:true};
  }
 }
 if(k==='popup'){
  if(m.type==='popup_status'){const tab=await chrome.tabs.get(m.tabId).catch(()=>null),origin=originOf(tab?.url);
   return {bindable:CFG.targets.includes(origin),bound:s.binding?.tabId===m.tabId,tracker_open:Boolean(s.controller),dev:CFG.dev,version:CFG.version};}
  if(m.type==='bind_tab')return bind(s,m.tabId);
  if(m.type==='unbind')return unbind(s,'user_removed');
 }
 return {ok:false,error:'unhandled'};
}
chrome.runtime.onMessage.addListener((m,sender,reply)=>{
 const k=kind(sender),allowed=k==='reader'?READER:k==='target'?TARGET:k==='popup'?POPUP:null;
 if(!allowed?.has(m?.type)){reply({ok:false,error:'rejected_sender_or_type'});return false;}
 // Rect reports are frequent and stateless; keep them out of the state lock.
 if(m.type==='fg_rects'){load().then(s=>handle(k,m,sender)).then(reply,()=>reply({ok:false}));return true;}
 locked(()=>handle(k,m,sender)).then(reply,error=>reply({ok:false,error:String(error?.message||error)}));return true;
});
chrome.tabs.onRemoved.addListener(tabId=>locked(async()=>{const s=await load();
 if(s.binding?.tabId===tabId){s.binding=null;log(s,'target_closed');await save(s);await toReader(s,{type:'fg_target_closed',reason:'tab_closed'});}
 if(s.controller?.tabId===tabId){s.controller=null;log(s,'reader_tab_closed');await save(s);await toTarget(s,{type:'fg_disconnect',reason:'reader_closed'});}
}));
chrome.tabs.onUpdated.addListener((tabId,change)=>{if(!change.url)return;locked(async()=>{const s=await load();
 if(s.binding?.tabId===tabId&&originOf(change.url)!==s.binding.origin)await unbind(s,'target_navigated_away');
});});
// Dev builds expose binding for the automated local loop; release builds do not.
if(CFG.dev)globalThis.kikiTest={bind:tabId=>locked(async()=>bind(await load(),tabId)),state:()=>load()};
