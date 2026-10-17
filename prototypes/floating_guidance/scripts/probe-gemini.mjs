// Gemini key probe for the live local lab. Reads the key inside this process
// (env file or environment) and never prints it. Makes one free model lookup
// and ONE small paid streaming vision call on the reader's model.
//   node prototypes/floating_guidance/scripts/probe-gemini.mjs --env-file <path> [--model gemini-3.5-flash-lite]
import {readFileSync} from 'node:fs';
const arg=name=>{const i=process.argv.indexOf(name);return i<0?null:process.argv[i+1];};
const model=arg('--model')||process.env.GEMINI_LAB_MODEL||'gemini-3.5-flash-lite';
function loadKey(){
 const file=arg('--env-file');
 if(file)for(const line of readFileSync(file,'utf8').split(/\r?\n/)){const m=/^\s*(?:export\s+)?(GEMINI_API_KEYS?)\s*=\s*(.*?)\s*$/.exec(line);
  if(m&&m[2]){const raw=m[2].replace(/^(['"])(.*)\1$/,'$2');return {source:`${file} (${m[1]})`,key:m[1]==='GEMINI_API_KEYS'?JSON.parse(raw)[0]:raw};}}
 if(process.env.GEMINI_API_KEY)return {source:'environment GEMINI_API_KEY',key:process.env.GEMINI_API_KEY};
 throw Error('No GEMINI_API_KEY found in --env-file or the environment.');
}
const {source,key}=loadKey();
const redact=text=>String(text).split(key).join('[redacted]').slice(0,400);
const report={model,key_source:source,key_shape:{length:key.length,looks_like_google_key:/^AIza[0-9A-Za-z_-]{35}$/.test(key),has_whitespace:/\s/.test(key)}};
const base='https://generativelanguage.googleapis.com/v1beta/models/';
const headers={'Content-Type':'application/json','x-goog-api-key':key};
let started=performance.now();
const lookup=await fetch(base+model,{headers,signal:AbortSignal.timeout(15000)}).catch(e=>({ok:false,status:0,text:async()=>e.message}));
report.model_lookup={status:lookup.status,ms:Math.round(performance.now()-started)};
if(lookup.ok){const m=await lookup.json();report.model_lookup.display_name=m.displayName;report.model_lookup.methods=m.supportedGenerationMethods;}
else report.model_lookup.error=redact(await lookup.text());
if(lookup.ok){
 const image=readFileSync(new URL('../../json_stream_site/scripts/fixtures/jpeg.txt',import.meta.url),'utf8').trim();
 const body={contents:[{role:'user',parts:[{text:'Reply with exactly the word OK, then the main colour of this image in one word.'},{inlineData:{mimeType:'image/jpeg',data:image}}]}],generationConfig:{maxOutputTokens:20,temperature:0}};
 started=performance.now();let text='',first=null,usage=null,finish=null;
 const r=await fetch(base+model+':streamGenerateContent?alt=sse',{method:'POST',headers,body:JSON.stringify(body),signal:AbortSignal.timeout(30000)}).catch(e=>({ok:false,status:0,text:async()=>e.message}));
 report.generation={status:r.status};
 if(r.ok){const reader=r.body.getReader(),decoder=new TextDecoder();let buffer='';
  while(true){const {value,done}=await reader.read();if(done)break;if(first===null)first=Math.round(performance.now()-started);buffer+=decoder.decode(value,{stream:true}).replace(/\r\n/g,'\n');
   for(const chunk of buffer.split('\n\n').slice(0,-1)){const line=chunk.trim();if(!line.startsWith('data:'))continue;const data=JSON.parse(line.slice(5));
    const c=data.candidates?.[0];text+=(c?.content?.parts||[]).filter(p=>!p.thought).map(p=>p.text||'').join('');finish=c?.finishReason||finish;usage=data.usageMetadata||usage;}
   buffer=buffer.slice(buffer.lastIndexOf('\n\n')+2);}
  if(buffer.trim().startsWith('data:')){const data=JSON.parse(buffer.trim().slice(5)),c=data.candidates?.[0];text+=(c?.content?.parts||[]).filter(p=>!p.thought).map(p=>p.text||'').join('');finish=c?.finishReason||finish;usage=data.usageMetadata||usage;}
  Object.assign(report.generation,{first_byte_ms:first,total_ms:Math.round(performance.now()-started),finish_reason:finish,reply:text.trim().slice(0,80),
   tokens:usage?{input:usage.promptTokenCount,output:usage.candidatesTokenCount,total:usage.totalTokenCount}:null});
 }else{report.generation.error=redact(await r.text());}
}
report.working=Boolean(lookup.ok&&report.generation?.status===200&&/ok/i.test(report.generation?.reply||''));
report.paid_generation_calls=lookup.ok?1:0;
console.log(JSON.stringify(report,null,1));process.exit(report.working?0:1);
