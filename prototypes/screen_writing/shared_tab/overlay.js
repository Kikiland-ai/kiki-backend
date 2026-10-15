(() => {
 if(globalThis.KikiTabOverlay)return;
 const ns='http://www.w3.org/2000/svg',host=document.createElement('div');
 host.dataset.kikiOverlay='true';host.style.cssText='all:initial!important;position:fixed!important;inset:0!important;width:100vw!important;height:100vh!important;pointer-events:none!important;z-index:2147483647!important;overflow:hidden!important;';
 const root=host.attachShadow({mode:'closed'}),style=document.createElement('style');style.textContent=':host{pointer-events:none!important}svg{position:absolute;inset:0;width:100%;height:100%;overflow:hidden;pointer-events:none}svg *{pointer-events:none}text{font:600 17px system-ui;paint-order:stroke;stroke:white;stroke-width:5px;stroke-linejoin:round}';root.append(style);document.documentElement.append(host);
 addEventListener('mousemove',e=>{cursor={x:e.clientX/innerWidth,y:e.clientY/innerHeight};},{passive:true});
 let revision=1,sessionId=null,generation=0,highWater=0,masked=false,timer=null,current=null,ink=null,probeInk=null,probeTimer=null,cursor={x:.48,y:.4};
 const node=(tag,attrs={},text=null)=>{const n=document.createElementNS(ns,tag);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,v);if(text!==null)n.textContent=text;return n;};
 const notify=value=>{try{chrome.runtime.sendMessage({to:'background',type:'view_invalidated',...value}).catch(()=>{});}catch{}};
 function clear(){clearTimeout(timer);timer=null;ink?.remove();ink=null;current=null;}
 function invalidate(reason){generation++;revision++;clearTimeout(probeTimer);probeTimer=null;probeInk?.remove();probeInk=null;masked=false;host.style.setProperty('visibility','visible','important');clear();notify({reason,revision,sessionId});}
 const dims=()=>({width:innerWidth,height:innerHeight,dpr:devicePixelRatio,scrollX,scrollY,zoom:visualViewport?.scale||1});
 function descriptor(){return {clock_ms:performance.now(),revision,sessionId,generation,url:location.href,viewport:dims(),cursor,highWater,visible:document.visibilityState==='visible',topLevel:window===top};}
 function begin(id){if(!host.isConnected)document.documentElement.append(host);sessionId=id;highWater=0;masked=false;host.style.setProperty('visibility','visible','important');invalidate('session_started');return descriptor();}
 const unchanged=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
 function valid(t){return t&&t.sessionId===sessionId&&t.revision===revision&&t.generation===generation&&unchanged(t.viewport,dims())&&t.url===location.href;}
 async function commit(packet){
  if(!['screen-overlay/local-test/v1','screen-overlay/viewport-test/v1','screen-overlay/live-prototype/v1'].includes(packet?.schema))throw Error('Production v0.2 requires producer trust validation before delivery');
  if(packet.schema==='screen-overlay/viewport-test/v1'&&packet.frameId!==null)throw Error('Viewport drawing cannot claim a captured frame');
  if(!valid(packet.binding)||masked||!host.isConnected||document.visibilityState!=='visible')throw Error('Tab or view changed; discard entire cue');
  if(!Number.isSafeInteger(packet.sequence)||packet.sequence<=highWater)throw Error('Out-of-order or cancelled cue');
  if(!Number.isFinite(packet.ttlMs)||packet.ttlMs<=0||packet.ttlMs>8000)throw Error('Invalid local deadline');
  if(packet.schema==='screen-overlay/live-prototype/v1'){if(!Number.isFinite(packet.deadline_renderer_ms)||packet.deadline_renderer_ms<=performance.now())throw Error('Tutor cue expired in transport');packet={...packet,ttlMs:Math.min(packet.ttlMs,packet.deadline_renderer_ms-performance.now())};}
  if(!Array.isArray(packet.operations)||packet.operations.length>20)throw Error('Invalid operations');
  const textOnly=packet.schema==='screen-overlay/live-prototype/v1'&&typeof packet.fallback_text==='string';
  if(textOnly&&(!packet.fallback_text||packet.fallback_text.length>1000||packet.operations.length))throw Error('Invalid canonical guide panel');
  const size=dims(),s=node('svg',{viewBox:`0 0 ${size.width} ${size.height}`,role:'img','aria-label':'Kiki temporary tab guidance'});
  s.setAttribute('width',size.width);s.setAttribute('height',size.height);s.style.cssText='position:absolute;inset:0;pointer-events:none;overflow:hidden';
  const colour={lab:'#2563eb',concept:'#16803e',words:'#d93025',english:'#b88600'};
  const finite=(x)=>Number.isFinite(x)&&x>=0&&x<=1;
  const xy=a=>{if(!a||!finite(a.x)||!finite(a.y))throw Error('Invalid normalized anchor');return[a.x*size.width,a.y*size.height];};
  for(const op of packet.operations){if(!colour[op.meaning]||typeof op.label!=='string'||op.label.length>500)throw Error('Missing cue label');const attrs={fill:'none',stroke:colour[op.meaning],'stroke-width':4,'aria-label':op.label};let n;
   if(['box','ellipse'].includes(op.kind)){const r=op.region;if(!r||![r.x,r.y,r.width,r.height].every(finite)||r.width<=0||r.height<=0||r.x+r.width>1.000001||r.y+r.height>1.000001)throw Error('Out-of-frame region');const [x,y]=xy(r),w=r.width*size.width,h=r.height*size.height;n=op.kind==='box'?node('rect',{...attrs,x,y,width:w,height:h,rx:5}):node('ellipse',{...attrs,cx:x+w/2,cy:y+h/2,rx:w/2,ry:h/2});
   }else if(op.kind==='text'){if(typeof op.text!=='string'||op.text.length>500)throw Error('Invalid text');const[x,y]=xy(op.anchor);n=node('text',{x,y,fill:colour[op.meaning],'aria-label':op.label},op.text);
   }else if(op.kind==='pointer'){const[x,y]=xy(op.anchor);n=node('circle',{...attrs,cx:x,cy:y,r:9});
   }else if(['arrow','polyline'].includes(op.kind)){if(!Array.isArray(op.anchors)||op.anchors.length<2||op.anchors.length>20)throw Error('Invalid path');const pts=op.anchors.map(xy);n=node('g',{'aria-label':op.label});n.append(node('polyline',{...attrs,points:pts.map(p=>p.join(',')).join(' ')}));if(op.kind==='arrow'){const p=pts.at(-1),q=pts.at(-2),a=Math.atan2(p[1]-q[1],p[0]-q[0]);n.append(node('path',{...attrs,d:`M ${p[0]-14*Math.cos(a-.5)} ${p[1]-14*Math.sin(a-.5)} L ${p[0]} ${p[1]} L ${p[0]-14*Math.cos(a+.5)} ${p[1]-14*Math.sin(a+.5)}`}));}
   }else throw Error('Unsupported primitive');s.append(n);if(packet.animate){for(const shape of [n,...n.querySelectorAll('rect,ellipse,circle,polyline,path')]){if(['rect','ellipse','circle','polyline','path'].includes(shape.tagName)){shape.setAttribute('pathLength','1');shape.animate([{strokeDasharray:'1',strokeDashoffset:'1'},{strokeDasharray:'1',strokeDashoffset:'0'}],{duration:450,easing:'ease-out'});}}}
  }
  if(!valid(packet.binding))throw Error('View changed during validation');
  const bounds=host.getBoundingClientRect();if(Math.abs(bounds.left)>1||Math.abs(bounds.top)>1||Math.abs(bounds.width-size.width)>1||Math.abs(bounds.height-size.height)>1)throw Error('Overlay surface does not match the tab viewport');
  const layer=document.createElement('div');layer.append(s);
  if(textOnly){const panel=document.createElement('div');panel.setAttribute('role','note');panel.setAttribute('aria-label','Kiki current instruction');panel.style.cssText='position:absolute;left:18px;bottom:32px;max-width:360px;padding:14px 18px;border:2px solid #2563eb;border-radius:10px;background:white;color:#173a72;font:600 16px/1.45 system-ui;box-shadow:0 6px 24px #0002;pointer-events:none;white-space:normal;overflow-wrap:anywhere';panel.textContent='Kiki · '+packet.fallback_text;layer.append(panel);}
  clear();ink=layer;root.append(layer);highWater=packet.sequence;current={sequence:packet.sequence,frameId:packet.frameId};const fence=generation;
  timer=setTimeout(()=>{if(current?.sequence===packet.sequence){clear();notify({reason:'expired',revision,sessionId});}},packet.ttlMs);
  await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
  if(fence!==generation||!valid(packet.binding)||!current||masked||(packet.schema==='screen-overlay/live-prototype/v1'&&performance.now()>=packet.deadline_renderer_ms)){clear();throw Error('View changed before visible delivery');}
  const prototype=packet.schema==='screen-overlay/live-prototype/v1';
  return {request_id:prototype?packet.producer.request_id:null,packet_id:prototype?packet.producer.packet_id:null,local_sequence:packet.sequence,source:packet.schema==='screen-overlay/viewport-test/v1'?'current_tab_viewport':'captured_frame',schema:prototype?'screen-overlay/live-prototype-ack/v1':'screen-overlay/local-test-ack/v1',status:textOnly?'text_only':'tab_rendered',sessionId,frameId:packet.frameId,sequence:prototype?packet.producer.sequence:packet.sequence,revision,operations:packet.operations.length,surface:textOnly?'guide_panel':'selected_browser_tab',deliveredAtConsumer:Date.now(),assessmentEffect:'none'};
 }
 function target(){
  // Authored DOM anchor applies only to this owned practice page; never match text in Simulink.
  if(location.origin!=='https://kiki-screen-writing-demo.woodsycarp256.chatgpt.site'||location.pathname!=='/practice.html')return null;
  const el=document.querySelector('[data-kiki-target="message.frequency"]');if(!el)return null;const b=el.getBoundingClientRect();if(b.width<=0||b.height<=0||b.x<0||b.y<0||b.right>innerWidth||b.bottom>innerHeight)return null;
  return {targetId:'message.frequency',method:'semantic_dom',region:{x:b.x/innerWidth,y:b.y/innerHeight,width:b.width/innerWidth,height:b.height/innerHeight}};
 }
 const events={scroll:'scroll',wheel:'wheel_or_zoom',resize:'resize',pointerdown:'student_action_or_pan',keydown:'keyboard_or_zoom',beforeinput:'edit',pagehide:'navigation'};
 for(const[event,reason]of Object.entries(events))addEventListener(event,()=>invalidate(reason),{capture:true,passive:true});
 document.addEventListener('visibilitychange',()=>invalidate('visibility_changed'));
 visualViewport?.addEventListener('resize',()=>invalidate('visual_viewport_resize'));visualViewport?.addEventListener('scroll',()=>invalidate('visual_viewport_scroll'));
 new MutationObserver(records=>{if(records.some(r=>r.target!==host&&!host.contains(r.target)&&(r.type!=='childList'||[...r.addedNodes,...r.removedNodes].some(n=>n!==host))))invalidate('layout_or_modal_mutation');}).observe(document.documentElement,{subtree:true,childList:true,attributes:true,characterData:true});
 new ResizeObserver(()=>invalidate('document_layout_resize')).observe(document.documentElement);
 const snapshot=async()=>{if(document.visibilityState!=='visible')throw Error('The connected tab is not visible');await Promise.race([new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))),new Promise((_,reject)=>setTimeout(()=>reject(Error('The tab did not paint; return to it and retry')),1000))]);return descriptor();};
 function prepare(options={}){
  clearTimeout(probeTimer);probeTimer=null;probeInk?.remove();probeInk=null;masked=true;
  if(!options.freshness_probe){host.style.setProperty('visibility','hidden','important');return {...descriptor(),target:target()};}
  if(!globalThis.KikiFrameProbe)throw Error('Reload the MATLAB tab after installing adapter 0.4.0.');
  host.style.setProperty('visibility','visible','important');if(ink)ink.style.visibility='hidden';
  const probe=KikiFrameProbe.create(dims()),r=probe.region,size=dims();probeInk=node('svg',{viewBox:'0 0 64 24','aria-hidden':'true'});
  probeInk.style.cssText=`position:absolute;inset:auto;left:${r.x*size.width}px;top:${r.y*size.height}px;width:64px;height:24px;pointer-events:none`;
  for(let i=0;i<96;i++)probeInk.append(node('rect',{x:(i%16)*4,y:Math.floor(i/16)*4,width:4,height:4,fill:KikiFrameProbe.bit(probe,i)?'rgb(224,224,224)':'rgb(32,32,32)'}));
  root.append(probeInk);const visibleProbe=probeInk;probeTimer=setTimeout(()=>{if(probeInk===visibleProbe)invalidate('capture_probe_timeout');},3000);
  return {...descriptor(),target:target(),freshness_probe:probe};
 }
 function finish(binding){clearTimeout(probeTimer);probeTimer=null;probeInk?.remove();probeInk=null;masked=false;host.style.setProperty('visibility','visible','important');if(ink)ink.style.visibility='visible';return valid(binding);}
 const api={begin,descriptor,snapshot,target,commit,clear:()=>invalidate('cleared'),prepare,finish,stop(){sessionId=null;invalidate('stopped');host.remove();}};
 globalThis.KikiTabOverlay=api;
 chrome.runtime.onMessage.addListener((m,s,reply)=>{if(m.to!=='overlay')return;void(async()=>{if(m.type==='begin')return begin(m.sessionId);if(m.type==='prepare'){const ticket=api.prepare({freshness_probe:m.freshness_probe});try{await snapshot();return ticket;}catch(e){api.finish(ticket);throw e;}}if(m.type==='finish')return api.finish(m.binding);if(m.type==='descriptor')return descriptor();if(m.type==='snapshot')return snapshot();if(m.type==='commit')return commit(m.packet);if(m.type==='clear'){if(m.reason==='producer_cancel'){clear();notify({reason:'producer_cancel',revision,sessionId});}else{masked=false;host.style.setProperty('visibility','visible','important');invalidate(m.reason||'cleared');}return{ok:true};}if(m.type==='stop'){sessionId=null;invalidate('stopped');return{ok:true};}})().then(reply,e=>reply({error:e.message}));return true;});
})();
