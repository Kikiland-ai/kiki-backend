import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
// Execute the real capture function with an encoder barrier, not a copied
// implementation. The full native-browser suite separately covers dispatch.
const source=readFileSync(new URL('../assets/capture.js',import.meta.url),'utf8'),frame=source.slice(source.indexOf('  async function frame() {'),source.indexOf('  async function tick() {'));
test('a stalled JPEG encoder cannot keep live guidance masked or sample after unmask',async()=>{
 let masked=false,encode,encoding,closed=false,copied=false,uploaded=false;
 const reached=new Promise(r=>encoding=r),canvas={width:0,height:0,getContext:()=>({drawImage(){assert.equal(masked,true);assert.equal(closed,false);copied=true;}}),toBlob(callback){assert.equal(masked,false,'Ink must be restored before JPEG scheduling');encode=()=>callback(new Blob(['jpeg']));encoding();}};
 const video={videoWidth:96,videoHeight:54},elements=new Map([['preview',video],['remote',{}],['remote-empty',{}]]),blob=new Blob(['jpeg']);
 const fixture={canvas,$:id=>elements.get(id),window:{KikiWriting:{prepareFrame:async()=>{masked=true;return {};},sample:()=>({image:{},width:96,height:54}),fingerprint:()=>{assert.equal(copied,true);assert.equal(masked,true);return [];},finishFrame:async ticket=>{assert.ok(ticket);masked=false;closed=true;return {};},admitFrame:async()=>null}},performance,fetch:async()=>{uploaded=true;return {ok:true,headers:{get:()=>null},blob:async()=>blob};},AbortSignal,URL:{createObjectURL:()=>'',revokeObjectURL(){}},decode:()=>({observation:{latest_frame:{}}}),show(){},status(){},maybeAnalyze(){}};
 const run=new Function('fixture',`const {canvas,$,window,performance,fetch,AbortSignal,URL,decode,show,status,maybeAnalyze}=fixture;let stream={},paused=false,busy=false,ending=false,generation=1,captureViewRevision=1,lastSourceWidth=0,lastSourceHeight=0,sequence=0,started=0,session='fixture',upload=null,imageURL=null;${frame};return frame;`)(fixture);
 const pending=run();await reached;assert.equal(uploaded,false);assert.equal(masked,false);assert.equal(closed,true);encode();assert.equal(await pending,2000);assert.equal(uploaded,true);
});
