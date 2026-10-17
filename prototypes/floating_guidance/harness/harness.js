// Harness glue: mounts the real window code the way content.js does and steps
// through recorded snapshots. A small control strip changes scenario, aging and
// connection. Test-only accessors live on window.__kiki.
(() => {
 const params=new URLSearchParams(location.search);
 const host=document.createElement('kiki-floating-guidance');
 host.style.cssText='all:initial;position:fixed;inset:0;z-index:2147483647;pointer-events:none;display:block';
 document.documentElement.append(host);
 const shadow=host.attachShadow({mode:'closed'});
 let ui,current=null,receivedAt=0,offset=0,connection='live',pending=null;
 const commands=[],layouts=[];
 KikiFloatingUI.installRouter(window,host,e=>ui.handleEvent(e));
 const store={get(){try{return JSON.parse(localStorage.getItem('kiki-fg-layout'));}catch{return null;}},set(v){try{localStorage.setItem('kiki-fg-layout',JSON.stringify(v));}catch{}}};
 const now=()=>performance.now()+offset;
 function draw(){ui.render(KikiFloatingCore.viewModel(current,{receivedAt,now:now(),lastMessageAt:connection==='lost'?receivedAt-KikiFloatingCore.LEASE_MS-1:now(),connection:connection==='lost'?'live':connection,pending}));}
 ui=KikiFloatingUI.create({host,shadow,canary:params.has('canary'),store,
  onCommand(command){commands.push(command);if(command==='pause'||command==='resume'){pending=command;draw();}},
  onLayout(value){layouts.push({...value,at:performance.now()});if(layouts.length>200)layouts.shift();}});
 function show(name,options={}){
  const m=KIKI_FIXTURES[name];if(!m)throw Error('Unknown scenario '+name);
  const result=KikiFloatingCore.validate(m);if(!result.ok)throw Error(result.reason);
  current=m;receivedAt=performance.now();offset=0;connection=options.connection||'live';pending=null;draw();
 }
 const strip=document.createElement('div');
 strip.style.cssText='position:fixed;left:8px;bottom:8px;z-index:10;background:#fff;border:1px solid #999;padding:6px;font:12px system-ui;display:flex;gap:6px';
 strip.innerHTML=`<select id="h-scenario">${Object.keys(KIKI_FIXTURES).map(k=>`<option>${k}</option>`).join('')}</select>
  <select id="h-connection"><option>live</option><option>lost</option><option>disconnected</option><option>superseded</option></select>
  <button id="h-age">Age +25 s</button>`;
 addEventListener('DOMContentLoaded',()=>{
  document.body.append(strip);
  strip.querySelector('#h-scenario').onchange=e=>show(e.target.value,{connection:strip.querySelector('#h-connection').value});
  strip.querySelector('#h-connection').onchange=e=>{connection=e.target.value;draw();};
  strip.querySelector('#h-age').onclick=()=>{offset+=25000;draw();};
 });
 setInterval(()=>{if(current)draw();},1000);
 window.__kiki={show,draw,commands,layouts,shadow,host,ui,age(ms){offset+=ms;draw();},state:()=>({pending,connection,layout:ui.layout()})};
 show(params.get('scenario')||'fresh');
})();
