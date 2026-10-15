/* Fresh samples from the reader's existing display track, including a hidden
 * reader page. No extension capture or second getDisplayMedia connection. */
(() => {
 class WritingFrames {
  constructor({matches=(image,probe)=>KikiFrameProbe.matches(image,probe)}={}){this.generation=0;this.latest=null;this.pending=new Set();this.reader=null;this.matches=matches;}
  stop(){this.generation++;this.reader?.cancel().catch(()=>{});this.reader=null;this.latest?.close();this.latest=null;for(const p of this.pending){clearTimeout(p.timer);p.reject(Error('Sharing changed.'));}this.pending.clear();}
  setTrack(track){
   this.stop();if(!track||!globalThis.MediaStreamTrackProcessor)return;
   try{this.reader=new MediaStreamTrackProcessor({track,maxBufferSize:1}).readable.getReader();}catch{return;}
   const reader=this.reader,token=this.generation;
   void(async()=>{try{while(token===this.generation){const {value,done}=await reader.read();if(done)break;
    if(token!==this.generation){value?.close();break;}this.latest?.close();this.latest=value;
    for(const p of this.pending){if(p.probe&&!this.matches(value,p.probe))continue;clearTimeout(p.timer);this.pending.delete(p);p.resolve(this.sample(value));}
   }}catch{}finally{if(token===this.generation){this.reader=null;for(const p of this.pending){clearTimeout(p.timer);p.reject(Error('The display track stopped supplying frames.'));}this.pending.clear();}}})();
  }
  sample(frame){const image=frame.clone();return {image,width:image.displayWidth,height:image.displayHeight,close:()=>image.close()};}
  async snapshot(video,probe=null){
   // The matching frame may already have arrived while writer_prepare awaited
   // the source compositor. A new unique challenge proves its capture order.
   if(probe&&this.latest&&this.matches(this.latest,probe))return this.sample(this.latest);
   if(this.reader)return new Promise((resolve,reject)=>{const p={resolve,reject,probe,timer:null};p.timer=setTimeout(()=>{this.pending.delete(p);reject(Error('The shared tab did not return the current capture marker.'));},2000);this.pending.add(p);});
   // Portable fallback uses media time, which can advance while the page is
   // hidden. A frozen preview is never silently treated as a current frame.
   const time=video.currentTime,token=this.generation,start=performance.now();
   while(token===this.generation&&performance.now()-start<2000){await new Promise(r=>setTimeout(r,60));
    if(video.readyState>=2&&(probe?this.matches(video,probe):video.currentTime>time)){
     if(!probe)return {image:video,width:video.videoWidth,height:video.videoHeight,close(){}};
     const image=await createImageBitmap(video);if(this.matches(image,probe))return {image,width:image.width,height:image.height,close:()=>image.close()};image.close();
    }
   }
   throw Error('The shared tab did not supply fresh pixels. Keep sharing active in Chrome.');
  }
 }
 globalThis.KikiWritingFrames=WritingFrames;
})();
