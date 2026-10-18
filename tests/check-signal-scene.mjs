// Compare the handoff vectors with the preserved, independent browser model.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
const require = createRequire(import.meta.url);
const Models = require('../artifacts/cam-review/site/dist/concepts/C-AM-01/models.js');
const saved = JSON.parse(readFileSync(new URL('../artifacts/cam-review/site/dist/concepts/C-AM-01/scene.json', import.meta.url)));
const candidate = JSON.parse(readFileSync(new URL('./fixtures/signal-parameters-v1.json', import.meta.url)));
for (const vector of candidate.behaviorTests) {
  const result = Models.model(saved, vector.inputs);
  const observed = vector.output === 'periodSeconds' ? Number(result.readouts[0][1].split(' ')[0]) / 1000
    : vector.output === 'angularFrequency' ? 2 * Math.PI * result.values.frequency
    : result.series[vector.output === 'signal' ? 0 : 1].fn(vector.inputs.timeSeconds / candidate.timeWindowSeconds);
  assert.ok(Math.abs(observed - vector.expected) <= vector.tolerance, `${vector.output} differs from saved model`);
}
assert.equal(candidate.sampleIntervals, 900);
assert.equal(candidate.timeWindowSeconds, 0.02);
if (process.env.KIKI_WEB_CHECKOUT) {
  const module = await import(pathToFileURL(resolve(process.env.KIKI_WEB_CHECKOUT, 'apps/web/src/contracts/concept-media.ts')));
  const record = JSON.parse(readFileSync(new URL('./fixtures/concept-media-C-AM-01-candidate.json', import.meta.url)));
  const parsed = module.MediaManifestSchema.parse(record.manifest);
  assert.equal(parsed.schema, 'concept-media-manifest/v1');
  assert.equal(parsed.narration.length, 4);
  assert.equal(parsed.artifacts.length, 0);
  assert.deepEqual(parsed.unsupportedArtifacts.map(a => a.renderer), ['signal-parameters/v1']);
}
console.log(JSON.stringify({ passed: true, behaviorVectors: candidate.behaviorTests.length, model: saved.modelVersion, providerCalls: 0 }));
