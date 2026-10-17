// Reader-page bridge. Forwards only the floating-guidance message types in each
// direction, only for the trusted reader origins, only in the top frame.
(() => {
 const CFG=globalThis.KIKI_FG_CONFIG;
 if(window.top!==window||!CFG?.readers.includes(location.origin))return;
 const CHANNEL='kiki-floating-guidance';
 const PAGE=new Set(['reader_hello','reader_snapshot','reader_command_result','reader_bye']);
 const EXTENSION=new Set(['fg_target_bound','fg_target_closed','fg_command','fg_rects','fg_snapshot_request','fg_superseded']);
 const post=m=>window.postMessage({channel:CHANNEL,direction:'extension',...m},location.origin);
 window.addEventListener('message',e=>{
  if(e.source!==window||e.origin!==location.origin||e.data?.channel!==CHANNEL||e.data.direction!=='page'||!PAGE.has(e.data.type))return;
  const {channel,direction,bridge_id,...message}=e.data;
  chrome.runtime.sendMessage(message).then(result=>post({type:'response',bridge_id,result}),error=>post({type:'response',bridge_id,result:{ok:false,error:String(error?.message||error)}}));
 });
 chrome.runtime.onMessage.addListener((m,sender)=>{
  if(sender.id!==chrome.runtime.id||sender.tab||m?.to!=='reader'||!EXTENSION.has(m.type))return false;
  const {to,...message}=m;post(message);return false;
 });
 const announce=()=>post({type:'extension_present',version:CFG.version});
 announce();addEventListener('DOMContentLoaded',announce);addEventListener('load',announce);
})();
