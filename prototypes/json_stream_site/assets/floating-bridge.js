import {FG_SCHEMA,projectSnapshot,contentKey} from '/static/floating-guidance.js';
/* Reader side of the Kiki window extension. Publishes the projection of the
   accepted lab state, routes window pause/resume to the existing lab action and
   keeps Kiki's own windows out of every captured frame. Without the extension
   installed this stays idle and capture behaves exactly as before. */
export function createFloatingPublisher({onCommand=async()=>{},onChange=()=>{}}={}){
 const CHANNEL='kiki-floating-guidance',streamId=crypto.randomUUID(),HEARTBEAT_MS=5000,RECENT_MS=1500,PAD=16;
 let present=false,generation=null,binding=null,superseded=false,sequence=0,lastKey=null,lastSentAt=0,source=()=>null,bridgeSeq=0;
 let rectReports=[],viewport=null,moving=false,lastSafety={mode:'none'},lastDisplay=null;
 const frames={none:0,redact:0,block:0};
 const waiting=new Map(),log=[];
 const record=(event,detail={})=>{log.push({at:new Date().toISOString(),event,...detail});if(log.length>200)log.shift();};
 function post(message){return new Promise(resolve=>{const bridge_id=++bridgeSeq;waiting.set(bridge_id,resolve);
  window.postMessage({channel:CHANNEL,direction:'page',bridge_id,...message},location.origin);
  setTimeout(()=>{if(waiting.delete(bridge_id))resolve({ok:false,error:'bridge_timeout'});},5000);});}
 async function hello(){
  const r=await post({type:'reader_hello',stream_id:streamId,lab_session_id:source()?.state?.lab_session_id||null});
  if(!r?.ok){record('hello_failed',{error:r?.error});return;}
  generation=r.generation;binding=r.binding;superseded=false;lastKey=null;rectReports=[];viewport=null;record('hello',{generation,bound:Boolean(binding)});onChange();void flush(true);
 }
 addEventListener('message',e=>{
  if(e.source!==window||e.origin!==location.origin||e.data?.channel!==CHANNEL||e.data.direction!=='extension')return;
  const m=e.data;
  if(m.type==='response'){const resolve=waiting.get(m.bridge_id);if(resolve){waiting.delete(m.bridge_id);resolve(m.result);}return;}
  if(m.type==='extension_present'){if(!present){present=true;record('extension_present',{version:m.version});void hello();}return;}
  if(m.type==='fg_target_bound'){binding={handle:m.handle,target_origin:m.target_origin};rectReports=[];viewport=null;record('target_bound');onChange();void flush(true);}
  else if(m.type==='fg_target_closed'){binding=null;rectReports=[];viewport=null;record('target_closed');onChange();}
  else if(m.type==='fg_superseded'){superseded=true;generation=null;record('superseded');onChange();}
  else if(m.type==='fg_snapshot_request')void flush(true);
  else if(m.type==='fg_rects'){
   const at=performance.now();rectReports.push({at,rects:Array.isArray(m.rects)?m.rects.slice(0,4):[]});
   rectReports=rectReports.filter((r,i)=>i===rectReports.length-1||at-r.at<=RECENT_MS);viewport=m.viewport||viewport;moving=Boolean(m.moving);
  }else if(m.type==='fg_command')void command(m);
 });
 async function command(m){
  let ok=true,error=null;record('command',{command:m.command});
  try{await onCommand(m.command);}catch(err){ok=false;error=String(err?.message||err).slice(0,200);}
  await post({type:'reader_command_result',request_id:m.request_id,ok,error});void flush(true);
 }
 async function flush(force){
  if(!present||!generation||!binding||superseded)return;
  const input=source();if(!input?.state)return;
  const body=projectSnapshot(input.state,{...input,blockedReason:lastSafety.mode==='block'?lastSafety.reason:null}),key=contentKey(body),now=performance.now();
  if(!force&&key===lastKey&&now-lastSentAt<HEARTBEAT_MS)return;
  lastKey=key;lastSentAt=now;
  const message={schema:FG_SCHEMA,type:'replace_snapshot',stream_id:streamId,generation,sequence:++sequence,issued_at:new Date().toISOString(),body};
  const r=await post({type:'reader_snapshot',message});
  lastDisplay=r?.result||null;
  record(r?.ok?'snapshot_delivered':'snapshot_rejected',{sequence:message.sequence,lab_revision:body.lab_revision,checkpoint_id:body.context.checkpoint_id,
   action_id:body.instructions.now?.action_id||null,observation_id:body.screen_context.observation_id,screen:body.screen_context.status,display:r?.result?.result||r?.error||null});
 }
 setInterval(()=>void flush(false),1000);
 addEventListener('pagehide',()=>{if(present&&generation)window.postMessage({channel:CHANNEL,direction:'page',bridge_id:0,type:'reader_bye'},location.origin);});
 // Decide how a sampled frame may be used before any JPEG is encoded.
 function sampleSafety(track,width,height){const safety=decideSafety(track,width,height);frames[safety.mode]++;return safety;}
 function decideSafety(track,width,height){
  if(!present||!binding)return lastSafety={mode:'none'};
  const settings=track?.getSettings?.()||{},handle=track?.getCaptureHandle?.()||null;
  if(settings.displaySurface!=='browser'||handle?.handle!==binding.handle)
   return lastSafety={mode:'block',reason:'Share the MATLAB tab where Kiki is shown, so Kiki can keep its windows out of the screen read.'};
  if(!viewport)return lastSafety={mode:'block',reason:'Waiting for Kiki window positions before reading the screen.'};
  if(moving)return lastSafety={mode:'block',reason:'A Kiki window is moving; the next frame will be read.'};
  const sx=width/viewport.w,sy=height/viewport.h;
  if(!(sx>0&&sy>0)||Math.abs(sx-sy)/sx>0.04)return lastSafety={mode:'block',reason:'The shared tab size does not match the Kiki tab. Share the MATLAB tab again.'};
  const now=performance.now(),boxes=rectReports.filter((r,i)=>i===rectReports.length-1||now-r.at<=RECENT_MS).flatMap(r=>r.rects)
   .map(r=>({x:(r.x-PAD)*sx,y:(r.y-PAD)*sy,w:(r.w+2*PAD)*sx,h:(r.h+2*PAD)*sy}));
  return lastSafety={mode:'redact',boxes};
 }
 function apply(ctx,safety,width,height){
  ctx.save();ctx.fillStyle='#7f7f7f';
  if(safety.mode==='block')ctx.fillRect(0,0,width,height);else for(const b of safety.boxes||[])ctx.fillRect(b.x,b.y,b.w,b.h);
  ctx.restore();
 }
 return {
  source(fn){source=fn;},changed(){void flush(false);},sampleSafety,apply,
  blockedReason:()=>lastSafety.mode==='block'?lastSafety.reason:null,
  status:()=>({present,generation,bound:Boolean(binding),superseded,stream_id:streamId,sequence,safety:lastSafety.mode,frames:{...frames},display:lastDisplay}),
  diagnostics:()=>({status:{present,generation,bound:Boolean(binding),superseded,stream_id:streamId,sequence},events:[...log]}),
 };
}
