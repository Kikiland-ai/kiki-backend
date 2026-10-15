/* Drawing-only command sequence. Coordinates refer to the exact sampled viewport.
   No lab identity, recognition result or checkpoint completion is invented. */
function kikiDrawingDemo(binding){
 const p=binding.cursor||{x:.48,y:.4};
 const r=Math.min(48,binding.viewport.width*.04,binding.viewport.height*.04),rx=r/binding.viewport.width,ry=r/binding.viewport.height;
 const x=Math.min(.72,Math.max(.18,p.x)),y=Math.min(.66,Math.max(.22,p.y));
 return [
  {kind:'ellipse',meaning:'lab',label:'Circle drawn on your live tab',region:{x:x-rx,y:y-ry,width:2*rx,height:2*ry}},
  {kind:'arrow',meaning:'lab',label:'Arrow pointing to the same screen location',anchors:[{x:x-.16,y:y+.12},{x,y:y+.045}]},
  {kind:'text',meaning:'lab',label:'Live annotation note',anchor:{x:x-.14,y:y+.17},text:'Kiki draws here · on your live tab'},
  {kind:'box',meaning:'concept',label:'Comparison region drawn over the live page',region:{x:x+.12,y:y-.04,width:.12,height:.10}},
  {kind:'polyline',meaning:'concept',label:'An explanatory path between screen regions',anchors:[{x:x+.055,y},{x:x+.09,y:y-.075},{x:x+.18,y:y-.075},{x:x+.18,y:y-.04}]},
  {kind:'pointer',meaning:'words',label:'Temporary pointer on the comparison region',anchor:{x:x+.18,y:y+.01}}
 ];
}
