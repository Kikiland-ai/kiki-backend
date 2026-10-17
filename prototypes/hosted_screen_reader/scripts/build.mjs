import {readFile,writeFile,mkdir,cp} from 'node:fs/promises';
const assets = Object.fromEntries(await Promise.all([
  ['html','assets/index.html'], ['css','assets/style.css'], ['js','assets/capture.js'], ['labjs','assets/lab.js'], ['labcadence','assets/lab-cadence.js'],
].map(async ([key,path]) => [key,await readFile(path,'utf8')])));
await mkdir('dist/server',{recursive:true});
await mkdir('dist/.openai',{recursive:true});
const constants='const LAB_DEFINITION='+await readFile('data/experiment.json','utf8')+';\nconst LAB_TEMPLATE='+await readFile('data/session-template.json','utf8')+';\nconst GUIDED_POLICY='+await readFile('data/guided-policy.json','utf8')+';\n';
const source = constants+'const ASSETS = '+JSON.stringify(assets)+';\n'+await readFile('worker/provider.js','utf8')+'\n'+await readFile('worker/analysis.js','utf8')+'\n'+await readFile('worker/guided-progress.js','utf8')+'\n'+await readFile('worker/lab.js','utf8')+'\n'+await readFile('worker/python-proxy.js','utf8')+'\n'+await readFile('worker/server.js','utf8');
await writeFile('worker/index.js',source);
await writeFile('dist/server/index.js',source);
await writeFile('dist/.openai/hosting.json',await readFile('.openai/hosting.json'));
console.log('Built dependency-free hosted receiver');

await cp('drizzle','dist/drizzle',{recursive:true});
