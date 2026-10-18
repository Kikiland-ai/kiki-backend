// Builds the unpacked extension in two variants under work/floating-guidance/:
//   release/  hosted reader Sites + matlab.mathworks.com only
//   dev/      adds http://localhost:8870 (reader) and :8871 (controlled target),
//             kiki-web Lab mode's local origins (:5174, matching its API CORS defaults),
//             the visible capture canary and an open shadow root for tests.
// Never give the dev build to a learner. Run: node prototypes/floating_guidance/scripts/build-extension.mjs
import {mkdir,readFile,writeFile,copyFile,rm} from 'node:fs/promises';
const source=new URL('../extension/',import.meta.url),out=new URL('../../../work/floating-guidance/',import.meta.url);
const VERSION='0.1.2';
const HOSTED_READERS=['https://kiki-512012.web.app','https://kiki-json-stream.woodsycarp256.chatgpt.site','https://kiki-screen-receiver.woodsycarp256.chatgpt.site'];
const variants={
 release:{readers:HOSTED_READERS,targets:['https://matlab.mathworks.com'],dev:false},
 dev:{readers:[...HOSTED_READERS,'http://localhost:8870','http://127.0.0.1:5174','http://localhost:5174'],targets:['https://matlab.mathworks.com','http://localhost:8871'],dev:true},
};
const files=['core.js','ui.js','content.js','bridge.js','background.js','popup.html','popup.js'];
for(const [name,v] of Object.entries(variants)){
 const dir=new URL(name+'/',out);await rm(dir,{recursive:true,force:true});await mkdir(dir,{recursive:true});
 for(const f of files)await copyFile(new URL(f,source),new URL(f,dir));
 await writeFile(new URL('config.js',dir),`globalThis.KIKI_FG_CONFIG=${JSON.stringify({version:VERSION,...v})};\n`);
 const manifest={manifest_version:3,name:v.dev?'Kiki windows (dev)':'Kiki windows',version:VERSION,minimum_chrome_version:'116',
  description:'Shows Kiki’s current lab step and screen context in small windows on the shared MATLAB Online tab.',
  permissions:['storage','scripting'],host_permissions:v.targets.map(o=>o+'/*'),
  background:{service_worker:'background.js'},action:{default_popup:'popup.html',default_title:'Kiki windows'},
  content_scripts:[
   {matches:v.targets.map(o=>o+'/*'),js:['config.js','core.js','ui.js','content.js'],run_at:'document_start',all_frames:false},
   {matches:v.readers.map(o=>o+'/*'),js:['config.js','bridge.js'],run_at:'document_start',all_frames:false}]};
 await writeFile(new URL('manifest.json',dir),JSON.stringify(manifest,null,1)+'\n');
}
console.log(JSON.stringify({built:Object.keys(variants),version:VERSION,out:out.pathname}));
