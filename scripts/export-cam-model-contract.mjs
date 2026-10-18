// Export pinned model policies/conformance examples, never generated lesson content.
import { readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';
const require = createRequire(import.meta.url);
const Models = require('../artifacts/cam-review/site/dist/concepts/C-AM-01/models.js');
const policies = { modelVersion: 'cam-packets/3', modelsSha256: '', concepts: {} };
const fixtures = {};
for (let i = 1; i <= 10; i++) {
  const id = `C-AM-${String(i).padStart(2, '0')}`;
  const folder = new URL(`../artifacts/cam-review/site/dist/concepts/${id}/`, import.meta.url);
  const scene = JSON.parse(readFileSync(new URL('scene.json', folder)));
  const digest = createHash('sha256').update(readFileSync(new URL('models.js', folder))).digest('hex');
  if (policies.modelsSha256 && digest !== policies.modelsSha256) throw new Error('Model code differs across concepts');
  policies.modelsSha256 = digest;
  policies.concepts[id] = { kind: scene.kind, controls: scene.controls };
  const defaults = Models.defaults(scene);
  const inputs = [defaults, ...scene.controls.flatMap(c => [c.min, c.max].map(v => ({ ...defaults, [c.name]: v })))];
  fixtures[id] = inputs.map(input => {
    const result = Models.render(scene, input, 0.25);
    return { inputs: input, cursor: 0.25, readouts: result.readouts,
      samples: result.series.map(s => ({ label: s.label, values: [0, 0.125, 0.25, 0.5, 0.75, 1].map(t => s.fn(t)) })),
      hasExtraSvg: result.extraSvg !== null };
  });
}
writeFileSync(new URL('../contracts/cam-model-policies-v1.json', import.meta.url), JSON.stringify(policies, null, 2) + '\n');
writeFileSync(new URL('../contracts/cam-model-conformance-v1.json', import.meta.url), JSON.stringify(fixtures, null, 2) + '\n');
console.log(JSON.stringify({ concepts: 10, cases: Object.values(fixtures).reduce((n, x) => n + x.length, 0), modelsSha256: policies.modelsSha256 }));
