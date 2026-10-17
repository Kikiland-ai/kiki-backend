import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';

// Execute the actual controller; only browser/extension/network boundaries are
// fixtures. In particular, no copied invalidation or admission implementation.
function harness(){
 let listener,contextWindow,serial=0,clearRelease,admitRelease;
 const tickets=new Set(),commands=[],trace={textContent:''};
 const binding=()=>({ticket_id:'ticket-'+(++serial),descriptor:{freshness_probe:{},clock_ms:performance.now()}});
 const sandbox={console,performance,crypto,Blob,Uint8Array,Map,Promise,JSON,Date,Error,Math,setTimeout,clearTimeout,setInterval(){},AbortSignal,btoa,structuredClone,
  document:{getElementById:id=>id==='writing-trace'?trace:null},location:{origin:'https://receiver.fixture'},
  KikiGuidanceProtocol:{},KikiWritingProtocol:{sourceMatches:()=>true,clockSample:()=>({upper:Date.now()-performance.now(),sampled:performance.now(),uncertainty:0}),fingerprint:()=>[10],changed:()=>false},KikiFrameProbe:{exclusion:()=>({})},
  KikiWritingFrames:class{setTrack(){}async snapshot(){return {image:{},width:1600,height:800,close(){}};}},createImageBitmap:async()=>({width:1600,height:800,close(){}}),
  fetch:async url=>({ok:true,json:async()=>url.endsWith('/connect')?{connection_id:'connection',guidance_stream_id:'stream'}:{}}),
  addEventListener(type,fn){if(type==='message')listener=fn;},
  postMessage(m){commands.push(m.type);void(async()=>{let result;
   if(m.type==='writer_identity')result={sessionId:'adapter',public_key:{}};
   else if(m.type==='writer_prepare'){result=binding();tickets.add(result.ticket_id);}
   else if(m.type==='writer_finish')result={same_view:true};
   else if(m.type==='writer_admit'){if(admitRelease)await new Promise(r=>{admitRelease=r;});result={attestation:{proof:{ticket_id:m.ticket_id}}};}
   else if(m.type==='writer_clear'){if(clearRelease)await new Promise(r=>{clearRelease=r;});tickets.clear();result={ok:true};}
   else result={ok:true};
   listener({source:contextWindow,origin:sandbox.location.origin,data:{...m,direction:'extension',result}});
  })();}
 };
 sandbox.window=sandbox;vm.createContext(sandbox);contextWindow=vm.runInContext('window',sandbox);vm.runInContext(readFileSync(new URL('../assets/guidance-consumer.js',import.meta.url),'utf8'),sandbox);
 const w=sandbox.KikiWriting;
 w.setStream({getVideoTracks:()=>[{addEventListener(){},readyState:'live'}]});w.attach({lab_session_id:'lab',runtime:{capture_active:true}},'capture');
 async function captured(){const b=await w.prepareFrame({});assert.ok(b);await w.finishFrame(b,{});return b;}
 async function admit(b){return w.admitFrame(b,{frame_id:'frame-'+b.ticket_id,sha256:'hash',width:1600,height:800},new Blob(['jpeg']));}
 return {w,tickets,commands,trace,captured,admit,holdClear(){clearRelease=true;},releaseClear(){const r=clearRelease;clearRelease=null;r();},holdAdmit(){admitRelease=true;},releaseAdmit(){const r=admitRelease;admitRelease=null;r();}};
}

test('cleared source proofs cannot be reused in later analysis requests',async()=>{
 const h=harness(),b=await h.captured(),signed=await h.admit(b),selected={frame:signed.frame,writingBinding:signed};
 assert.ok(h.w.requestHeaders(selected)['X-Guidance-Attestation']);await h.w.invalidate('Rejected previous cue');
 assert.equal(h.tickets.size,0);assert.equal(Object.keys(h.w.requestHeaders(selected)).length,0);
 const shown=JSON.parse(h.trace.textContent);assert.equal(shown.painted_is_cumulative,true);assert.equal(shown.current_cue,null);
});

test('an admission completing after invalidation cannot restore an obsolete frame',async()=>{
 const h=harness(),b=await h.captured();h.holdAdmit();const pending=h.admit(b);await new Promise(r=>setTimeout(r,0));
 await h.w.invalidate('View changed during admission');h.releaseAdmit();assert.equal(await pending,null);
});

test('new captures wait for an outstanding source clear, then recover',async()=>{
 const h=harness();await h.captured();h.holdClear();const clearing=h.w.invalidate('Previous delivery rejected');await new Promise(r=>setTimeout(r,0));
 const before=h.commands.filter(x=>x==='writer_prepare').length,next=h.captured();await new Promise(r=>setTimeout(r,0));
 assert.equal(h.commands.filter(x=>x==='writer_prepare').length,before,'Do not create a ticket that an older clear will erase');
 h.releaseClear();await clearing;const b=await next,signed=await h.admit(b);assert.ok(h.tickets.has(b.ticket_id));assert.ok(signed);
 assert.ok(h.w.requestHeaders({frame:signed.frame,writingBinding:signed})['X-Guidance-Attestation']);
});
