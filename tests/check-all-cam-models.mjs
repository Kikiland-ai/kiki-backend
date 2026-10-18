import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
const require=createRequire(import.meta.url);
const Models=require('../artifacts/cam-review/site/dist/concepts/C-AM-01/models.js');
const vectors=JSON.parse(readFileSync(new URL('../contracts/cam-model-conformance-v1.json',import.meta.url)));
let cases=0;
for(let i=1;i<=10;i++){
  const id=`C-AM-${String(i).padStart(2,'0')}`;
  const scene=JSON.parse(readFileSync(new URL(`../artifacts/cam-review/site/dist/concepts/${id}/scene.json`,import.meta.url)));
  for(const test of vectors[id]){
    const result=Models.render(scene,test.inputs,test.cursor);
    assert.deepEqual(result.readouts,test.readouts);
    assert.equal(result.extraSvg!==null,test.hasExtraSvg);
    assert.equal(result.series.length,test.samples.length);
    result.series.forEach((s,j)=>[0,.125,.25,.5,.75,1].forEach((x,k)=>{
      assert.ok(Number.isFinite(s.fn(x)));
      assert.ok(Math.abs(s.fn(x)-test.samples[j].values[k])<1e-12);
    }));
    for(const plot of result.plots)assert.ok(!/NaN|Infinity/.test(plot.svg));
    cases++;
  }
  assert.throws(()=>Models.model(scene,{...Models.defaults(scene),[scene.controls[0].name]:Infinity}));
  assert.throws(()=>Models.model(scene,{...Models.defaults(scene),[scene.controls[0].name]:scene.controls[0].max+scene.controls[0].step}));
}
function scene(i){return JSON.parse(readFileSync(new URL(`../artifacts/cam-review/site/dist/concepts/C-AM-${String(i).padStart(2,'0')}/scene.json`,import.meta.url)));}
assert.ok(Math.abs(Models.model(scene(1),{}).series[0].fn(.125)-1)<1e-12);
assert.equal(Models.model(scene(2),{stage:3}).flow.active,3);
assert.equal(Models.model(scene(3),{mu:1.5}).readouts[1][1],'-0.50');
assert.deepEqual(Models.model(scene(4),{fm:100}).spectrum.map(s=>s.f),[1900,2100]);
assert.equal(Models.model(scene(5),{family:2}).spectrum.family,2);
assert.ok(Math.abs(Models.model(scene(6),{stage:2}).series[1].fn(.125)-.5)<1e-12);
assert.ok(Math.abs(Models.butterworth(100,500).gain-.9992009587217894)<1e-12);
assert.ok(Math.abs(Models.model(scene(8),{phase:60}).series[1].fn(.125)-.5)<1e-12);
assert.equal(Models.model(scene(9),{df:5000,B:1000}).readouts[1][1],'12000 Hz');
assert.equal(Models.render(scene(10),{constant:1},.25).readouts[3][1],'8.000');
console.log(JSON.stringify({concepts:10,renderCases:cases,independentExamples:10,invalidInputChecks:20,passed:true,providerCalls:0}));
