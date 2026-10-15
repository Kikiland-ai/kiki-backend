import {readFile,writeFile,mkdir,cp} from 'node:fs/promises';
import {packAdapter,readAdapterAsset} from './package-adapter.mjs';
const assets=Object.fromEntries(await Promise.all([
 ['html','assets/index.html'],['css','assets/style.css'],['js','assets/capture.js'],['labjs','assets/lab.js'],['labcadence','assets/lab-cadence.js'],['streamclient','assets/json-stream-client.js'],
 ...['writing-protocol.js','writing-frames.js','guidance-protocol.js','guidance-consumer.js'].map(n=>[n,'assets/'+n])
].map(async([key,path])=>[key,await readFile(path,'utf8')])));
assets['frame-probe.js']=await readAdapterAsset('frame-probe.js');assets.adapterzip=(await packAdapter()).toString('base64');
const constants='const LAB_DEFINITION='+await readFile('data/experiment.json','utf8')+';\nconst LAB_TEMPLATE='+await readFile('data/session-template.json','utf8')+';\nconst GUIDED_POLICY='+await readFile('data/guided-policy.json','utf8')+';\nconst WRITING_TARGETS='+await readFile('data/screen-writing-targets.json','utf8')+';\n';
const helpers=(await readFile('worker/guidance-contracts.js','utf8')+'\n'+await readFile('worker/guidance.js','utf8')).replace(/^import .*;$/gm,'').replace(/^export \{[^}]+\};$/gm,'').replace(/^export /gm,'');
const scoped='const {DrawingRunJS,GuidanceTraceJS,buildCommittedDrawing,validateGuidanceSchema,DRAWING_SCHEMA}=(()=>{\n'+helpers+'\nreturn {DrawingRunJS,GuidanceTraceJS,buildCommittedDrawing,validateGuidanceSchema:validate,DRAWING_SCHEMA};})();\n';
const modules=await Promise.all(['provider','analysis','guided-progress','guidance-catalog','guidance-transport','lab','context-batch','stream','python-proxy','server'].map(n=>readFile('worker/'+n+'.js','utf8')));
const source=constants+'const ASSETS='+JSON.stringify(assets)+';\n'+assets['frame-probe.js']+'\n'+await readFile('worker/stream-core.js','utf8')+'\n'+scoped+modules.join('\n');
await mkdir('dist/server',{recursive:true});await mkdir('dist/.openai',{recursive:true});
await writeFile('worker/index.js',source);await writeFile('dist/server/index.js',source);await writeFile('dist/.openai/hosting.json',await readFile('.openai/hosting.json'));await cp('drizzle','dist/drizzle',{recursive:true});console.log('Built analysis-owned guidance experiment');
