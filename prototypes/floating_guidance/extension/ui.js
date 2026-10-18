// Kiki mini windows in Breadboard style. Renders a view model from core.js and
// owns only local layout (dock/split/minimize/position/details). Every event
// that starts inside Kiki is consumed before the host page sees it, so Kiki
// interactions never reach Simulink or count as lab actions.
(() => {
 const EVENTS=['pointerdown','pointerup','pointermove','pointercancel','pointerover','pointerout','mousedown','mouseup','mousemove','mouseover','mouseout',
  'click','dblclick','auxclick','contextmenu','wheel','keydown','keyup','keypress','beforeinput','input','touchstart','touchmove','touchend','focusin','focusout',
  'copy','cut','paste','selectstart','dragstart'];
 const CSS=`
.layer{--paper:#fbfaf7;--raised:#fff;--ink:#1f1f1f;--pencil:#5f6368;--line:#d9d6cf;--blue:#4285f4;--blue-ink:#1967d2;--blue-tint:#e8f0fe;--on-blue-ink:#fff;
 --red:#ea4335;--yellow:#fbbc05;--green:#34a853;--yellow-ink:#9a5500;--yellow-tint:#fef7e0;--focus:#1967d2;--lift:0 8px 24px rgba(31,31,31,.12);
 --key:0 3px 0 #0f4fa8;--key-n:0 3px 0 #c9c5bc;font:14px/1.45 "Google Sans","Noto Sans","Noto Sans Oriya",system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink)}
@media (prefers-color-scheme:dark){.layer{--paper:#14161a;--raised:#1e2127;--ink:#ecedef;--pencil:#a8adb4;--line:#3a3f48;--blue-ink:#8ab4f8;--blue-tint:#1b2a44;
 --on-blue-ink:#062e6f;--yellow-ink:#fdd663;--yellow-tint:#3a3220;--focus:#8ab4f8;--lift:0 8px 24px rgba(0,0,0,.5);--key:0 3px 0 #4f7fc4;--key-n:0 3px 0 #0b0d11}}
.win{position:fixed;pointer-events:auto;box-sizing:border-box;width:344px;max-width:calc(100vw - 16px);display:flex;flex-direction:column;
 background:var(--raised);border:1px solid var(--line);border-radius:24px;box-shadow:var(--lift);overflow:hidden}
.win[data-id=b]{width:300px}
.win[hidden],.launcher[hidden],[hidden]{display:none!important}
.bar{display:flex;align-items:center;gap:8px;padding:8px 8px 8px 16px;cursor:grab;user-select:none;touch-action:none;border-bottom:1px solid var(--line)}
.bar.dragging{cursor:grabbing}
.dots{display:inline-grid;grid-template-columns:6px 6px;gap:3px;flex:none}.dots i{width:6px;height:6px;border-radius:50%}
.dots i:nth-child(1){background:var(--blue)}.dots i:nth-child(2){background:var(--red)}.dots i:nth-child(3){background:var(--yellow)}.dots i:nth-child(4){background:var(--green)}
.title{flex:1;min-width:0;display:flex;flex-direction:column;line-height:1.2}.title strong{font-weight:700}.hdr{color:var(--pencil);font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.hdr:empty{display:none}
.icon{flex:none;width:32px;height:32px;border-radius:999px;border:0;background:transparent;color:var(--pencil);display:grid;place-items:center;cursor:pointer;padding:0}
.icon:hover{background:var(--blue-tint);color:var(--blue-ink)}.icon svg{width:18px;height:18px}
:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.win:focus{outline:none}
.body{padding:12px 16px;overflow:auto;overscroll-behavior:contain;max-height:min(56vh,520px);flex:1 1 auto;min-height:0}
.label{display:inline-block;font-size:12px;font-weight:600;color:var(--blue-ink);background:var(--blue-tint);border-radius:999px;padding:2px 10px;margin:0}
.label[data-tone=muted]{color:var(--pencil);background:transparent;box-shadow:inset 0 0 0 1px var(--line)}
h2{font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:var(--pencil);margin:12px 0 4px;font-weight:600;display:flex;gap:8px;align-items:baseline}
h2 .age,h2 .tag{letter-spacing:0;text-transform:none;font-weight:400}
.now{font-size:17px;line-height:1.35;font-weight:600;margin:0}.next{margin:0}
table{border-collapse:collapse;margin:8px 0 0;width:100%}td{padding:4px 8px 4px 0;border-top:1px solid var(--line);vertical-align:top}
code{font-family:"Roboto Mono",ui-monospace,Consolas,monospace;font-variant-numeric:tabular-nums}
.toggle{font:inherit;font-size:13px;font-weight:600;color:var(--blue-ink);background:none;border:0;padding:6px 0;margin-top:6px;cursor:pointer}
dl{margin:4px 0 0}dt{font-size:12px;color:var(--pencil);margin-top:8px}dd{margin:2px 0 0}ol{margin:2px 0 0;padding-left:20px}
.screen{border-top:1px solid var(--line);margin-top:14px}.win[data-id=b] .screen{border-top:0;margin-top:0}.win[data-id=b] .screen h2:first-child{margin-top:0}
.summary{margin:0}.check{margin:6px 0 0;padding-left:18px}.uncertain{margin:6px 0 0;color:var(--pencil)}
.foot{display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:10px 16px 14px;border-top:1px solid var(--line)}
.status{flex:1 1 100%;font-size:12px;color:var(--pencil)}.status::before{content:"";display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;background:var(--pencil);vertical-align:1px}
.status[data-live=true]::before{background:var(--blue)}
.btn{font:inherit;font-weight:600;border-radius:999px;padding:6px 14px;cursor:pointer;border:1px solid var(--line);background:var(--raised);color:var(--ink);box-shadow:var(--key-n)}
.btn.primary{background:var(--blue-ink);color:var(--on-blue-ink);border-color:transparent;box-shadow:var(--key)}
.btn:active:not(:disabled){transform:translateY(2px);box-shadow:none}.btn:disabled{opacity:.55;cursor:default}
.notice{flex:1 1 100%;margin:0;font-size:12px;color:var(--yellow-ink);background:var(--yellow-tint);border-radius:12px;padding:6px 10px}
.launcher{position:fixed;pointer-events:auto;display:flex;align-items:center;gap:8px;padding:8px 14px;border-radius:999px;border:1px solid var(--line);
 background:var(--raised);box-shadow:var(--lift);font:inherit;font-weight:600;color:var(--ink);cursor:pointer}
.launcher small{font-weight:400;color:var(--pencil)}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.canary{display:inline-flex;gap:6px;align-items:center;font-size:11px;color:#c000c0}.canary i{width:20px;height:20px;background:#ff00ff;display:inline-block}
@media (prefers-reduced-motion:reduce){.btn:active:not(:disabled){transform:none}*{transition:none!important;animation:none!important}}`;
 const ICONS={
  split:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="8" height="16" rx="2"/><rect x="13" y="4" width="8" height="16" rx="2"/></svg>',
  dock:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M4 12h16"/></svg>',
  reset:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 12a8 8 0 1 0 2.3-5.6"/><path d="M4 4v4h4"/></svg>',
  minimize:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 18h14"/></svg>'};
 function h(tag,attrs={},...children){const node=document.createElement(tag);for(const [k,v] of Object.entries(attrs))if(v!==null&&v!==undefined&&v!==false)node.setAttribute(k,v===true?'':v);
  for(const c of children.flat())if(c!==null&&c!==undefined&&c!==false)node.append(c instanceof Node?c:document.createTextNode(String(c)));return node;}
 const icon=(action,label)=>{const b=h('button',{class:'icon',type:'button','data-action':action,'aria-label':label,title:label});b.innerHTML=ICONS[action];return b;};
 const dots=()=>h('span',{class:'dots','aria-hidden':'true'},h('i'),h('i'),h('i'),h('i'));

 // Consume every event that originates inside Kiki at window capture, before
 // any page listener. The handler resolves the real inner target itself.
 function installRouter(win,host,handler){
  const route=e=>{if(e.target!==host)return;e.stopImmediatePropagation();handler(e);};
  for(const type of EVENTS)win.addEventListener(type,route,{capture:true});
  return ()=>{for(const type of EVENTS)win.removeEventListener(type,route,{capture:true});};
 }

 function create({host,shadow,onCommand=()=>{},store={get:()=>null,set:()=>{}},canary=false,onLayout=()=>{}}){
  const defaults={mode:'docked',minimized:false,details:false,a:null,b:null,launcher:null};
  const layout={...defaults,...(store.get()||{})};let vm=null,dragging=null,lastAnnounce='';
  const style=h('style');style.textContent=CSS;
  const live=h('div',{class:'sr',role:'status','aria-live':'polite'});
  const label=h('p',{class:'label'}),now=h('p',{class:'now'}),settings=h('table',{hidden:true},h('tbody'));
  const toggle=h('button',{class:'toggle',type:'button','data-action':'details','aria-expanded':'false','aria-controls':'kiki-details'},'Step details');
  const where=h('dd'),how=h('ol'),result=h('dd'),why=h('dd'),already=h('dd');
  const details=h('dl',{id:'kiki-details',hidden:true},h('dt',{},'Where'),where,h('dt',{},'How'),h('dd',{},how),h('dt',{},'Expected result'),result,
   h('dt',{'data-for':'why'},'Why this step'),why,h('dt',{'data-for':'already'},'If it is already done'),already);
  const nextTag=h('span',{class:'tag',hidden:true},'· next stage'),next=h('p',{class:'next'});
  const guide=h('div',{class:'guide'},label,h('h2',{},'Now'),now,settings,toggle,details,h('h2',{},'Next',nextTag),next);
  const screenHeading=h('span'),age=h('span',{class:'age'}),summary=h('p',{class:'summary'}),check=h('ul',{class:'check',hidden:true}),uncertain=h('p',{class:'uncertain',hidden:true});
  const screen=h('div',{class:'screen'},h('h2',{},screenHeading,age),summary,check,uncertain);
  const status=h('div',{class:'status'}),notice=h('p',{class:'notice',hidden:true,role:'alert'});
  const pause=h('button',{class:'btn primary',type:'button','data-action':'pause'},'Pause guidance');
  const confirm=h('button',{class:'btn',type:'button','data-action':'focus_confirmation'},'Confirm saved model in tracker');
  const tracker=h('button',{class:'btn',type:'button','data-action':'open_tracker'},'Open tracker');
  const hdr=h('span',{class:'hdr'}),splitButton=icon('split','Split into two windows');
  const barA=h('div',{class:'bar','data-drag':'a',tabindex:'0','aria-label':'Kiki guide. Use arrow keys to move this window.'},dots(),h('span',{class:'title'},h('strong',{},'Kiki'),hdr),splitButton,icon('reset','Reset window position'),icon('minimize','Minimize Kiki'));
  const bodyA=h('div',{class:'body'},guide,screen);
  const foot=h('div',{class:'foot'},status,notice,pause,confirm,tracker,canary?h('span',{class:'canary'},h('i'),'KIKI CANARY 7319'):null);
  const winA=h('section',{class:'win','data-id':'a',role:'region','aria-label':'Kiki guide',tabindex:'-1'},barA,bodyA,foot);
  const barB=h('div',{class:'bar','data-drag':'b',tabindex:'0','aria-label':'Screen context. Use arrow keys to move this window.'},dots(),h('span',{class:'title'},h('strong',{},'Screen context')),icon('dock','Dock windows together'),icon('minimize','Minimize Kiki'));
  const bodyB=h('div',{class:'body'});
  const winB=h('section',{class:'win','data-id':'b',role:'region','aria-label':'Kiki screen context',tabindex:'-1',hidden:true},barB,bodyB);
  const launcherState=h('small');
  const launcher=h('button',{class:'launcher',type:'button','data-action':'restore','aria-label':'Open Kiki',hidden:true},dots(),'Kiki',launcherState);
  const layer=h('div',{class:'layer'},winA,winB,launcher,live);
  shadow.replaceChildren(style,layer);

  const frames={a:winA,b:winB};
  const size=node=>{const r=node.getBoundingClientRect();return {w:r.width||344,h:r.height||200};};
  function clamp(id,pos){const s=size(frames[id]);return {x:Math.round(Math.min(Math.max(8,pos.x),Math.max(8,innerWidth-s.w-8))),y:Math.round(Math.min(Math.max(8,pos.y),Math.max(8,innerHeight-48)))};}
  function defaultPos(id){
   const a={x:innerWidth-size(winA).w-16,y:72};if(id==='a')return a;
   const ra=winA.getBoundingClientRect(),sb=size(winB);
   return ra.bottom+12+Math.min(sb.h,240)<innerHeight?{x:ra.left,y:ra.bottom+12}:{x:ra.left-sb.w-12,y:ra.top};
  }
  const save=()=>store.set({...layout});
  function place(){
   winA.hidden=layout.minimized;winB.hidden=layout.minimized||layout.mode!=='split';launcher.hidden=!layout.minimized;
   if(layout.mode==='split'&&screen.parentNode!==bodyB)bodyB.append(screen);
   if(layout.mode!=='split'&&screen.parentNode!==bodyA)bodyA.append(screen);
   splitButton.hidden=layout.mode==='split';
   for(const id of ['a','b']){if(frames[id].hidden)continue;layout[id]=clamp(id,layout[id]||defaultPos(id));frames[id].style.left=layout[id].x+'px';frames[id].style.top=layout[id].y+'px';frames[id].style.maxHeight=Math.max(120,innerHeight-layout[id].y-8)+'px';}
   if(!launcher.hidden){const p=layout.a||defaultPos('a');launcher.style.left=Math.max(8,Math.min(p.x,innerWidth-140))+'px';launcher.style.top=Math.max(8,Math.min(p.y,innerHeight-56))+'px';}
   report(Boolean(dragging));
  }
  function rects(){
   if(host.style.display==='none')return [];
   return [winA,winB,launcher].filter(n=>!n.hidden).map(n=>{const r=n.getBoundingClientRect();return {x:r.left,y:r.top,w:r.width,h:r.height};}).filter(r=>r.w&&r.h);
  }
  function report(moving){onLayout({rects:rects(),viewport:{w:innerWidth,h:innerHeight},moving});}
  function setText(node,value){const text=value??'';if(node.textContent!==text)node.textContent=text;}
  function render(model){
   vm=model;
   if(vm.empty){setText(label,'Kiki');label.dataset.tone='muted';setText(now,vm.status.text);settings.hidden=true;toggle.hidden=true;details.hidden=true;setText(next,'');
    setText(screenHeading,'Screen context');setText(age,'');setText(summary,'Waiting for the Kiki tracker.');check.hidden=uncertain.hidden=true;
    setText(status,vm.status.text);status.dataset.live='false';pause.disabled=true;setText(hdr,'');setText(launcherState,'· not connected');place();return;}
   setText(hdr,vm.header);setText(label,vm.guide.label);label.dataset.tone=vm.guide.label==='Current step'?'':'muted';
   const a=vm.guide.now;setText(now,a?.title||(vm.guide.label==='Experiment complete'?'Experiment complete. Review and export your journal in the tracker.':'Keep the experiment visible; Kiki is waiting for the tracker.'));
   const rows=a?.settings||[];settings.hidden=!rows.length;
   settings.tBodies[0].replaceChildren(...rows.map(s=>h('tr',{},h('td',{},s.field),h('td',{},h('code',{},s.value)))));
   const hasDetails=Boolean(a&&(a.where||a.how?.length||a.expected_result||vm.guide.why||a.already_done_help));
   toggle.hidden=!hasDetails;details.hidden=!hasDetails||!layout.details;toggle.setAttribute('aria-expanded',String(hasDetails&&layout.details));
   setText(toggle,layout.details?'Hide step details':'Step details');
   setText(where,a?.where||'—');how.replaceChildren(...(a?.how||[]).map(t=>h('li',{},t)));setText(result,a?.expected_result||'—');
   setText(why,vm.guide.why||'');why.hidden=!vm.guide.why;details.querySelector('[data-for=why]').hidden=!vm.guide.why;
   setText(already,a?.already_done_help||'');already.hidden=!a?.already_done_help;details.querySelector('[data-for=already]').hidden=!a?.already_done_help;
   nextTag.hidden=!vm.guide.next?.crosses_stage;setText(next,vm.guide.next?.title||'Save and review your experiment.');
   setText(screenHeading,vm.screen.heading);setText(age,vm.screen.age?`· ${vm.screen.age}`:'');
   setText(summary,vm.screen.reason?`${vm.screen.reason}${vm.screen.summary?` Earlier view: ${vm.screen.summary}`:''}`:vm.screen.summary||(vm.screen.status==='waiting'?'Keep the current step visible in Simulink.':'No screen view to show.'));
   check.hidden=!vm.screen.check.length;check.replaceChildren(...vm.screen.check.map(t=>h('li',{},`Check this: ${t}`)));
   uncertain.hidden=!vm.screen.uncertainties.length;setText(uncertain,vm.screen.uncertainties.length?`Not sure: ${vm.screen.uncertainties.join(' ')}`:'');
   setText(status,vm.status.text);status.dataset.live=String(vm.status.live);
   setText(pause,vm.pause.label);pause.disabled=vm.pause.disabled;pause.dataset.command=vm.pause.command;
   setText(launcherState,`· ${vm.status.live?(vm.guide.label==='Guidance paused'?'paused':'connected'):'not live'}`);
   // Announce step and connection changes only, never every sampled frame.
   const announce=`${vm.guide.label}. Now: ${a?.title||''}`;if(announce!==lastAnnounce){lastAnnounce=announce;live.textContent=announce;}
   place();
  }
  function showNotice(text){setText(notice,text||'');notice.hidden=!text;report(Boolean(dragging));}
  function act(action){
   if(action==='split'){layout.mode='split';layout.b=null;}
   else if(action==='dock')layout.mode='docked';
   else if(action==='reset'){layout.a=null;layout.b=null;}
   else if(action==='minimize'){layout.minimized=true;}
   else if(action==='restore'){layout.minimized=false;}
   else if(action==='details'){layout.details=!layout.details;if(vm)render(vm);}
   else if(action==='pause'){if(!pause.disabled)onCommand(pause.dataset.command);return;}
   else if(action==='focus_confirmation'){onCommand('focus_confirmation');return;}
   else if(action==='open_tracker'){onCommand('open_tracker');return;}
   else return;
   save();place();
   if(action==='minimize')launcher.focus({preventScroll:true});
   if(action==='restore'||action==='dock')barA.focus({preventScroll:true});
   if(action==='split')barB.focus({preventScroll:true});
  }
  function inner(e){
   if(e.type.startsWith('key')||(e.type==='click'&&e.detail===0))return shadow.activeElement;
   return Number.isFinite(e.clientX)?shadow.elementFromPoint(e.clientX,e.clientY):null;
  }
  function handleEvent(e){
   if(dragging&&e.pointerId===dragging.pointerId&&(e.type==='pointermove'||e.type==='pointerup'||e.type==='pointercancel')){
    if(e.type==='pointermove'){layout[dragging.id]=clamp(dragging.id,{x:e.clientX-dragging.dx,y:e.clientY-dragging.dy});frames[dragging.id].style.left=layout[dragging.id].x+'px';frames[dragging.id].style.top=layout[dragging.id].y+'px';frames[dragging.id].style.maxHeight=Math.max(120,innerHeight-layout[dragging.id].y-8)+'px';report(true);}
    else{dragging.bar.classList.remove('dragging');dragging=null;save();report(false);}
    return;
   }
   const target=inner(e),actionNode=target?.closest?.('[data-action]'),bar=target?.closest?.('[data-drag]');
   if(e.type==='pointerdown'&&bar&&!actionNode&&e.button===0){
    const id=bar.dataset.drag,r=frames[id].getBoundingClientRect();
    dragging={id,bar,pointerId:e.pointerId,dx:e.clientX-r.left,dy:e.clientY-r.top};bar.classList.add('dragging');
    try{bar.setPointerCapture(e.pointerId);}catch{}
    return;
   }
   if(e.type==='click'&&actionNode){act(actionNode.dataset.action);return;}
   if(e.type==='keydown'){
    if(e.key==='Escape'&&!layout.minimized){act('minimize');return;}
    const focused=shadow.activeElement?.closest?.('[data-drag]');
    if(focused&&focused===shadow.activeElement){const step=e.shiftKey?64:16,d={ArrowLeft:[-step,0],ArrowRight:[step,0],ArrowUp:[0,-step],ArrowDown:[0,step]}[e.key];
     if(d){const id=focused.dataset.drag,p=layout[id]||defaultPos(id);layout[id]=clamp(id,{x:p.x+d[0],y:p.y+d[1]});save();place();e.preventDefault();}
     else if(e.key==='Home'){act('reset');e.preventDefault();}}
   }
  }
  const resizeObserver=new ResizeObserver(()=>report(Boolean(dragging)));resizeObserver.observe(winA);resizeObserver.observe(winB);
  addEventListener('resize',()=>place());
  return {render,handleEvent,rects,showNotice,place,layout:()=>({...layout}),setVisible(on){host.style.display=on?'block':'none';if(on)place();else report(false);}};
 }
 globalThis.KikiFloatingUI={create,installRouter,EVENTS};
})();
