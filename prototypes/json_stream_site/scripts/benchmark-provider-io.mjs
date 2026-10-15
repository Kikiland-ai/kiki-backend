// Reproducible DB-latency simulation. No network, credentials or learner state.
import {performance} from 'node:perf_hooks';
import {writeFile,mkdir} from 'node:fs/promises';
import {dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {providerRequest} from '../worker/provider.js';
import {localDB} from './local-db.mjs';
const median=values=>{const a=[...values].sort((a,b)=>a-b);return (a[Math.floor((a.length-1)/2)]+a[Math.ceil((a.length-1)/2)])/2;};
export async function benchmarkProviderIO({rttMs=20,repeats=3,keyCount=4}={}){
 if(!Number.isInteger(rttMs)||rttMs<0||rttMs>100||!Number.isInteger(repeats)||repeats<1||repeats>10||!Number.isInteger(keyCount)||keyCount<1||keyCount>16)throw Error('Invalid bounded benchmark configuration');
 const records=[];
 for(let i=0;i<repeats;i++)for(const mode of i%2?['batched','serial']:['serial','batched']){
  const db=localDB(),counts={before_http:0,total:0};let dispatched=false,metrics;
  const delayed=async action=>{counts.total++;if(!dispatched)counts.before_http++;if(rttMs)await new Promise(resolve=>setTimeout(resolve,rttMs));return action();};
  const wrap=statement=>({bind(...values){return wrap(statement.bind(...values));},first(){return delayed(()=>statement.first());},run(){return delayed(()=>statement.run());},all(){return delayed(()=>statement.all());}});
  const env={DB:{prepare(sql){return wrap(db.prepare(sql));}},KIKI_PROVIDER_IO:mode,GEMINI_API_KEYS:JSON.stringify(Array.from({length:keyCount},(_,i)=>'fixture-'+i))};
  const started=performance.now();try{
   const value=await providerRequest(env,'fixture-model',{},async()=>{dispatched=true;return Response.json({fixture:true});},{signal:new AbortController().signal,async reset(){},async consume(response){return response.json();},onMetrics(value){metrics=value;}});
   if(value.fixture!==true)throw Error('Fixture result changed');
   const expected=mode==='serial'?3*keyCount+5:4;
   if(counts.total!==expected||metrics.provider_db_operations!==expected)throw Error('Unexpected database round trips');
   records.push({arm:mode,iteration:i+1,elapsed_ms:Math.round(performance.now()-started),db_operations:counts.total,before_http_operations:counts.before_http,metrics,status:'passed'});
  }finally{db.close();}
 }
 return {schema:'provider-io-benchmark/v1',kind:'simulated_database_latency_not_production',paid_model_calls:0,key_count:keyCount,injected_rtt_ms:rttMs,repeats,records,summary:Object.fromEntries(['serial','batched'].map(mode=>{const rows=records.filter(r=>r.arm===mode);return [mode,{median_elapsed_ms:median(rows.map(r=>r.elapsed_ms)),db_operations:rows[0].db_operations,before_http_operations:rows[0].before_http_operations}];})),passed:records.every(r=>r.status==='passed')};
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
 const arg=(name,fallback)=>{const i=process.argv.indexOf(name);return i<0?fallback:process.argv[i+1];};
 const output=arg('--output','work/provider-io-benchmark.json');const result=await benchmarkProviderIO({rttMs:Number(arg('--rtt-ms','20')),repeats:Number(arg('--repeats','3'))});await mkdir(dirname(output),{recursive:true});await writeFile(output,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({passed:result.passed,summary:result.summary,kind:result.kind,report:output}));
}
