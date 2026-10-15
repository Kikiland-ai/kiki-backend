importScripts('demo.js','frame-probe.js','guidance-protocol.js');
let guidanceKey=null,guidancePublicKey=null,guidanceConnection=null;
async function guidanceSignedAck(ack){const bytes=await crypto.subtle.sign({name:'ECDSA',hash:'SHA-256'},guidanceKey,new TextEncoder().encode(JSON.stringify(ack)));return {ack,signature:btoa(String.fromCharCode(...new Uint8Array(bytes)))};}
const CONTROL=new Set(['https://kiki-screen-receiver.woodsycarp256.chatgpt.site','https://kiki-screen-writing-demo.woodsycarp256.chatgpt.site','https://kiki-screen-receiver.woodsycarp256.chatgpt.site']);
const VERSION=chrome.runtime.getManifest().version;
const writingTickets=new Map(),writingHighWater=new Map();
let writerStream=null;const retiredWritingStreams=new Set();let writingMessageCount=0;
let session=null,frame=null,seq=0,controllers=new Set(),busy=false,armed=false,queuedViewport=null,events=[],lastError=null,lastAck=null,captureCount=0,restorePromise=null,workerLogged=false,logWrites=Promise.resolve();
function record(stage,details={}){
 const event={consumer_time:new Date().toISOString(),stage,...details};events.push(event);if(events.length>200)events.shift();
 console[details.error?'error':'info']('[Kiki]',stage,JSON.stringify(details));
 logWrites=logWrites.then(()=>chrome.storage.session.set({kiki_diagnostics:{adapter_version:VERSION,events:[...events],last_error:lastError}})).catch(()=>{});
}
async function restore(){
 if(session)return;
 if(!restorePromise)restorePromise=(async()=>{const stored=await chrome.storage.session.get(['kiki_selected_tab','kiki_diagnostics']);
  if(!workerLogged&&stored.kiki_diagnostics?.adapter_version===VERSION){events=stored.kiki_diagnostics.events||[];lastError=stored.kiki_diagnostics.last_error||null;}
  if(!workerLogged){workerLogged=true;record('worker_started',{adapter_version:VERSION});}
  const saved=stored.kiki_selected_tab;if(!saved)return;
  try{const d=await chrome.tabs.sendMessage(saved.tabId,{to:'overlay',type:'descriptor'});if(d?.sessionId===saved.id&&d.url===saved.url){session=saved;seq=Math.max(seq,d.highWater||0);record('session_restored');}}
  catch{};
 })().finally(()=>{restorePromise=null;});
 await restorePromise;
}
const overlay=(type,extra={})=>{if(!session)throw Error('No connected tab. Connect from the extension popup first.');return chrome.tabs.sendMessage(session.tabId,{to:'overlay',type,...extra});};
async function checkedOverlay(type,extra={}){const response=await overlay(type,extra);if(response===undefined||response===null)throw Error('The tab renderer did not respond. Refresh the tab and reconnect.');if(response.error)throw Error(response.error);return response;}
async function broadcast(type,value={}){
 for(const id of controllers){
  // Sending telemetry back into the sampled page changes its DOM, causing a
  // self-invalidation loop. It can be a target OR a telemetry panel, never both.
  if(id===session?.tabId)continue;
  try{await chrome.tabs.sendMessage(id,{to:'controller',type,...value});}catch{controllers.delete(id);}
 }
}
const summary=()=>({adapter_version:VERSION,connected:!!session,tabTitle:session?.title,tabId:session?.tabId,sessionId:session?.id,capturing:!!session?.capturing,captureCount,last_error:lastError,last_ack:lastAck,latestFrame:frame?{frameId:frame.id,sha256:frame.sha256,width:frame.width,height:frame.height,viewRevision:frame.binding.revision}:null,mode:session?.tutor?'live_tutor':'browser_local_drawing_test',capture_handle:session?.captureHandle||null,producerConnected:!!guidanceConnection,guidance_connection_id:guidanceConnection?.connection_id||null});
async function stop(reason='stopped'){
 const old=session;guidanceConnection=null;guidanceKey=null;guidancePublicKey=null;writingTickets.clear();writingHighWater.clear();writerStream=null;retiredWritingStreams.clear();writingMessageCount=0;session=null;frame=null;armed=false;queuedViewport=null;
 await chrome.storage.session.set({kiki_selected_tab:null});
 if(old?.tutor)try{await chrome.scripting.executeScript({target:{tabId:old.tabId},world:'MAIN',func:()=>navigator.mediaDevices?.setCaptureHandleConfig?.({handle:'',exposeOrigin:false,permittedOrigins:[]})});}catch{}
 if(old)try{await chrome.tabs.sendMessage(old.tabId,{to:'overlay',type:'stop'});}catch{}
 try{await chrome.runtime.sendMessage({to:'offscreen',type:'stop'});}catch{}
 record('stopped',{reason});await broadcast('stopped',{reason});return {ok:true,adapter_version:VERSION};
}
async function deliverViewport(operations=null){
 if(session?.tutor)throw Error('Tutor cues come from the reader. Use the separate drawing smoke-test connection for fixed shapes.');
 const sid=session?.id;if(!sid)throw Error('Connect a website tab first.');
 const binding=await checkedOverlay('snapshot');
 if(!session||session.id!==sid||binding.sessionId!==sid)throw Error('The tab changed before drawing.');
 if(!binding.visible)throw Error('Return to the connected tab before drawing.');
 if(binding.viewport.zoom!==1)throw Error('Reset pinch zoom before drawing.');
 const packet={schema:'screen-overlay/viewport-test/v1',sequence:++seq,frameId:null,binding,ttlMs:7000,animate:true,operations:operations||kikiDrawingDemo(binding)};
 record('render_requested',{source:'current_tab_viewport',sequence:packet.sequence,view_revision:binding.revision,operations:packet.operations.length});
 const ack=await checkedOverlay('commit',{packet});
 if(!session||session.id!==sid||ack.status!=='tab_rendered')throw Error('Drawing was not acknowledged on the connected tab.');
 lastAck=ack;lastError=null;record('rendered',{source:ack.source,sequence:ack.sequence,operations:ack.operations});
 await broadcast('ack',{ack});return {ok:true,...summary()};
}
async function start(tabId,tutor=false){
 if(busy)throw Error('Connection is already changing.');busy=true;
 try{
  await stop('new_tab');lastError=null;lastAck=null;captureCount=0;
  record('connect_requested');
  const tab=await chrome.tabs.get(tabId);if(!/^https?:/.test(tab.url||''))throw Error('Choose a website tab. Browser settings and protected pages cannot be annotated.');
  await chrome.scripting.executeScript({target:{tabId},files:['frame-probe.js','overlay.js']});record('renderer_injected');
  session={id:crypto.randomUUID(),tabId,title:tab.title,url:tab.url,capturing:false,tutor,captureHandle:tutor?'kiki:'+crypto.randomUUID():null};seq=0;
  const descriptor=await checkedOverlay('begin',{sessionId:session.id});
  if(!descriptor.topLevel)throw Error('The renderer must run in the top-level tab.');
  if(tutor){
   if(new URL(tab.url).origin!=='https://matlab.mathworks.com')throw Error('Connect to tutor on the MATLAB/Simulink Online tab.');
   const results=await chrome.scripting.executeScript({target:{tabId},world:'MAIN',func:config=>{if(!navigator.mediaDevices?.setCaptureHandleConfig)return false;navigator.mediaDevices.setCaptureHandleConfig(config);return true;},args:[{handle:session.captureHandle,exposeOrigin:true,permittedOrigins:['https://kiki-screen-receiver.woodsycarp256.chatgpt.site']}]});
   if(results?.[0]?.result!==true)throw Error('Chrome Capture Handle is unavailable. Use a current Chrome tab.');
  }
  await chrome.storage.session.set({kiki_selected_tab:session});
  record('renderer_connected',{visible:descriptor.visible,width:descriptor.viewport.width,height:descriptor.viewport.height});
  if(!tutor)await deliverViewport();await broadcast('connected',summary());return summary();
 }catch(e){if(tutor)await stop('tutor_connect_failed');lastError=e.message;record('connect_failed',{error:e.message});throw e;}finally{busy=false;}
}
async function startCapture(){
 if(!session)throw Error('Connect this tab first.');
 if(session.tutor)throw Error('Tutor mode uses the reader site screen share. A second capture is disabled.');
 if(session.capturing)return summary();
 record('capture_requested');
 if(!await chrome.offscreen.hasDocument())await chrome.offscreen.createDocument({url:'offscreen.html',reasons:['USER_MEDIA'],justification:'Optionally test periodic samples of the explicitly selected tab.'});
 const streamId=await chrome.tabCapture.getMediaStreamId({targetTabId:session.tabId});
 const response=await chrome.runtime.sendMessage({to:'offscreen',type:'start',streamId});
 if(!response||response.error)throw Error(response?.error||'The capture document did not respond.');
 session.capturing=true;await chrome.storage.session.set({kiki_selected_tab:session});record('capture_started');return summary();
}
async function handle(m,sender){
 await restore();
 const fromOffscreen=sender.url===chrome.runtime.getURL('offscreen.html');
 const fromTarget=!!session&&sender.tab?.id===session.tabId;
 let fromController=false;try{fromController=!!sender.tab&&CONTROL.has(new URL(sender.url).origin);}catch{}
 const fromPopup=!sender.tab&&sender.url===chrome.runtime.getURL('popup.html');
 if(m.type==='start'){if(!fromPopup)throw Error('Connect requires the extension popup on the selected tab.');return start(m.tabId,m.mode==='tutor');}
 if(m.type==='view_invalidated'){
  if(!fromTarget||m.sessionId!==session.id)return;
  if(!['expired','producer_cancel','consumer_cancel'].includes(m.reason))writingTickets.clear();
  frame=null;record('view_invalidated',{reason:m.reason,view_revision:m.revision});await broadcast('invalidated',{reason:m.reason,viewRevision:m.revision});
  if(queuedViewport&&m.reason==='visibility_changed'){const d=await checkedOverlay('descriptor');if(d.visible){const q=queuedViewport;queuedViewport=null;try{if(q.expires<performance.now())throw Error('Queued drawing expired; trigger it again on the connected tab.');await deliverViewport();}catch(e){lastError=e.message;record('render_failed',{error:e.message});await broadcast('capture_error',{error:e.message});}}}return{ok:true};
 }
 if(m.type.startsWith('writer_')||m.type.startsWith('guidance_')){
  if(!fromController||new URL(sender.url).origin!=='https://kiki-screen-receiver.woodsycarp256.chatgpt.site')throw Error('Only the signed-in reader page can drive tutor cues.');
  controllers.add(sender.tab.id);
  if(m.type==='writer_status')return {...summary(),binding:session?await checkedOverlay('descriptor'):null};
  if(!session?.tutor)throw Error('Choose Connect to tutor on the shared Simulink tab.');
  if(m.type==='writer_identity'){
   if(!guidanceKey){const pair=await crypto.subtle.generateKey({name:'ECDSA',namedCurve:'P-256'},false,['sign','verify']);guidanceKey=pair.privateKey;guidancePublicKey=await crypto.subtle.exportKey('jwk',pair.publicKey);}
   return {...summary(),public_key:guidancePublicKey,binding:await checkedOverlay('descriptor')};
  }
  if(m.type==='writer_handshake'){
   if(!guidanceKey||m.negotiation?.controller_origin!==new URL(sender.url).origin||m.negotiation?.payload_contract!=='analysis-owned-guidance/v0.1'||m.negotiation?.stream_contract!=='lab-analysis-stream/v3')throw Error('Unsupported server negotiation.');
   guidanceConnection=m.negotiation;writerStream={guidance_stream_id:m.negotiation.guidance_stream_id,lab_session_id:m.lab_session_id};writingHighWater.clear();await checkedOverlay('clear',{reason:'producer_cancel'});record('guidance_negotiated',{connection_id:guidanceConnection.connection_id});return {ok:true};
  }
  if(m.type==='guidance_cancel'){
   const c=m.cancel;if(c?.guidance_stream_id!==guidanceConnection?.guidance_stream_id||!Number.isSafeInteger(c.cue_sequence))throw Error('Foreign cancellation stream.');
   const high=writingHighWater.get(c.guidance_stream_id)||0;if(c.cue_sequence<=high)return {duplicate:true};writingHighWater.set(c.guidance_stream_id,c.cue_sequence);await checkedOverlay('clear',{reason:'producer_cancel'});record('guidance_cancelled',{sequence:c.cue_sequence});return guidanceSignedAck(KikiGuidanceProtocol.ack(c,'cancelled','ordered_cancel'));
  }
  if(m.type==='guidance_commit'){
   const e=m.envelope,t=writingTickets.get(m.ticket_id),b=t?.binding.descriptor;
   if(!guidanceConnection||e?.guidance_stream_id!==guidanceConnection.guidance_stream_id||!t?.attestation||t.expires<=performance.now()||e.context.lab_session_id!==writerStream.lab_session_id)throw Error('Expired or foreign source admission.');
   if(e.source_binding.binding_id!==session.id||e.source_binding.binding_revision!==b.revision||e.source_binding.transform_revision!==b.revision||e.frame.frame_id!==t.frame.frame_id||e.frame.sha256!==t.frame.sha256)throw Error('Foreign frame or transform.');
   const high=writingHighWater.get(e.guidance_stream_id)||0;if(!Number.isSafeInteger(e.cue_sequence)||e.cue_sequence<=high)throw Error('Out-of-order guidance.');
   const d=await checkedOverlay('descriptor');if(d.revision!==b.revision||d.generation!==b.generation||JSON.stringify(d.viewport)!==JSON.stringify(b.viewport)||!d.visible)throw Error('Live source changed before paint.');
   const operations=KikiGuidanceProtocol.compile(e);writingHighWater.set(e.guidance_stream_id,e.cue_sequence);
   if(e.outcome==='none'){await checkedOverlay('clear',{reason:'producer_cancel'});return {cleared:true};}
   const result=await checkedOverlay('commit',{packet:{schema:'screen-overlay/live-prototype/v1',sequence:++seq,frameId:t.frame.frame_id,binding:b,ttlMs:m.ttlMs,deadline_renderer_ms:m.deadline_renderer_ms,operations,fallback_text:e.outcome==='text_only'?e.packet.fallback.instruction:null,producer:{request_id:e.analysis_request_id,packet_id:e.packet.packet_id,sequence:e.cue_sequence}}});
   if(!writingTickets.has(m.ticket_id)||t.expires<=performance.now())throw Error('Source invalidated before paint acknowledgement.');
   const ack=KikiGuidanceProtocol.ack(e,result.status==='text_only'?'text_only':'live_rendered','painted',d);lastAck=ack;lastError=null;record('guidance_painted',{request_id:e.analysis_request_id,frame_id:e.frame.frame_id,sequence:e.cue_sequence,operations:operations.length});return guidanceSignedAck(ack);
  }
  if(m.type==='writer_bind'){
   if(typeof m.guidance_stream_id!=='string'||!m.guidance_stream_id||typeof m.lab_session_id!=='string'||!m.lab_session_id||retiredWritingStreams.has(m.guidance_stream_id))throw Error('Invalid or retired guidance stream.');
   if(writerStream?.guidance_stream_id===m.guidance_stream_id){if(writerStream.lab_session_id!==m.lab_session_id)throw Error('Foreign lab for guidance stream.');return {ok:true};}
   if(writerStream)retiredWritingStreams.add(writerStream.guidance_stream_id);
   writerStream={guidance_stream_id:m.guidance_stream_id,lab_session_id:m.lab_session_id};writingMessageCount=0;
   await checkedOverlay('clear',{reason:'producer_cancel'});record('tutor_stream_bound',{guidance_stream_id:m.guidance_stream_id});return {ok:true};
  }
  if(m.type==='writer_clear'){writingTickets.clear();await checkedOverlay('clear',{reason:'producer_cancel'});return {ok:true};}
  if(m.type==='writer_cancel'){
   const c=m.cancel;if(c?.schema!=='screen-writing/v0.2'||c.message_type!=='cancel'||typeof c.guidance_stream_id!=='string'||!Number.isSafeInteger(c.cue_sequence)||c.cue_sequence<1)throw Error('Invalid ordered cancellation.');
   if(c.guidance_stream_id!==writerStream?.guidance_stream_id||c.context?.lab_session_id!==writerStream.lab_session_id)throw Error('Cancellation belongs to another stream.');
   const high=writingHighWater.get(c.guidance_stream_id)||0;if(c.cue_sequence<=high)return {duplicate:true};
   if(writingMessageCount>=500)throw Error('Guidance stream limit reached. Reconnect the extension.');writingMessageCount++;
   writingHighWater.set(c.guidance_stream_id,c.cue_sequence);await checkedOverlay('clear',{reason:'producer_cancel'});record('tutor_cancelled',{sequence:c.cue_sequence,reason:c.reason});return {ok:true};
  }
  if(m.type==='writer_prepare'){
   for(const[id,t]of writingTickets)if(t.expires<=performance.now())writingTickets.delete(id);
   if(writingTickets.size>=32)writingTickets.delete(writingTickets.keys().next().value);
   const descriptor=await checkedOverlay('prepare',{freshness_probe:true}),ticket_id=crypto.randomUUID();
   if(!KikiFrameProbe.valid(descriptor.freshness_probe)){await checkedOverlay('finish',{binding:descriptor});throw Error('Reload the MATLAB tab after installing adapter 0.4.0.');}
   const binding={schema:'screen-writing/tab-binding-prototype/v1',ticket_id,adapter_session_id:session.id,capture_handle:session.captureHandle,descriptor};
   writingTickets.set(ticket_id,{binding,expires:performance.now()+20000,frame:null,finished:false});return binding;
  }
  const ticket=writingTickets.get(m.ticket_id||m.cue?.binding?.ticket_id);
  if(!ticket||ticket.expires<=performance.now())throw Error('Source capture ticket expired or changed.');
  if(m.type==='writer_finish'){const same_view=await checkedOverlay('finish',{binding:ticket.binding.descriptor});ticket.finished=same_view;if(!same_view)writingTickets.delete(m.ticket_id);return {same_view};}
  if(m.type==='writer_admit'){
   const f=m.frame,d=await checkedOverlay('descriptor'),b=ticket.binding.descriptor;
   if(!ticket.finished||d.revision!==b.revision||d.generation!==b.generation||JSON.stringify(d.viewport)!==JSON.stringify(b.viewport)||d.url!==b.url)throw Error('Source changed before frame admission.');
   if(!f||!Number.isInteger(f.width)||!Number.isInteger(f.height)||f.width<=0||f.height<=0||f.width>1600||f.height>1600||!/^([a-f0-9]{64})$/.test(f.sha256)||typeof f.frame_id!=='string'||!f.frame_id||f.frame_id.length>200||
    Math.abs(f.source_width/f.source_height-b.viewport.width/b.viewport.height)>.02||Math.abs(f.width/f.height-b.viewport.width/b.viewport.height)>.02||b.viewport.zoom!==1)throw Error('Unverified captured-tab geometry.');
   ticket.frame=structuredClone(f);
   if(m.jpeg){
    if(!guidanceKey||!guidanceConnection)throw Error('Negotiate the guidance connection first.');
    const bytes=Uint8Array.from(atob(m.jpeg),c=>c.charCodeAt(0)),digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
    if(digest!==f.sha256||bytes.length!==f.byte_count)throw Error('Signed admission JPEG does not match receipt.');
    const bitmap=await createImageBitmap(new Blob([bytes],{type:'image/jpeg'}));let matched=false;try{matched=bitmap.width===f.width&&bitmap.height===f.height&&KikiFrameProbe.matches(bitmap,b.freshness_probe);}finally{bitmap.close();}if(!matched)throw Error('The admitted JPEG did not capture this tab marker.');
    const proof={schema:'kiki-native-binding/v1',connection_id:guidanceConnection.connection_id,challenge:guidanceConnection.challenge,adapter_session_id:session.id,capture_handle:session.captureHandle,controller_origin:new URL(sender.url).origin,binding:ticket.binding,frame:f};
    const signature=await crypto.subtle.sign({name:'ECDSA',hash:'SHA-256'},guidanceKey,new TextEncoder().encode(JSON.stringify(proof)));
    ticket.attestation={proof,signature:btoa(String.fromCharCode(...new Uint8Array(signature)))};record('guidance_frame_signed',{frame_id:f.frame_id});return {ok:true,attestation:ticket.attestation};
   }return {ok:true};
  }
  if(m.type==='writer_commit'){
   const c=m.cue,p=c?.packet,r=c?.request,f=ticket.frame,b=ticket.binding.descriptor;
   if(p?.guidance_stream_id!==writerStream?.guidance_stream_id||p?.context?.lab_session_id!==writerStream.lab_session_id)throw Error('Cue belongs to another stream.');
   if(c?.schema!=='screen-writing/live-prototype/v1'||c.production_live_proof!==false||!f||p?.request_id!==r?.request_id||p.guidance_stream_id!==r.guidance_stream_id||p.cue_sequence!==r.cue_sequence||
    p.frame.frame_id!==f.frame_id||p.frame.sha256!==f.sha256||p.frame.encoded_width!==f.width||p.frame.encoded_height!==f.height||p.frame.view_revision!==f.view_revision||
    p.delivery.adapter_binding_id!==session.id||p.delivery.transform_revision!==b.revision||c.binding.capture_handle!==session.captureHandle||
    JSON.stringify(c.binding)!==JSON.stringify(ticket.binding)||p.context.view_revision!==f.view_revision)throw Error('Foreign cue, frame or source binding.');
   const high=writingHighWater.get(p.guidance_stream_id)||0;if(!Number.isSafeInteger(p.cue_sequence)||p.cue_sequence<=high)throw Error('Out-of-order tutor cue.');
   if(writingMessageCount>=500)throw Error('Guidance stream limit reached. Reconnect the extension for a fresh stream.');
   if(!Number.isFinite(m.ttlMs)||m.ttlMs<=0||m.ttlMs>7900)throw Error('Cue has no usable deadline.');
   if(m.fallback_text!==undefined&&m.fallback_text!==null&&(p.fallback.reason!=='unresolved_required_target'||m.fallback_text!==r.canonical_instruction||m.operations.length!==0))throw Error('Foreign fallback guidance.');
   writingHighWater.set(p.guidance_stream_id,p.cue_sequence);writingMessageCount++;
   const ack=await checkedOverlay('commit',{packet:{schema:'screen-overlay/live-prototype/v1',sequence:++seq,frameId:f.frame_id,binding:b,
    ttlMs:Math.min(m.ttlMs,ticket.expires-performance.now()),deadline_renderer_ms:m.deadline_renderer_ms,operations:m.operations,fallback_text:m.fallback_text,producer:{request_id:r.request_id,packet_id:p.packet_id,sequence:p.cue_sequence}}});
   if(!writingTickets.has(c.binding.ticket_id)||ticket.expires<=performance.now()){await checkedOverlay('clear',{reason:'producer_cancel'});throw Error('View changed before acknowledgement.');}
   lastAck=ack;record('tutor_painted',{request_id:r.request_id,frame_id:f.frame_id,operations:ack.operations});return ack;
  }
  throw Error('Unsupported writing operation.');
 }
 if(['prepare','finish','frame','source_ended','capture_error'].includes(m.type)){
  if(!fromOffscreen)throw Error('Only the capture document can submit pixels.');
  if(m.type==='source_ended'){if(session){session.capturing=false;await chrome.storage.session.set({kiki_selected_tab:session});}frame=null;record('capture_ended');return{ok:true};}
  if(!session)return{error:'No selected tab'};
  if(m.type==='prepare'){const d=await checkedOverlay('prepare');record('capture_prepared',{view_revision:d.revision,visible:d.visible});return{...d,ticketId:crypto.randomUUID()};}
  if(m.type==='finish'){
   if(m.ticket?.sessionId!==session.id)return{error:'Capture session changed'};
   const ready=await checkedOverlay('finish',{binding:m.ticket});record('capture_unmasked',{same_view:ready});
   if(ready&&armed&&frame?.binding.visible){try{await deliverCaptured();}catch(e){armed=false;lastError=e.message;record('render_failed',{error:e.message});await broadcast('capture_error',{error:e.message});}}
   return ready;
  }
  if(m.type==='capture_error'){frame=null;lastError=m.error;if(lastAck?.source==='captured_frame')await overlay('clear',{reason:'capture_error'});record('capture_failed',{error:m.error,video_state:m.videoState});await broadcast('capture_error',{error:m.error});return{ok:true};}
  if(m.type==='frame'){
   const sid=session.id,d=await checkedOverlay('descriptor'),t=m.ticket;
   const reject=reason=>{frame=null;lastError=reason;record('frame_rejected',{error:reason,source_width:m.sourceWidth,source_height:m.sourceHeight,viewport_width:t?.viewport?.width,viewport_height:t?.viewport?.height});return{error:reason};};
   if(!session||session.id!==sid||!t||t.sessionId!==sid||d.revision!==t.revision||d.generation!==t.generation||JSON.stringify(d.viewport)!==JSON.stringify(t.viewport)||d.url!==t.url)return reject('View changed during capture');
   if(!m.width||!m.height||!Number.isFinite(m.sourceWidth)||!Number.isFinite(m.sourceHeight)||Math.abs(m.sourceWidth/m.sourceHeight-t.viewport.width/t.viewport.height)>.02||t.viewport.zoom!==1)return reject('Unverified source-to-viewport transform');
   frame={...m,id:crypto.randomUUID(),binding:t,expires:performance.now()+8000};captureCount++;lastError=null;record('frame_accepted',{frame_number:captureCount,width:m.width,height:m.height,view_revision:t.revision});
   await broadcast('frame',{...summary(),capturedElapsedMs:m.capturedElapsedMs,byteCount:m.byteCount});return{ok:true};
  }
 }
 if(['connect','status','diagnostics','draw_demo','draw_json','start_capture','capture_probe','probe','stop'].includes(m.type)){
  if(!fromController&&!fromPopup)throw Error('Unknown controller.');
  if(fromController)controllers.add(sender.tab.id);
  if(m.type==='diagnostics'){await logWrites;return{...summary(),events:[...events],pixel_data_included:false};}
  if(m.type==='stop')return stop();
  if(m.type==='connect'||m.type==='status')return{...summary(),is_selected_tab:sender.tab?.id===session?.tabId};
  if(!session)throw Error('Connect this tab first.');
  if(m.type==='start_capture'){if(!fromPopup)throw Error('Start capture from the extension popup.');return startCapture();}
  if(m.type==='capture_probe'){armed={mode:'drawing'};record('captured_render_armed');return{armed:true};}
  if(m.type==='draw_json'){
   if(!fromPopup||!Array.isArray(m.operations)||m.operations.length>20)throw Error('Drawing JSON must contain at most 20 operations.');
   return deliverViewport(structuredClone(m.operations));
  }
  if(fromController){const d=await checkedOverlay('descriptor');if(!d.visible){queuedViewport={expires:performance.now()+8000};record('viewport_drawing_queued');return{armed:true,message:'Return to the connected tab within 8 seconds to see the drawing.'};}}
  return deliverViewport();
 }
 throw Error('Unsupported adapter message.');
}
async function deliverCaptured(){
 if(!session||!frame||performance.now()>=frame.expires)throw Error('Wait for a fresh frame from the connected tab.');
 const selected=frame,sid=session.id,operations=kikiDrawingDemo(selected.binding);
 const packet={schema:'screen-overlay/local-test/v1',sequence:++seq,frameId:selected.id,binding:selected.binding,ttlMs:Math.min(7000,selected.expires-performance.now()),animate:true,operations};
 record('render_requested',{source:'captured_frame',sequence:packet.sequence});
 const ack=await checkedOverlay('commit',{packet});
 if(!session||session.id!==sid||!frame||frame.id!==selected.id||performance.now()>=selected.expires){if(session)await overlay('clear',{reason:'frame_invalidated_before_ack'});throw Error('Context changed before acknowledgement.');}
 armed=false;lastAck=ack;record('rendered',{source:'captured_frame',sequence:ack.sequence});await broadcast('ack',{ack});return ack;
}
chrome.runtime.onMessage.addListener((m,sender,reply)=>{if(m.to!=='background')return;handle(m,sender).then(result=>{if(result&&typeof result==='object'&&sender.tab){let controller=false;try{controller=CONTROL.has(new URL(sender.url).origin);}catch{}if(controller)result={...result,is_selected_tab:sender.tab.id===session?.tabId};}reply(result);},e=>{lastError=e.message;record('request_failed',{request_type:m.type,error:e.message});reply({error:e.message,adapter_version:VERSION});});return true;});
chrome.tabs.onRemoved.addListener(id=>{controllers.delete(id);if(session?.tabId===id)void stop('tab_closed');});
chrome.tabs.onUpdated.addListener((id,change)=>{if(session?.tabId===id&&(change.status==='loading'||change.url))void stop('navigation');});
chrome.commands.onCommand.addListener(async command=>{if(command!=='show-live-drawing')return;try{await restore();if(!session)throw Error('Connect this tab from the extension first.');const[tab]=await chrome.tabs.query({active:true,currentWindow:true});if(tab?.id!==session.tabId)throw Error('Return to the connected tab.');await deliverViewport();}catch(e){lastError=e.message;record('shortcut_failed',{error:e.message});}});
