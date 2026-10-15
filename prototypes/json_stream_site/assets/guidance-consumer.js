/* The controller owns one capture/paint mutex and one attachment generation.
 * The model chooses marks; this consumer validates, transforms and delivers. */
(() => {
 const P=KikiGuidanceProtocol,F=KikiWritingProtocol,$=id=>document.getElementById(id);
 let track=null,video=null,lab=null,captureId=null,connection=null,identityKey=null,epoch=0,mask=Promise.resolve(),active=null,high=0,queue=null,delivering=null,polling=false,offset=null,lastFP=null,inflightSequence=0;
 const pending=new Map(),samples=new Map(),retained=new Map(),events=[];
 const health={capture:'Waiting for shared pixels',analysis:'Waiting for analysis',delivery:'No cue received',captured:0,painted:0,last_failure:null};
 const text=(key,value)=>{health[key]=value;const el=$('writing-'+key);if(el)el.textContent=value;};
 function log(stage,details={}){events.push({at:new Date().toISOString(),stage,...details});if(events.length>100)events.shift();const el=$('writing-trace');if(el)el.textContent=JSON.stringify({health,events},null,2);}
 function message(s){text('delivery',s);if($('writing-status'))$('writing-status').textContent=s;}
 function adapter(type,data={},timeout=1800){return new Promise((resolve,reject)=>{const requestId=crypto.randomUUID(),timer=setTimeout(()=>{pending.delete(requestId);reject(Error('Extension operation '+type+' exceeded '+Math.round(timeout)+' ms.'));},timeout);pending.set(requestId,{resolve,reject,timer});window.postMessage({channel:'kiki-tab-adapter',direction:'page',type,requestId,...data},location.origin);});}
 window.addEventListener('message',e=>{if(e.source!==window||e.origin!==location.origin||e.data?.channel!=='kiki-tab-adapter'||e.data.direction!=='extension')return;
  const r=pending.get(e.data.requestId);if(r){clearTimeout(r.timer);pending.delete(e.data.requestId);const error=e.data.result?.error||e.data.error;error?r.reject(Error(error)):r.resolve(e.data.result);}
  if(e.data.type==='invalidated'&&!['expired','producer_cancel','consumer_cancel'].includes(e.data.reason))void invalidate('Shared view changed',true);
  if(e.data.type==='stopped'){connection=null;identityKey=null;void invalidate('Extension disconnected');}
 });
 async function reserve(){let release;const before=mask;mask=new Promise(r=>release=r);await before;return release;}
 const sampler=new KikiWritingFrames();
 async function api(path,method='GET',body=null){const r=await fetch(path,{method,credentials:'same-origin',signal:AbortSignal.timeout(4000),...(body?{headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{})});const data=await r.json();if(!r.ok)throw Error(data.detail||'Guidance transport is unavailable');return data;}
 const path=kind=>`/lab-sessions/${lab.lab_session_id}/guidance/${kind}`;
 async function calibrate(){const start=performance.now(),r=await api(path('clock')),end=performance.now();if((end-start)/2>250)throw Error('Clock uncertainty exceeds 250 ms; live drawing is paused.');offset={upper:r.server_time_ms-start,uncertainty:(end-start)/2,sampled:end};}
 function upperNow(){if(!offset||performance.now()-offset.sampled>30000)throw Error('Drawing clock needs calibration.');return performance.now()+offset.upper;}
 let connecting=null;
 async function ensureConnection(){if(connecting)return connecting;connecting=connect();try{return await connecting;}finally{connecting=null;}}
 async function connect(){
  if(!lab?.runtime.capture_active||!captureId)return false;
  const identity=await adapter('writer_identity');if(!F.sourceMatches(track,identity))throw Error('Share the same MATLAB Chrome tab that is connected to the extension.');
  const key=JSON.stringify([lab.lab_session_id,captureId,identity.sessionId,identity.public_key]);
  if(!connection||key!==identityKey){connection=await api(path('connect'),'POST',{contract:'analysis-owned-guidance/v0.1',capture_session_id:captureId,identity});
   await adapter('writer_handshake',{negotiation:connection,lab_session_id:lab.lab_session_id});identityKey=key;high=0;epoch++;await calibrate();log('negotiated',{stream_id:connection.guidance_stream_id});}
  return true;
 }
 async function invalidate(reason,reportView=false){epoch++;active=null;queue=null;message(reason);log('invalidated',{reason});if(connection)void adapter('writer_clear',{},800).catch(()=>{});
  if(reportView&&lab)void window.KikiLab?.onViewChange(window.KikiLab.viewRevision()+1).catch(()=>{});
 }
 function setStream(stream){epoch++;track=stream?.getVideoTracks()[0]||null;sampler.setTrack(track);connection=null;identityKey=null;retained.clear();active=null;
  if(track){track.addEventListener('ended',()=>void invalidate('Sharing stopped'));track.addEventListener('capturehandlechange',()=>{connection=null;identityKey=null;void invalidate('Shared source changed',true);});}
 }
 async function prepareFrame(preview){video=preview;const release=await reserve();let held=false;
  try{if(!await ensureConnection())return null;const b=await adapter('writer_prepare');let sample;
   try{sample=await sampler.snapshot(preview,b.descriptor.freshness_probe);}catch(e){await adapter('writer_finish',{ticket_id:b.ticket_id}).catch(()=>{});throw e;}
   samples.set(b.ticket_id,{...sample,release});held=true;health.captured++;text('capture','Verified pixels from the connected tab');log('captured',{ticket_id:b.ticket_id});return b;
  }catch(e){text('capture',e.message);health.last_failure={stage:'capture',reason:e.message};log('capture_blocked',{reason:e.message});return null;}finally{if(!held)release();}
 }
 const fingerprint=(b,canvas)=>F.fingerprint(canvas,[KikiFrameProbe.exclusion(b.descriptor.freshness_probe,canvas.width,canvas.height)]);
 async function finishFrame(b,canvas){if(!b)return null;try{const r=await adapter('writer_finish',{ticket_id:b.ticket_id});if(!r.same_view)return null;
   const fp=fingerprint(b,canvas),changed=lastFP&&F.changed(fp,lastFP);lastFP=fp;if(changed&&active){await invalidate('Content changed; waiting for a fresh drawing');return null;}return b;
  }finally{const s=samples.get(b.ticket_id);s?.close();s?.release();samples.delete(b.ticket_id);}}
 async function admitFrame(b,frame,blob){if(!b)return null;try{
   const bytes=new Uint8Array(await blob.arrayBuffer());let raw='';for(let i=0;i<bytes.length;i+=8192)raw+=String.fromCharCode(...bytes.subarray(i,i+8192));
   const admitted=await adapter('writer_admit',{ticket_id:b.ticket_id,frame,jpeg:btoa(raw)},2200);
   const bitmap=await createImageBitmap(blob),reference=fingerprint(b,bitmap);bitmap.close();
   const selected={binding:b,attestation:admitted.attestation,connection_id:connection.connection_id,frame,blob,reference,received:performance.now()};retained.set(frame.frame_id,selected);
   for(const [id,v] of retained)if(retained.size>12||performance.now()-v.received>20000)retained.delete(id);
   log('frame_signed',{frame_id:frame.frame_id});return selected;
  }catch(e){text('capture',e.message);log('admission_rejected',{reason:e.message});return null;}}
 function requestHeaders(selected){const v=selected.writingBinding;if(!connection||!v||v.connection_id!==connection.connection_id)return {};
  return {'X-Guidance-Contract':'analysis-owned-guidance/v0.1','X-Guidance-Connection':connection.connection_id,'X-Guidance-Attestation':JSON.stringify(v.attestation)};}
 async function recordAck(signed,started){const ack=signed?.ack||signed;if(!ack?.ack_id)return;await api(`/lab-sessions/${ack.context.lab_session_id}/guidance/ack?connection=${encodeURIComponent(ack.guidance_stream_id)}`,'POST',{ack,signature:signed.signature||null,commit_to_paint_ms:started===null?null:performance.now()-started});log('ack_recorded',{sequence:ack.cue_sequence,status:ack.status});}
 async function cancel(c){if(!connection||c.guidance_stream_id!==connection.guidance_stream_id||c.cue_sequence<=high)return;
  high=c.cue_sequence;if(c.cue_sequence>=inflightSequence){epoch++;active=null;if(queue?.e.cue_sequence<=c.cue_sequence)queue=null;}const ack=await adapter('guidance_cancel',{cancel:c});await recordAck(ack,null);message('Guidance cleared for the current context');log('cancelled',{sequence:c.cue_sequence});}
 function receive(state){lab=state;text('analysis',state.runtime.analysis_status==='checking'?'Reading a pinned frame':state.runtime.analysis_status==='waiting_for_provider'?'Waiting for provider':state.runtime.analysis_status);
  const e=state.screen_guidance;if(!e)return Promise.resolve();queue={state,e,started:performance.now()};epoch++;
  if(!delivering)delivering=(async()=>{try{while(queue){const next=queue;queue=null;await paint(next);}}finally{delivering=null;}})();return delivering;
 }
 async function paint({state,e,started}){const token=epoch;inflightSequence=e.cue_sequence;let release;try{
   if(!connection||e.guidance_stream_id!==connection.guidance_stream_id||e.cue_sequence<=high)return;P.validate(e,state);
   const selected=retained.get(e.frame.frame_id);if(!selected||selected.frame.sha256!==e.frame.sha256)throw Error('The exact admitted frame is no longer retained.');
   if(!offset||performance.now()-offset.sampled>20000)await calibrate();
   const current=await api(path('events')+'?connection='+encodeURIComponent(connection.connection_id)+'&after='+high);
   if(current.revision!==e.context.lab_revision||current.messages.some(m=>m.cue_sequence>e.cue_sequence))throw Error('A newer context cancelled this drawing.');
   release=await reserve();const reserved=performance.now();log('presentation_reserved');
   const check=()=>{if(token!==epoch||track?.readyState!=='live'||upperNow()>=Date.parse(e.validity.expires_at)||performance.now()-reserved>=500)throw Error('Drawing expired, invalidated or exceeded its 500 ms presentation reservation.');};check();
   message('Checking live pixels before drawing');const b=await adapter('writer_prepare'),preparedAt=performance.now();let fresh;
   try{fresh=await sampler.snapshot(video,b.descriptor.freshness_probe);const canvas=document.createElement('canvas');canvas.width=fresh.width;canvas.height=fresh.height;canvas.getContext('2d').drawImage(fresh.image,0,0);
    const ignored=[b.descriptor.freshness_probe,selected.binding.descriptor.freshness_probe].map(p=>KikiFrameProbe.exclusion(p,canvas.width,canvas.height));
    if(F.changed(F.fingerprint(canvas,ignored),selected.reference))throw Error('Live content differs from the analysed frame; geometry discarded.');
   log('live_pixels_verified',{reservation_ms:performance.now()-reserved});
   }finally{fresh?.close();await adapter('writer_finish',{ticket_id:b.ticket_id}).catch(()=>{});}check();
   const remaining=Math.min(7900,Date.parse(e.validity.expires_at)-upperNow()-50);if(remaining<=0)throw Error('Drawing expired before presentation.');check();
   log('paint_requested',{reservation_ms:performance.now()-reserved});
   const signed=await adapter('guidance_commit',{envelope:e,ticket_id:selected.binding.ticket_id,ttlMs:remaining,deadline_renderer_ms:b.descriptor.clock_ms+(performance.now()-preparedAt)+remaining},Math.max(40,500-(performance.now()-reserved)));check();const ack=signed.ack;
   high=e.cue_sequence;active=e.outcome==='none'?null:e;
   if(e.outcome==='none'){message('Analysis supplied no current drawing');log('no_cue',{sequence:high});return;}
   if(!['live_rendered','text_only'].includes(ack.status))throw Error('The connected tab did not acknowledge paint.');health.painted++;health.last_failure=null;message(ack.status==='text_only'?'Current instruction painted; target unresolved':'Shapes and notes painted on your shared tab');log('paint_acknowledged',{request_id:e.analysis_request_id,sequence:high,commit_to_paint_ms:performance.now()-started});
   release();release=null;try{await recordAck(signed,started);}catch(err){log('ack_record_failed',{reason:err.message});}
  }catch(err){health.last_failure={stage:'delivery',reason:err.message};log('delivery_rejected',{request_id:e.analysis_request_id,reason:err.message});void recordAck(P.ack(e,'rejected','consumer_validation_failed'),started).catch(()=>{});if(token===epoch)await invalidate(err.message);}finally{release?.();inflightSequence=0;}}
 async function poll(){if(polling||!connection||!lab)return;polling=true;const observedConnection=connection;try{const result=await api(path('events')+'?connection='+encodeURIComponent(connection.connection_id)+'&after='+high);if(connection!==observedConnection)return;for(const m of result.messages)if(m.message_type==='cancel')await cancel(m);if(!result.active){connection=null;identityKey=null;}}catch(e){log('poll_failed',{reason:e.message});}finally{polling=false;}}
 setInterval(()=>void poll(),650);
 globalThis.KikiWriting={setStream,prepareFrame,finishFrame,admitFrame,fingerprint,requestHeaders,receive,invalidate,sample:b=>samples.get(b?.ticket_id),
  attach(state,id){lab=state;captureId=id;},context(state){lab=state;},get diagnostics(){return {schema:'guidance-consumer-trace/v1',health:structuredClone(health),events:structuredClone(events)};}};
 $('writing-check')?.addEventListener('click',async()=>{try{await ensureConnection();await calibrate();message('Source and contracts match. Waiting for a committed analysis drawing.');}catch(e){message(e.message);}});
})();
