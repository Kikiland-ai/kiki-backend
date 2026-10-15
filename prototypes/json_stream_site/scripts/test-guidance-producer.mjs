import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
import {DrawingRunJS,DrawingFindingParserJS,buildCommittedDrawing,validateDrawingModel} from '../worker/guidance.js';
const base=new URL('../../../docs/architecture/examples/analysis-owned-guidance/v0.1/',import.meta.url);
const load=async name=>JSON.parse(await readFile(new URL(name,base),'utf8'));
const definition=JSON.parse(await readFile(new URL('../data/experiment.json',import.meta.url))),policy=JSON.parse(await readFile(new URL('../data/guided-policy.json',import.meta.url)));
const input=await load('input.single.json'),model=await load('model.single.json'),cp=definition.checkpoints.find(c=>c.id==='CP-DSB-03'),actions=policy.procedures[cp.id];
const pixels=new Uint8Array(Buffer.from(await readFile(new URL('frame.jpeg.b64',base),'utf8'),'base64'));
function runtime(r){r.cue_sequence=1;r.canonical_instruction=r.eligible_actions.find(a=>a.action_id===r.current_action_id).canonical_instruction;return r;}
for(const name of ['single','comparison','action-advance','none','declined','text-only','multi-unresolved'])test('Worker typed projection '+name,async()=>{
 const source=name==='action-advance'?name:['comparison','multi-unresolved'].includes(name)?'comparison':'single',a=await load('input.'+source+'.json'),m=await load('model.'+name+'.json'),r=runtime(await load('trusted.'+source+'.json'));
 const result=buildCommittedDrawing(a,m,r),expected=await load('committed.'+name+'.json');assert.equal(result.outcome,expected.outcome);assert.deepEqual(result.packet?.operations,expected.packet?.operations);assert.deepEqual(result.text_bindings,expected.text_bindings);
});
test('new parser accepts bytewise four fields and rejects dangerous malformed tails',()=>{
 const text=JSON.stringify(model),p=new DrawingFindingParserJS(cp,actions,input);for(const char of text)p.feed(char);assert.deepEqual(JSON.parse(JSON.stringify(p.finish())),model);
 for(const bad of [text.slice(0,-1),text+'{}',text.replace('"x":0.2','"x":1e309'),text.replace('"cue_id":"note"','"cue_id":"focus-0"'),text.replace('"text_ref":"canonical_instruction"','"text_ref":"foreign"'),text.replace('"mode":"annotate"','"mode":"text_only"'),text.replace('"x":0.2','"x":0.99')])assert.throws(()=>{const p=new DrawingFindingParserJS(cp,actions,input);p.feed(bad);p.finish();});
});
test('input pins exact JPEG and versioned provider schema',async()=>{
 const run=new DrawingRunJS(input),body={generationConfig:{},systemInstruction:{parts:[{text:'control'}]},contents:[{parts:[{text:'control'}]}]};
 await run.extendRequest(body,pixels,cp,actions,input.admitted_context);
 assert.deepEqual(Object.keys(body.generationConfig.responseJsonSchema.properties),['criteria','action_findings','uncertainties','screen_guidance']);assert.equal(body.generationConfig.responseJsonSchema.properties.criteria.minItems,2);
 await assert.rejects(()=>run.extendRequest(body,pixels,cp,actions,input.admitted_context),/reused/);
 const foreign=new Uint8Array(pixels);foreign[30]^=1;await assert.rejects(()=>new DrawingRunJS(input).extendRequest(body,foreign,cp,actions,input.admitted_context),/foreign_frame_pixels/);
});
test('stale view/condition/provenance and missing live proof reject entire packet',async()=>{
 for(const key of ['view_revision','parameter_revision','condition']){const r=runtime(await load('trusted.single.json'));r.current_context[key]=key==='condition'?'phase_fault':99;assert.throws(()=>buildCommittedDrawing(input,model,r),/stale/);}
 const live=structuredClone(input);live.source_binding.surface='live_workspace';live.source_binding.transform_revision=1;const r=runtime(await load('trusted.single.json'));r.source_binding=live.source_binding;assert.throws(()=>buildCommittedDrawing(live,model,r),/unverified_live/);
});
test('actual Worker stream uses one request and holds drawing behind full STOP',async()=>{
 const run=new DrawingRunJS(input),events=[],metrics={provider_chunks:0};let requests=0;
 const context={lab_session_id:input.admitted_context.lab_session_id,experiment_id:'PR-AM-DSB',revision:7,steps:[{checkpoint_id:cp.id,current_visit_id:input.admitted_context.visit_id,criteria:[]}],workspace:{id:input.admitted_context.workspace_id,capture_epoch:1,view_revision:4,parameter_revision:2,condition:'baseline'},runtime:{answers:[]}};
 const source=await readFile(new URL('../worker/stream.js',import.meta.url),'utf8'),core=(await readFile(new URL('../worker/stream-core.js',import.meta.url),'utf8')).replace(/export \{[^}]+\};/,'');
 const analysis=(await readFile(new URL('../worker/analysis.js',import.meta.url),'utf8')).replace(/export \{[^}]+\};/,'');
 const sandbox={Date,TextEncoder,TextDecoder,console,structuredClone,AbortController,GUIDED_POLICY:policy,LAB_DEFINITION:definition,btoa:s=>Buffer.from(s,'binary').toString('base64'),checkpoint:()=>cp,fetch:()=>{throw Error('no network');},providerRequest:async(env,m,body,fetcher,opts)=>{
  requests++;assert.ok(body.generationConfig.responseJsonSchema.properties.screen_guidance);await opts.reset();let release;const wait=new Promise(r=>{release=r;});let reads=0;
  const text=JSON.stringify(model),cut=text.indexOf(',"screen_guidance"');const sse=(text,stop)=>new TextEncoder().encode('data: '+JSON.stringify({candidates:[{content:{parts:[{text}]},...(stop?{finishReason:stop}:{})}]})+'\n\n');
  const response={body:{getReader:()=>({read:async()=>{reads++;if(reads===1)return {value:sse(text.slice(0,cut)),done:false};if(reads===2){assert.equal(run.model,null);assert.ok(events.some(e=>e.type==='provisional_findings'));release();await wait;return {value:sse(text.slice(cut),'STOP'),done:false};}return {done:true};},cancel:async()=>{}})}};
  return opts.consume(response);
 }};
 vm.createContext(sandbox);vm.runInContext(core+'\n'+analysis+'\n'+source+'\nglobalThis.runStream=analyzeLabFrameStream;',sandbox);
 const emit=Object.assign(async event=>events.push(event),{metrics,signal:new AbortController().signal,batch:async list=>events.push(...list)});
 const result=await sandbox.runStream(pixels,cp,context,{},emit,run);assert.equal(requests,1);assert.equal(result.timing.wire_format,'lab-observer-drawing/v1');assert.ok(result.timing.provider_stop_ms>=0);assert.equal(result.result.screen_guidance,undefined);assert.deepEqual(JSON.parse(JSON.stringify(run.model)),model);
});
