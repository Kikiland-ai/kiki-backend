(() => {
 const origins=new Set(['https://kiki-screen-receiver.woodsycarp256.chatgpt.site','https://kiki-screen-writing-demo.woodsycarp256.chatgpt.site','https://kiki-screen-receiver.woodsycarp256.chatgpt.site']);
 if(!origins.has(location.origin))return;
 const send=value=>window.postMessage({channel:'kiki-tab-adapter',direction:'extension',...value},location.origin);
 window.addEventListener('message',async e=>{
  if(e.source!==window||e.origin!==location.origin||e.data?.channel!=='kiki-tab-adapter'||e.data.direction!=='page')return;
  if(!['writer_identity','writer_handshake','guidance_commit','guidance_cancel','connect','status','probe','diagnostics','stop','writer_status','writer_prepare','writer_finish','writer_admit','writer_commit','writer_clear','writer_cancel','writer_bind'].includes(e.data.type))return;
  try{const result=await chrome.runtime.sendMessage({to:'background',...e.data,to:'background',type:e.data.type,requestId:e.data.requestId});send({type:'response',requestId:e.data.requestId,result});}catch(error){send({type:'error',requestId:e.data.requestId,error:error.message});}
 });
 chrome.runtime.onMessage.addListener(m=>{if(m.to==='controller')send(m);});
})();
