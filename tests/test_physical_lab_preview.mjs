import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {PreparationClient} from '../prototypes/physical_labs/static/preparation-client.mjs';
import {ApparatusViewer,defaultCamera,projectPoint,pickPart,clampPanel,guidePosition} from '../prototypes/physical_labs/static/apparatus-viewer.mjs';
import {componentHint,tooltipPosition} from '../prototypes/physical_labs/static/component-hints.mjs';

const root=new URL('../prototypes/physical_labs/',import.meta.url);
const pack=JSON.parse(await readFile(new URL('packs/dsb-sc-trainer.json',root),'utf8'));
const gltf=JSON.parse(await readFile(new URL(`assets/${pack.asset}`,root),'utf8'));

test('rapid part clicks are all saved in order with fresh revisions',async()=>{
  let serverRevision=0;const targets=[];
  const api=async(path,options)=>{const event=JSON.parse(options.body);await new Promise(r=>setTimeout(r,2));assert.equal(event.revision,serverRevision);targets.push(event.target);return{session_id:'test',revision:++serverRevision};};
  let id=0;const client=new PreparationClient(api,()=>{},()=>`event-${id++}`);client.use({session_id:'test',revision:0});
  await Promise.all(pack.orientation.map(target=>client.event('select',{target})));
  assert.deepEqual(targets,pack.orientation);assert.equal(client.state.revision,pack.orientation.length);assert.equal(client.pending,0);
});

test('a rejected event does not block subsequent actions or advance the local revision',async()=>{
  const revisions=[];const client=new PreparationClient(async(path,options)=>{const e=JSON.parse(options.body);revisions.push(e.revision);if(e.target==='reject')throw Error('Rejected');return{session_id:'test',revision:e.revision+1};},()=>{},()=>String(Math.random()));
  client.use({session_id:'test',revision:0});const first=client.event('select',{target:'reject'});const second=client.event('advance');await assert.rejects(first,/Rejected/);await second;assert.deepEqual(revisions,[0,0]);assert.equal(client.state.revision,1);
});

test('instrument picking resolves physical parts at the same projection used for drawing',()=>{
  const camera=defaultCamera();for(const id of ['source.message','modulator.null','detector.reference','scope.input']){const part=pack.parts.find(p=>p.id===id);const p=projectPoint(part.position,camera,1100,600);assert.equal(pickPart(pack.parts,camera,1100,600,p[0],p[1]).id,id);}
  assert.equal(pickPart(pack.parts,camera,1100,600,-100,-100),null);
});

test('refined glTF renders actual meshes and printed labels without a WebGL dependency',()=>{
  const calls={fill:0,text:[]};const gradient={addColorStop(){}};
  const context=new Proxy({}, {get(target,key){if(key==='createLinearGradient')return()=>gradient;if(key==='fillText')return text=>calls.text.push(text);if(key==='fill')return()=>calls.fill++;return()=>{};},set(target,key,value){target[key]=value;return true;}});
  const canvas={clientWidth:1100,clientHeight:600,getContext:kind=>{assert.equal(kind,'2d');return context;},addEventListener(){}};
  globalThis.ResizeObserver=class{observe(){}};globalThis.requestAnimationFrame=()=>1;globalThis.devicePixelRatio=1;
  const viewer=new ApparatusViewer(canvas);viewer.load(gltf,pack);viewer.controls={'trainer.power':true,'source.message_frequency':1000};viewer.draw();
  assert.ok(calls.fill>100,'draw physical mesh surfaces');assert.ok(calls.text.includes('BALANCED MODULATOR'));assert.ok(calls.text.includes('SYNCHRONOUS DETECTOR'));assert.ok(calls.text.includes('MC1496'));
  assert.ok(gltf.nodes.filter(n=>n.extras?.decorative).length>150,'physical component detail');
  const before=projectPoint([0,0,0],viewer.camera,1100,600);viewer.view('scope');const after=projectPoint([0,0,0],viewer.camera,1100,600);assert.notDeepEqual(before,after);
});

test('floating guide moves clear of the active sockets',()=>{
  const points=[[480,300],[1060,520]],size=[340,480];
  const [x,y]=guidePosition(points,1440,850,...size,[1088,20]);
  assert.ok(points.every(([px,py])=>!(px>x-30&&px<x+size[0]+30&&py>y-30&&py<y+size[1]+30)));
});

test('dragged guide stays inside the fullscreen workspace',()=>{
  assert.deepEqual(clampPanel(-500,-100,1440,850,340,480),[8,8]);
  assert.deepEqual(clampPanel(5000,5000,1440,850,340,480),[1092,362]);
});

test('CRO displays the backend trace for its actual probe connection',()=>{
  const paths=[];let path=[];
  const ctx={save(){},restore(){},beginPath(){path=[];},moveTo(x,y){path.push([x,y]);},lineTo(x,y){path.push([x,y]);},stroke(){paths.push({color:this.strokeStyle,points:[...path]});}};
  const viewer=Object.create(ApparatusViewer.prototype);viewer.ctx=ctx;viewer.parts=pack.parts;viewer.project=p=>p;viewer.controls={'trainer.power':true};
  viewer.observation={traces:{dsb_sc_v:[1,0,-1],recovered_v:[.5,-.5]}};
  viewer.connections=[['modulator.output','scope.input']];viewer.screen();
  assert.equal(paths.at(-1).points.length,3);assert.equal(paths.at(-1).color,'#a5dc8d');
  viewer.connections=[['detector.output','scope.input']];viewer.screen();
  assert.equal(paths.at(-1).points.length,2);
  paths.length=0;viewer.connections=[];viewer.screen();
  assert.equal(paths.filter(p=>p.color==='#a5dc8d').length,0);
});

const firstLead={kind:'connect',target:'source.message',other:'modulator.message'};
test('hover identifies the numbered source and the exact destination',()=>{
  const hint=componentHint(pack.parts.find(p=>p.id==='source.message'),pack.parts,firstLead,null,1);
  assert.equal(hint.title,'#1 Message output');assert.equal(hint.detail,'Signal source · Output socket');
  assert.match(hint.cue,/#3 Message input/);assert.equal(hint.current,true);assert.equal(hint.step,'Step 1');
});

test('destination hover follows the selected source without changing experiment state',()=>{
  const part=pack.parts.find(p=>p.id==='modulator.message');
  const before=componentHint(part,pack.parts,firstLead,null,1);
  const selected=componentHint(part,pack.parts,firstLead,'source.message',1);
  const incorrect=componentHint(part,pack.parts,firstLead,'source.carrier',1);
  assert.match(before.cue,/#1 Message output/);assert.match(selected.cue,/finish this lead/);
  assert.match(incorrect.cue,/#1 Message output/);assert.equal(selected.title,'#3 Message input');
});

test('an unrelated numbered socket still shows its own name and the current route',()=>{
  const hint=componentHint(pack.parts.find(p=>p.id==='source.carrier'),pack.parts,firstLead);
  assert.equal(hint.title,'#2 Carrier output');assert.equal(hint.current,false);
  assert.match(hint.cue,/#1 Message output.*#3 Message input/);
});

test('cursor tooltip flips at workspace edges and remains within fullscreen bounds',()=>{
  assert.deepEqual(tooltipPosition(500,300,1000,600,250,110),[517,317]);
  const [x,y]=tooltipPosition(990,590,1000,600,250,110);
  assert.ok(x>=8&&y>=8&&x+250<990&&y+110<590);
  assert.deepEqual(tooltipPosition(2,2,1000,600,250,110),[19,19]);
});

test('mesh hover supplies mouse coordinates and never performs a lab action',()=>{
  const listeners={},hovered=[];let picks=0;
  globalThis.ResizeObserver=class{observe(){}};
  const canvas={clientWidth:1100,clientHeight:600,getContext:()=>({}),getBoundingClientRect:()=>({left:80,top:120}),addEventListener:(name,fn)=>listeners[name]=fn};
  const viewer=new ApparatusViewer(canvas,{onHover:(p,e)=>hovered.push([p,e]),onPick:()=>picks++});viewer.parts=pack.parts;
  const part=pack.parts.find(p=>p.id==='source.message'),point=projectPoint(part.position,viewer.camera,1100,600),event={clientX:point[0]+80,clientY:point[1]+120};
  viewer.pointerMove(event);assert.equal(hovered.at(-1)[0].id,part.id);assert.equal(hovered.at(-1)[1],event);
  listeners.pointerleave(event);assert.equal(hovered.at(-1)[0],null);assert.equal(picks,0);
});
