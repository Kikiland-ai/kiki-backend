/* A per-capture pixel challenge. Freshness comes from the source pixels, not
 * from receiving an arbitrary frame after an asynchronous message returns. */
(() => {
 const columns=16,rows=6,cell=4,schema='screen-capture-probe/v1';
 const valid=p=>p?.schema===schema&&/^[a-f0-9]{24}$/.test(p.token)&&p.columns===columns&&p.rows===rows&&
  p.region&&['x','y','width','height'].every(k=>Number.isFinite(p.region[k])&&p.region[k]>=0&&p.region[k]<=1)&&
  p.region.width>0&&p.region.height>0&&p.region.x+p.region.width<=1&&p.region.y+p.region.height<=1;
 function create(viewport){
  if(viewport.width<256||viewport.height<160)throw Error('The shared viewport is too small to verify capture.');
  const token=[...crypto.getRandomValues(new Uint8Array(12))].map(v=>v.toString(16).padStart(2,'0')).join('');
  return {schema,token,columns,rows,region:{x:(viewport.width-68)/viewport.width,y:(viewport.height-28)/viewport.height,width:64/viewport.width,height:24/viewport.height}};
 }
 const bit=(p,index)=>(parseInt(p.token[Math.floor(index/4)],16)>>(3-index%4))&1;
 function matches(image,p){
  if(!valid(p))return false;
  const width=image.displayWidth||image.videoWidth||image.naturalWidth||image.width,height=image.displayHeight||image.videoHeight||image.naturalHeight||image.height;
  if(!width||!height||width*p.region.width/columns<2||height*p.region.height/rows<2)return false;
  const canvas=typeof document==='undefined'?new OffscreenCanvas(columns*cell,rows*cell):document.createElement('canvas');canvas.width=columns*cell;canvas.height=rows*cell;
  const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.imageSmoothingEnabled=false;
  ctx.drawImage(image,p.region.x*width,p.region.y*height,p.region.width*width,p.region.height*height,0,0,canvas.width,canvas.height);
  const pixels=ctx.getImageData(0,0,canvas.width,canvas.height).data;
  for(let i=0;i<columns*rows;i++){
   const offset=((Math.floor(i/columns)*cell+2)*canvas.width+(i%columns)*cell+2)*4,expected=bit(p,i)?224:32;
   if([0,1,2].some(k=>Math.abs(pixels[offset+k]-expected)>48))return false;
  }
  return true;
 }
 function exclusion(p,width,height){if(!valid(p))return null;const r=p.region,x=Math.max(0,r.x-16/width),y=Math.max(0,r.y-16/height);
  return {x,y,width:Math.min(1,r.x+r.width+16/width)-x,height:Math.min(1,r.y+r.height+16/height)-y};}
 globalThis.KikiFrameProbe={create,valid,bit,matches,exclusion,columns,rows,cell};
})();
