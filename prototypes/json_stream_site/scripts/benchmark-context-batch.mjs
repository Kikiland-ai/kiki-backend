// Controlled context-read latency, not production inference or user performance.
import assert from 'node:assert/strict';
import {performance} from 'node:perf_hooks';
import {mkdir,writeFile} from 'node:fs/promises';
import {dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {streamContextBatch} from '../worker/context-batch.js';
const median=values=>{const a=[...values].sort((x,y)=>x-y);return(a[Math.floor((a.length-1)/2)]+a[Math.ceil((a.length-1)/2)])/2;};
export async function benchmarkContextBatch({rttMs=20,repeats=3}={}){
 if(!Number.isInteger(rttMs)||rttMs<0||rttMs>350||!Number.isInteger(repeats)||repeats<1||repeats>5)throw Error('Invalid bounded context benchmark');
 const events=Array.from({length:7},(_,i)=>({type:'provisional_findings',id:i})),records=[];
 for(const chunks of [1,3,7])for(let iteration=0;iteration<repeats;iteration++)for(const mode of iteration%2?['per_chunk','per_event']:['per_event','per_chunk']){
  const shown=[],gate=streamContextBatch({mode,signal:new AbortController().signal,read:async()=>{if(rttMs)await new Promise(r=>setTimeout(r,rttMs));return {current:true};},valid:s=>s.current,push:e=>shown.push(e)}),started=performance.now();
  for(let i=0;i<chunks;i++)await gate.batch(events.slice(Math.floor(i*7/chunks),Math.floor((i+1)*7/chunks)));
  assert.deepEqual(shown,events);assert.equal(gate.metrics.context_db_reads,mode==='per_event'?7:chunks);
  records.push({mode,chunks,iteration:iteration+1,elapsed_ms:Math.round(performance.now()-started),...gate.metrics,passed:true});
 }
 return {schema:'stream-context-benchmark/v1',kind:'simulated_context_database_latency_not_production',paid_model_calls:0,rtt_ms:rttMs,repeats,event_count:7,records,summary:[1,3,7].map(chunks=>({chunks,...Object.fromEntries(['per_event','per_chunk'].map(mode=>{const r=records.filter(v=>v.mode===mode&&v.chunks===chunks);return [mode,{median_ms:median(r.map(x=>x.elapsed_ms)),reads:r[0].context_db_reads}];}))})),passed:true};
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
 const arg=(n,d)=>{const i=process.argv.indexOf(n);return i<0?d:process.argv[i+1];},output=arg('--output','work/context-benchmark.json');
 const result=await benchmarkContextBatch({rttMs:Number(arg('--rtt-ms','20')),repeats:Number(arg('--repeats','3'))});await mkdir(dirname(output),{recursive:true});await writeFile(output,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({passed:true,summary:result.summary,report:output}));
}
