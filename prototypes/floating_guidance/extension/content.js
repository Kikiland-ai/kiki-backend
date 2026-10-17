// MATLAB-tab content script: mounts Kiki's windows, accepts validated, ordered
// snapshots from the worker and reports window rectangles so the reader can
// mask them out of captured frames. It never reads or changes the model.
(() => {
 const CFG=globalThis.KIKI_FG_CONFIG;
 if(window.top!==window||!CFG?.targets.includes(location.origin))return;
 const core=globalThis.KikiFloatingCore,UI=globalThis.KikiFloatingUI;
 const host=document.createElement('kiki-floating-guidance');
 host.style.cssText='all:initial;position:fixed;inset:0;z-index:2147483647;pointer-events:none;display:none';
 // Dev builds use an open root so the automated loop can read what is shown.
 const shadow=host.attachShadow({mode:CFG.dev?'open':'closed'});
 const attach=()=>{if(!host.isConnected&&document.documentElement)document.documentElement.append(host);};
 attach();new MutationObserver(attach).observe(document,{childList:true,subtree:false});
 addEventListener('DOMContentLoaded',()=>{attach();new MutationObserver(attach).observe(document.documentElement,{childList:true});});
 let ui=null,bound=false,message=null,receivedAt=0,lastMessageAt=0,connection='reconnecting',pending=null,highWater=null,commandTimer=null,layout=null,rectTimer=null;
 UI.installRouter(window,host,e=>ui?.handleEvent(e));
 const send=m=>chrome.runtime.sendMessage(m).catch(error=>({ok:false,error:String(error?.message||error)}));
 const draw=()=>ui?.render(core.viewModel(message,{receivedAt,now:performance.now(),lastMessageAt,connection,pending}));
 function sendRects(){rectTimer=null;if(bound&&layout)void send({type:'fg_rects',...layout});}
 function onLayout(value){
  const transition=value.moving!==layout?.moving;layout=value;if(!bound)return;
  // Drag start/end goes out at once; positions while moving are throttled.
  if(transition){clearTimeout(rectTimer);sendRects();}else if(!rectTimer)rectTimer=setTimeout(sendRects,value.moving?16:50);
 }
 function settle(text){pending=null;clearTimeout(commandTimer);if(text!==undefined)ui.showNotice(text);draw();}
 function onCommand(command){
  if(command==='open_tracker'){void send({type:'fg_command',command}).then(r=>{if(!r?.ok)ui.showNotice('Open the Kiki tracker tab first.');});return;}
  if(command!=='pause'&&command!=='resume')return;
  pending=command;ui.showNotice(null);draw();
  clearTimeout(commandTimer);commandTimer=setTimeout(()=>{if(pending)settle('The Kiki tracker did not respond. Use Pause in the tracker tab.');},10000);
  void send({type:'fg_command',command,request_id:crypto.randomUUID()}).then(r=>{if(!r?.ok)settle(r?.error==='tracker_not_open'?'Open the Kiki tracker tab first.':'Could not reach the Kiki tracker.');});
 }
 function show(on){bound=on;ui?.setVisible(on);if(on){draw();sendRects();}}
 function apply(next){
  const valid=core.validate(next);if(!valid.ok)return {result:'rejected',reason:valid.reason};
  const order=core.order(highWater,next);
  if(order==='duplicate'){lastMessageAt=performance.now();return {result:'duplicate',sequence:next.sequence};}
  if(order!=='accept')return {result:'rejected',reason:order};
  highWater={generation:next.generation,stream_id:next.stream_id,sequence:next.sequence};
  message=next;receivedAt=lastMessageAt=performance.now();connection='live';
  const lab=next.body.lab.status;
  if((pending==='pause'&&lab==='paused')||(pending==='resume'&&lab!=='paused'))settle(null);
  if(!bound)show(true);else draw();
  const l=ui.layout();
  return {result:'displayed',sequence:next.sequence,generation:next.generation,lab_revision:next.body.lab_revision,
   action_id:next.body.instructions.now?.action_id||null,minimized:l.minimized,mode:l.mode,windows:ui.rects().length};
 }
 chrome.runtime.onMessage.addListener((m,sender,reply)=>{
  if(sender.id!==chrome.runtime.id||sender.tab||m?.to!=='target')return false;
  if(m.type==='fg_snapshot'){reply(ui?apply(m.message):{result:'rejected',reason:'not_ready'});return false;}
  if(m.type==='fg_bound'){connection=m.connected?'reconnecting':'disconnected';show(true);}
  else if(m.type==='fg_unbound'){message=null;highWater=null;pending=null;show(false);}
  else if(m.type==='fg_controller'){connection='reconnecting';draw();}
  else if(m.type==='fg_disconnect'){connection='disconnected';if(pending)settle(undefined);else draw();}
  else if(m.type==='fg_command_result'){if(!m.ok)settle(m.error||'The tracker could not change guidance.');}
  reply({ok:true});return false;
 });
 setInterval(()=>{if(bound){draw();}},1000);
 setInterval(()=>{if(bound)sendRects();},3000);
 chrome.storage.local.get('kiki_fg_layout').then(saved=>{
  ui=UI.create({host,shadow,canary:CFG.dev,onCommand,onLayout,
   store:{get:()=>saved?.kiki_fg_layout||null,set:value=>void chrome.storage.local.set({kiki_fg_layout:value})}});
  return send({type:'target_hello'});
 }).then(r=>{if(r?.bound){connection=r.connected?'reconnecting':'disconnected';show(true);}});
})();
