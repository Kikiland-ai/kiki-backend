// Simulink-shaped controlled underlay. Not MATLAB: it only counts the events
// the page receives, so tests can prove Kiki interactions never reach it.
(() => {
 const types=['pointerdown','pointerup','pointermove','mousedown','mouseup','mousemove','click','dblclick','contextmenu','wheel','keydown','keyup','input','focusin'];
 const page=window.__page={counts:{},total:0,reset(){this.counts={};this.total=0;}};
 const count=e=>{page.counts[e.type]=(page.counts[e.type]||0)+1;page.total++;};
 document.title='Kiki target fixture';
 document.body.innerHTML=`<style>
  body{margin:0;font:13px system-ui,sans-serif;background:#f3f3f3;color:#222;overflow:hidden}
  header{height:40px;background:#2b3a4a;color:#fff;display:flex;align-items:center;padding:0 12px;gap:16px}
  #canvas{display:block;width:100vw;height:calc(100vh - 40px);background:#fff}
  .dialog{position:fixed;left:120px;top:300px;width:300px;background:#fafafa;border:1px solid #888;box-shadow:0 4px 12px rgba(0,0,0,.2)}
  .dialog h3{margin:0;padding:6px 10px;background:#dde3ea;font-size:13px}.dialog label{display:block;padding:10px}
 </style><header><strong>MATLAB Online</strong><span>dsb_sc_test — Simulink (controlled fixture)</span></header>
 <canvas id="canvas"></canvas>
 <div class="dialog" role="dialog" aria-label="Block Parameters: Recovery gain"><h3>Block Parameters: Recovery gain</h3><label>Gain <input id="gain" value="1"></label></div>`;
 const canvas=document.getElementById('canvas'),ctx=canvas.getContext('2d');
 function draw(){
  canvas.width=innerWidth;canvas.height=innerHeight-40;ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);
  ctx.strokeStyle='#e6e6e6';for(let x=0;x<canvas.width;x+=20){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,canvas.height);ctx.stroke();}
  const blocks=[['Message',60,60],['Carrier',60,180],['Modulator',260,120],['Local carrier',460,220],['Receiver product',660,120],['Lowpass',860,120],['Recovery gain',1060,120]];
  ctx.font='13px system-ui';ctx.lineWidth=2;
  for(const [name,x,y] of blocks){ctx.fillStyle='#fff';ctx.strokeStyle='#333';ctx.fillRect(x,y,120,56);ctx.strokeRect(x,y,120,56);ctx.fillStyle='#222';ctx.fillText(name,x+8,y+32);}
  ctx.strokeStyle='#333';ctx.beginPath();ctx.moveTo(180,88);ctx.lineTo(260,140);ctx.moveTo(180,208);ctx.lineTo(260,156);ctx.moveTo(380,148);ctx.lineTo(660,148);ctx.moveTo(780,148);ctx.lineTo(860,148);ctx.moveTo(980,148);ctx.lineTo(1060,148);ctx.stroke();
 }
 draw();addEventListener('resize',draw);
 // Registered after Kiki's router, like ordinary page code loaded after a document_start content script.
 for(const t of types){addEventListener(t,count,true);document.addEventListener(t,count);canvas.addEventListener(t,count);}
})();
