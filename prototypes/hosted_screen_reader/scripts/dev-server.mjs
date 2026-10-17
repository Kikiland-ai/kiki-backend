// Local QA only. Production identity is injected by private Sites dispatch.
import http from 'node:http';
import {readFile} from 'node:fs/promises';
import {randomBytes} from 'node:crypto';
import worker from '../dist/server/index.js';
import {localDB} from './local-db.mjs';
const env = {CAPTURE_RECEIPT_KEY: randomBytes(32).toString('hex'), DB:localDB('work/lab-preview.sqlite')};
// Explicit local-only deterministic provider for latency/failure UI checks.
if (process.argv.includes('--analysis-fixture')) {
  env.GEMINI_API_KEY = 'local-fixture-only';
  if(process.argv.includes('--quota-fixture'))await env.DB.prepare('DELETE FROM provider_cooldowns').run();
  let quotaInjected=false;
  env.LAB_ANALYSIS_FETCH=async(url,options)=>{
    const body=JSON.parse(options.body),context=JSON.parse(body.contents[0].parts[0].text);
    if(process.argv.includes('--quota-fixture')&&context.checkpoint.id==='CP-DSB-02'&&!quotaInjected){quotaInjected=true;return new Response('',{status:429,headers:{'Retry-After':'15'}});}
    await new Promise(resolve=>setTimeout(resolve,1200));
    if(process.argv.includes('--receiver-fixture')&&context.checkpoint.id==='CP-DSB-05'){
     const scene=(await readFile('work/receiver-scene.txt','utf8')).trim(),levels={carrier:0,local:1,configured:2,product:3,modulated:4,wired:5},level=levels[scene]||0;
     return Response.json({candidates:[{finishReason:'STOP',content:{parts:[{text:JSON.stringify({summary:level?'The controlled Local carrier fixture is visible.':'The Carrier dialog shows frequency 2*pi*2000 and phase pi/2.',criteria:context.checkpoint.completion_criteria.map((c,i)=>({criterion_id:c.id,status:(i===0&&level>=2)||(i===1&&level>=5)?'match':'unknown',evidence:'Controlled fixture, not real recognition.'})),action_findings:context.procedure.map((a,i)=>({action_id:a.id,status:level>=i+1?'match':'unknown',evidence:'Controlled fixture, not real recognition.'})),uncertainties:[]})}]}}]});
    }
    return Response.json({candidates:[{finishReason:'STOP',content:{parts:[{text:JSON.stringify({summary:'Controlled Simulink-shaped fixture for lab isolation tests.',criteria:context.checkpoint.completion_criteria.map(c=>({criterion_id:c.id,status:process.argv.includes('--guided-fixture')&&context.checkpoint.id==='CP-DSB-02'?'match':'unknown',evidence:'Controlled local fixture; not actual recognition.'})),action_findings:context.procedure.map(a=>({action_id:a.id,status:context.checkpoint.id==='CP-DSB-01'&&a.id.endsWith('/create')?'match':'unknown',evidence:'Controlled named workspace fixture.'})),uncertainties:['This is an explicit local provider mock.']})}]}}]});
  };
  let calls = 0;
  env.ANALYSIS_FETCH = async () => {
    calls++;
    if (calls === 2) return new Response('Controlled fixture failure', {status:503});
    await new Promise(resolve => setTimeout(resolve,6000));
    return Response.json({candidates:[{finishReason:'STOP',content:{parts:[{text:JSON.stringify({
      summary:'Controlled fixture analysis: oscillator controls are visible.',
      facts:['Control voltage reads -0.5 V.','Output frequency reads 950 Hz.'],changes:'',uncertainties:[],
    })}]}}]});
  };
}
http.createServer(async (req, res) => {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  const headers = new Headers(req.headers);
  headers.set('oai-authenticated-user-id', 'local-fixture-user');
  const request = new Request('http://localhost:8870'+req.url, {method:req.method,headers,
    ...(req.method === 'GET' ? {} : {body:Buffer.concat(chunks)})});
  const result = await worker.fetch(request,env);
  res.writeHead(result.status,Object.fromEntries(result.headers));
  res.end(Buffer.from(await result.arrayBuffer()));
}).listen(8870,'127.0.0.1',() => console.log('Local hosted-adapter QA at http://localhost:8870'));
