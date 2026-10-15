// Matched exact-JPEG control/drawing sample. --live makes two real provider calls;
// default uses the same controlled transport/delay. Neither arm asserts paint.
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {setupGuidance,fixtureImage} from './guidance-fixture.mjs';
const live=process.argv.includes('--live'),out=process.argv.find(v=>v.startsWith('--output='))?.slice(9)||'../../work/guidance-integration/paired';
if(live&&!process.env.GEMINI_API_KEY)throw Error('Configured runtime Gemini key is unavailable.');
await mkdir(out,{recursive:true});const records=[],outcomes=[],prior=console.info;
console.info=value=>{try{const r=JSON.parse(value);if(r.schema==='guidance-producer-timing/v1')records.push(r);}catch{}};
const fingerprint=createHash('sha256').update(await readFile('dist/server/index.js')).digest('hex');
const arms=process.argv.includes('--drawing-only')?['drawing_v1']:['control','drawing_v1'];
for(const arm of arms){
 const h=await setupGuidance();h.env.GUIDANCE_SAMPLE_KIND=live?'live_provider':'offline_replay';h.env.GUIDANCE_CONFIGURATION_ID=live?'cloud-paired-exact-jpeg-v1':'offline-paired-exact-jpeg-v1';h.env.GUIDANCE_SOURCE_REVISION=fingerprint;h.headers['X-Guidance-Pair']='matched-constant-image-v1';
 if(live){h.env.GEMINI_API_KEY=process.env.GEMINI_API_KEY;h.env.LAB_STREAM_FETCH=async(...args)=>{const response=await fetch(...args);if(!response.ok){const error=await response.clone().json().catch(()=>({}));console.log(JSON.stringify({event:'provider_schema_error',status:response.status,message:error.error?.message?.slice(0,1800)||null,details:error.error?.details||null}));}return response;};}else h.env.fixtureDelay=200;
 if(arm==='control')for(const key of ['X-Guidance-Contract','X-Guidance-Connection','X-Guidance-Attestation'])delete h.headers[key];
 try{const response=await h.check(),text=await response.text(),events=text.split('\n\n').filter(Boolean).map(v=>JSON.parse(v.slice(6))),core=events.find(e=>e.type==='guidance_committed'),waiting=events.find(e=>e.type==='analysis_waiting');outcomes.push({arm,status:core?'committed':events.at(-1)?.type||'failed',reason:events.find(e=>['analysis_failed','discarded'].includes(e.type))?.reason||waiting?.state.runtime.analysis_error||null,analysis_status:core?.state.runtime.analysis_status||waiting?.state.runtime.analysis_status,drawing_outcome:core?.state.screen_guidance?.outcome||null,provider_attempts:(core||waiting)?.state.runtime.last_analysis_timing.provider_http_attempts??null});}
 catch(e){outcomes.push({arm,status:'failed',reason:e.name});}finally{h.env.DB.close();}
}
console.info=prior;await writeFile(out+'/timings.jsonl',records.map(r=>JSON.stringify(r)).join('\n')+'\n');const report={sample_kind:live?'live_provider':'offline_replay',same_exact_jpeg_sha256:createHash('sha256').update(fixtureImage).digest('hex'),source_fingerprint:fingerprint,model:'gemini-3.5-flash-lite',calls_requested:arms.length,real_recognition_tested:false,paint_tested:false,outcomes};await writeFile(out+'/acceptance.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
if(outcomes.some(r=>r.status!=='committed'))process.exitCode=1;
