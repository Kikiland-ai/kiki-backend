/* Pure source matching and marker-excluded visual freshness checks. */
(() => {
 function sourceMatches(track,status){
  const handle=track?.getCaptureHandle?.();if(!status?.binding?.url)return false;
  return track?.readyState==='live'&&track.getSettings().displaySurface==='browser'&&status?.mode==='live_tutor'&&
   typeof handle?.handle==='string'&&handle.handle===status.capture_handle&&handle.origin===new URL(status.binding.url).origin;
 }
 function fingerprint(canvas,ignoredRegions=[]){
  const sample=document.createElement('canvas');sample.width=256;sample.height=144;
  const ctx=sample.getContext('2d',{willReadFrequently:true});ctx.drawImage(canvas,0,0,256,144);
  const rgba=ctx.getImageData(0,0,256,144).data,values=[];
  for(let ty=0;ty<18;ty++)for(let tx=0;tx<32;tx++){
   if(ignoredRegions.some(r=>r&&tx/32<r.x+r.width&&(tx+1)/32>r.x&&ty/18<r.y+r.height&&(ty+1)/18>r.y)){values.push(null);continue;}
   let total=0;for(let y=ty*8;y<(ty+1)*8;y++)for(let x=tx*8;x<(tx+1)*8;x++){const i=(y*256+x)*4;total+=(rgba[i]+rgba[i+1]+rgba[i+2])/3;}values.push(total/64);
  }
  return values;
 }
 function changed(a,b){return !a||!b||a.length!==b.length||a.some((v,i)=>v!==null&&b[i]!==null&&Math.abs(v-b[i])>3);}
 globalThis.KikiWritingProtocol={sourceMatches,fingerprint,changed};
})();
