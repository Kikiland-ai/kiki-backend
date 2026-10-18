// Reader-page bridge. Forwards only the floating-guidance message types in each
// direction, only for the trusted reader origins, only in the top frame.
(() => {
 const CFG=globalThis.KIKI_FG_CONFIG;
 if(window.top!==window||!CFG?.readers.includes(location.origin))return;
 const CHANNEL='kiki-floating-guidance';
 const PAGE=new Set(['reader_hello','reader_snapshot','reader_command_result','reader_bye']);
 const EXTENSION=new Set(['fg_target_bound','fg_target_closed','fg_command','fg_rects','fg_snapshot_request','fg_superseded']);
 const post=m=>window.postMessage({channel:CHANNEL,direction:'extension',...m},location.origin);
 let activeStream=null,activeGeneration=null,helloEpoch=0;
 window.addEventListener('message',e=>{
  if(e.source!==window||e.origin!==location.origin||e.data?.channel!==CHANNEL||e.data.direction!=='page'||!PAGE.has(e.data.type))return;
  const {channel,direction,bridge_id,...message}=e.data;
  if(message.type==='reader_hello'){
   if(typeof message.stream_id!=='string'||!/^[A-Za-z0-9-]{8,64}$/.test(message.stream_id))return;
   if(activeStream!==message.stream_id)activeGeneration=null;
   activeStream=message.stream_id;helloEpoch++;
  }
  const stream=message.type==='reader_snapshot'?message.message?.stream_id:message.stream_id||activeStream,epoch=helloEpoch;
  if(!stream||stream!==activeStream)return;
  if(message.type==='reader_bye'||message.type==='reader_command_result'){
   message.stream_id=stream;message.generation=message.generation??activeGeneration;
   if(!Number.isSafeInteger(message.generation))return;
  }
  const reply=result=>{
   // Per-publisher bridge IDs restart at 1 (including React StrictMode mounts).
   // Never broadcast an old publisher's result into its replacement's waiter.
   if(stream!==activeStream||epoch!==helloEpoch)return;
   if(message.type==='reader_hello'&&result?.ok)activeGeneration=result.generation;
   post({type:'response',bridge_id,stream_id:stream,result});
  };
  chrome.runtime.sendMessage(message).then(reply,error=>reply({ok:false,error:String(error?.message||error)}));
 });
 chrome.runtime.onMessage.addListener((m,sender)=>{
  if(sender.id!==chrome.runtime.id||sender.tab||m?.to!=='reader'||!EXTENSION.has(m.type))return false;
  if(m.type==='fg_superseded'){helloEpoch++;activeGeneration=null;}
  const {to,...message}=m;post(message);return false;
 });
 const announce=()=>post({type:'extension_present',version:CFG.version});
 announce();addEventListener('DOMContentLoaded',announce);addEventListener('load',announce);
})();
