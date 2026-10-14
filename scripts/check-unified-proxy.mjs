// Offline integration contract: the prepared Site bridge preserves job idempotency.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source=await readFile('deploy/sites/python-proxy.js','utf8');
const proxy=new Function('json',source+'\nreturn pythonProxy;')((body,status)=>Response.json(body,{status}));
let forwarded;
const env={KIKI_FASTAPI_ORIGIN:'https://backend.test',KIKI_PROXY_SECRET:'controlled-secret-at-least-32-characters',
 PYTHON_PROXY_FETCH:async request=>{forwarded=request;return Response.json({ok:true},{status:202});}};
const headers={'oai-authenticated-user-id':'actual-owner','origin':'https://site.test','content-type':'application/json','idempotency-key':'frontend-job-1','x-kiki-owner':'spoofed','x-kiki-proxy-key':'spoofed'};
let result=await proxy(new Request('https://site.test/v1/mixed-language-jobs',{method:'POST',headers,body:'{}'}),env);
assert.equal(result.status,202);assert.equal(forwarded.url,'https://backend.test/v1/mixed-language-jobs');
assert.equal(forwarded.headers.get('idempotency-key'),'frontend-job-1');assert.equal(forwarded.headers.get('x-kiki-owner'),'actual-owner');
assert.equal(forwarded.headers.get('x-kiki-proxy-key'),env.KIKI_PROXY_SECRET);assert.equal(forwarded.headers.get('origin'),'https://backend.test');
result=await proxy(new Request('https://site.test/v1/mixed-language-jobs',{method:'POST',headers:{...headers,origin:'https://foreign'},body:'{}'}),env);
assert.equal(result.status,403);
result=await proxy(new Request('https://site.test/v1/mixed-language-jobs',{method:'POST',headers:{...headers,'oai-authenticated-user-id':''},body:'{}'}),env);
assert.equal(result.status,401);
console.log('PASS: job idempotency, fixed origin, trusted owner/secret, same-origin and authentication');
