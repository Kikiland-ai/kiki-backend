let stream=null,timer=null,generation=0;const video=document.querySelector('video'),canvas=document.createElement('canvas');
const send=m=>chrome.runtime.sendMessage({to:'background',...m});
const paint=()=>new Promise((r,reject)=>{const timer=setTimeout(()=>reject(Error('No fresh video frame while guidance is masked')),1500);video.requestVideoFrameCallback(()=>{clearTimeout(timer);r();});});
async function stop(){generation++;clearTimeout(timer);stream?.getTracks().forEach(t=>t.stop());stream=null;video.srcObject=null;}
async function tick(g){if(g!==generation||!stream)return;let ticket;try{
 ticket=await send({type:'prepare'});if(!ticket||ticket.error){await stop();await send({type:'source_ended'});return;}
 // Two freshly composited video frames exclude the annotation layer before encoding.
 await paint();await paint();if(g!==generation)return;
 const scale=Math.min(1,1600/Math.max(video.videoWidth,video.videoHeight));canvas.width=Math.round(video.videoWidth*scale);canvas.height=Math.round(video.videoHeight*scale);
 if(!canvas.width||!canvas.height)throw Error('No source pixels');
 canvas.getContext('2d').drawImage(video,0,0,canvas.width,canvas.height);
 const blob=await new Promise(r=>canvas.toBlob(r,'image/jpeg',.8));if(!blob||blob.size>1000000)throw Error('Capture exceeds 1 MB');
 const bytes=await blob.arrayBuffer(),hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
 const dataUrl=await new Promise(r=>{const f=new FileReader();f.onload=()=>r(f.result);f.readAsDataURL(blob);});
 if(g===generation){const result=await send({type:'frame',ticket,width:canvas.width,height:canvas.height,sourceWidth:video.videoWidth,sourceHeight:video.videoHeight,byteCount:blob.size,sha256:hash,dataUrl,capturedElapsedMs:performance.now()});if(!result?.ok)throw Error(result?.error||'Frame broker did not admit the pixels');}
 }catch(e){await send({type:'capture_error',error:e.message,videoState:{readyState:video.readyState,width:video.videoWidth,height:video.videoHeight,currentTime:video.currentTime}});}finally{if(ticket)await send({type:'finish',ticket});if(g===generation&&stream)timer=setTimeout(()=>tick(g),2000);}}
chrome.runtime.onMessage.addListener((m,s,reply)=>{if(m.to!=='offscreen')return;void(async()=>{
 if(m.type==='stop'){await stop();return {ok:true};}
 if(m.type==='start'){await stop();const g=generation;stream=await navigator.mediaDevices.getUserMedia({audio:false,video:{mandatory:{chromeMediaSource:'tab',chromeMediaSourceId:m.streamId}}});video.srcObject=stream;await video.play();stream.getVideoTracks()[0].onended=()=>send({type:'source_ended'});void tick(g);return {ok:true};}
 })().then(reply,e=>reply({error:e.message}));return true;});
