// Explicit bounded live prompt evaluation, not a paint or live Simulink test.
// Run from prototype root after build: node --use-env-proxy --use-system-ca
// scripts/evaluate-writing-prompt.mjs --live [--case CASE]
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {gzipSync} from 'node:zlib';
import {setupGuidance,seedCheckpoint} from './guidance-fixture.mjs';
import {DrawingFindingParserJS} from '../worker/guidance.js';
import {SSEDecoderJS} from '../worker/stream-core.js';
import {drawingWritingPrompt,LIVE_DRAWING_PROMPT_VERSION} from '../worker/guidance-prompt.js';
if(!process.argv.includes('--live'))throw Error('Explicit --live required; at most six model calls, no retries.');
if(!process.env.GEMINI_API_KEY)throw Error('Configured GEMINI_API_KEY required.');
const root=new URL('../../../',import.meta.url),out=new URL('work/writing-prompt-evaluation/',root);await mkdir(out,{recursive:true});
const policy=JSON.parse(await readFile(new URL('../data/guided-policy.json',import.meta.url))),definition=JSON.parse(await readFile(new URL('../data/experiment.json',import.meta.url)));
const cases=[
 {id:'gain-visible',split:'development',checkpoint:'CP-DSB-06',action:'gain-settings',image:'docs/experiments/analysis-owned-guidance/generated-marks-v1-evidence/controlled-query-image.jpeg',mode:'annotate',boxes:{'recovery_gain.value':{x:188/1200,y:380/800,width:488/1200,height:50/800}}},
 {id:'gain-hidden',split:'development',checkpoint:'CP-DSB-06',action:'gain-settings',image:'fixtures/json-stream/clear-wires-heldout.jpg',mode:'text_only'},
 {id:'two-fields-wrong-phase',split:'held_out_for_this_prompt_change',checkpoint:'CP-DSB-05',action:'local-settings',image:'fixtures/screen-reader-baseline/wrong-local-phase-heldout.jpg',mode:'annotate',finding:'mismatch',boxes:{'local_carrier.frequency':{x:51/1200,y:528/820,width:480/1200,height:35/820},'local_carrier.phase':{x:51/1200,y:602/820,width:480/1200,height:35/820}}}
];
const selected=process.argv.includes('--case')?process.argv[process.argv.indexOf('--case')+1]:null;if(selected&&!cases.some(c=>c.id===selected))throw Error('Unknown case');
const hash=value=>createHash('sha256').update(typeof value==='string'||Buffer.isBuffer(value)?value:JSON.stringify(value)).digest('hex');
const iou=(a,b)=>{const n=Math.max(0,Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x))*Math.max(0,Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y));return n/(a.width*a.height+b.width*b.height-n);};
const rows=[];const info=console.info;console.info=()=>{};
for(const [index,c] of cases.entries()){
 if(selected&&selected!==c.id)continue;
 const h=await setupGuidance();let prepared;
 try{
  const s=await seedCheckpoint(h.env,h.state,c.checkpoint),procedure=policy.procedures[c.checkpoint],at=procedure.findIndex(a=>a.id===c.checkpoint+'/'+c.action),visit=s.steps.find(v=>v.checkpoint_id===c.checkpoint).current_visit_id;
  s.procedure_history=Object.fromEntries(procedure.slice(0,at).map(a=>[a.id,{count:2,scope:{visit_id:visit,workspace_id:s.workspace.id,capture_epoch:s.workspace.capture_epoch,parameter_revision:s.workspace.parameter_revision,condition:s.workspace.condition},last_seen_ms:Date.now(),last_evidence:'Explicit evaluation setup precondition.'}]));
  await h.env.DB.prepare('UPDATE lab_sessions SET state_json=? WHERE id=?').bind(JSON.stringify(s),s.lab_session_id).run();
  const original=h.env.LAB_STREAM_FETCH;h.env.LAB_STREAM_FETCH=(url,options)=>{prepared=JSON.parse(options.body);return original(url,options);};await(await h.check()).text();
 }finally{h.env.DB.close();}
 if(!prepared)throw Error('Production request preparation failed');
 const actions=JSON.parse(prepared.contents[0].parts[0].text.split('\nAuthored drawing catalogue: ')[1]),cp=definition.checkpoints.find(cp=>cp.id===c.checkpoint),current=c.checkpoint+'/'+c.action;
 if(actions[0].action_id!==current)throw Error('Fixture selected wrong action');
 const pixels=await readFile(new URL(c.image,root));prepared.contents[0].parts[1].inlineData.data=pixels.toString('base64');
 const suffix=drawingWritingPrompt(actions);if(!prepared.systemInstruction.parts[0].text.endsWith(suffix))throw Error('Prompt suffix mismatch');
 const baseline=structuredClone(prepared);baseline.systemInstruction.parts[0].text=baseline.systemInstruction.parts[0].text.slice(0,-suffix.length);
 for(const arm of index%2?['candidate','baseline']:['baseline','candidate']){
  const body=arm==='baseline'?baseline:prepared,started=performance.now(),row={case:c.id,split:c.split,arm,prompt_version:arm==='baseline'?'dsb-step-observer/v5-drawing1':LIVE_DRAWING_PROMPT_VERSION,sample_kind:'live_provider',source_kind:'controlled_screenshot_fixture',image:c.image,image_sha256:hash(pixels),schema_sha256:hash(body.generationConfig.responseJsonSchema),input_sha256:hash(body.contents),model:'gemini-3.5-flash-lite',timeout_ms:20000,retries:0,paint_tested:false,real_simulink_tested:false,request_characters:JSON.stringify(body).length-pixels.toString('base64').length};
  try{
   const response=await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${row.model}:streamGenerateContent?alt=sse`,{method:'POST',headers:{'Content-Type':'application/json','x-goog-api-key':process.env.GEMINI_API_KEY},body:JSON.stringify(body),signal:AbortSignal.timeout(row.timeout_ms)});row.http_status=response.status;row.headers_ms=Math.round(performance.now()-started);
   const decoder=new SSEDecoderJS(),parser=new DrawingFindingParserJS(cp,policy.procedures[cp.id],{eligible_actions:actions});let stopped=false,raw='';const reader=response.body.getReader();
   if(!response.ok){await reader.cancel();throw Error('provider_http_'+response.status);}
   while(true){const chunk=await reader.read();if(chunk.done)break;if(row.first_byte_ms===undefined)row.first_byte_ms=Math.round(performance.now()-started);raw+=new TextDecoder().decode(chunk.value);for(const data of decoder.feed(chunk.value)){if(data==='[DONE]')continue;const value=JSON.parse(data);if(value.usageMetadata)row.tokens=value.usageMetadata;for(const item of value.candidates||[]){parser.feed((item.content?.parts||[]).filter(p=>!p.thought).map(p=>p.text||'').join(''));if(item.finishReason){if(item.finishReason!=='STOP')throw Error('finish_'+item.finishReason);stopped=true;}}}}
   await writeFile(new URL(`${c.id}.${arm}.response.txt.gz`,out),gzipSync(raw));decoder.finish();if(!stopped)throw Error('missing_STOP');
   await writeFile(new URL(`${c.id}.${arm}.model.json`,out),parser.text);const value=parser.finish();row.contract_valid=true;const candidate=value.screen_guidance.find(a=>a.action_id===current);row.outcome=candidate?.mode||'omitted';row.mark_kinds=candidate?.marks.map(m=>m.kind)||[];
   row.expected_mode=c.mode;row.mode_correct=row.outcome===c.mode;row.target_iou=Object.fromEntries(Object.entries(c.boxes||{}).map(([id,box])=>[id,candidate?.targets.find(t=>t.target_id===id)?.region?iou(candidate.targets.find(t=>t.target_id===id).region,box):0]));
   if(c.finding){row.expected_finding=c.finding;row.actual_finding=value.action_findings.find(a=>a.action_id===current)?.status;}
   row.pass=row.mode_correct&&Object.values(row.target_iou).every(v=>v>=.5)&&(!c.finding||row.actual_finding===c.finding);
  }catch(error){row.pass=false;row.error=error.name==='TimeoutError'?'provider_timeout':error.message;}
  row.elapsed_ms=Math.round(performance.now()-started);rows.push(row);await writeFile(new URL('results.json',out),JSON.stringify(rows,null,2)+'\n');info(JSON.stringify(row));
 }
 const pair=rows.filter(r=>r.case===c.id);if(pair[0].schema_sha256!==pair[1].schema_sha256||pair[0].input_sha256!==pair[1].input_sha256)throw Error('A/B changed schema or source input');
}
console.info=info;
