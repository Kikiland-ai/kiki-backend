# C-AM-01 backend contract handoff to kiki-web

**Superseded by [the all-CAM handoff](all-cam-compatibility.md).** Do not implement the v2
decoder proposed below. The existing v1 envelope supports the renderer extension; the
current batch candidate covers all ten modules and both original audio scopes.

18 October 2026. Backend implementation is local on `work/learning-content-compat`, based
on PR #7 `f2dca8b806e4002411b5704e19f0f40681093298`. It is not committed/pushed or merged.
The original main and running PR #7 integration checkout were not changed.

## Deliverable and limits

C-AM-01 candidate media contains the original four Odia recordings plus a source-bound,
typed signal scene. C-AM-08's existing phase contract and legacy v1 revision are unchanged.
The current web consumer rejects the new v2 manifest, deliberately. No connected-browser,
private-delivery or content-quality acceptance is claimed.

Read [the decision/audio-scope proposal](../decisions/0012-learning-media-candidate-contract.md).
The machine-readable contracts and fixture are:

- `contracts/signal-parameters-v1.schema.json`
- `contracts/concept-media-manifest-v2.schema.json`
- `tests/fixtures/signal-parameters-v1.json`

## Export offline

Use the existing web API Python environment/dependencies, with Python UTF-8 enabled on
Windows. From this backend checkout:

```sh
python -X utf8 -B scripts/publish-concept-library.py --web-root /path/to/kiki-web --concepts C-AM-01 --contract candidate-v2 --output work/cam01-candidate
```

It writes the manifest/asset references, schema and compatibility report, not asset copies
or cloud data. Original WAV bytes are accessible through `ConceptLibrary.asset(assetId)`.
The default v1 export still yields 16 compatible recordings and the C-AM-08 scene over
all ten concepts. Six whole-concept recordings and the other eight unsupported candidate
scenes remain excluded. Candidate v2 currently projects C-AM-01 and legacy C-AM-08 only.

## Required web change

Keep reading `concept-media-manifest/v1`. Add an explicitly versioned v2 decoder and a
trusted `signal-parameters/v1` React renderer. Do not enable v2 publication or replace
existing media heads while the decoder/renderer/delivery path is incomplete. Continue
through the existing enrollment/authenticated API boundary; no direct public WAV endpoint.

The signal scene has controls in this exact order:

| Control | Unit | Min | Max | Step | Default |
|---|---|---|---|---|---|
| amplitude | normalized | 0.25 | 2 | 0.25 | 1 |
| frequency | Hz | 10 | 1000 | 10 | 100 |
| phase | degree | 0 | 180 | 15 | 0 |

Render two curves, using a 20 ms window with 900 intervals (901 points):

- Signal: `A * sin(2*pi*f*t + phase*pi/180)`.
- Reference: `sin(2*pi*f*t)`; it follows frequency, retaining unit amplitude and zero phase.

These expressions describe fixed renderer code, not executable manifest formula fields.
Readouts are period in seconds (`1/f`) and angular frequency in rad/s (`2*pi*f`). A UI may
format period as milliseconds while keeping the underlying conformance value in seconds.
At 100 Hz the period is 0.01 s / 10 ms. Use the supplied labels, prompt, accessible alt
text and source/review disclosures. Amplitude is normalized, not a measured voltage.

Structural JSON Schema validation is necessary but insufficient: implement the documented
control domains/order, output units/order, finite values, allowed range/steps, reference
semantics, unique/known placard placements and all numerical vectors. Pydantic's semantic
validators cannot all be represented in generated JSON Schema. Check both authored-source
bindings and the model/scene provenance hashes; never load a path or execute JavaScript
merely because it appears in binding metadata.

## Mac acceptance checklist

1. Validate the candidate and all 13 vectors in TypeScript; deliberately reject bad units,
   invalid controls, NaN/nonfinite calculations, unsupported renderer IDs and source drift.
2. Render on the concept/application placards from `placardIds`. Check slider/reset,
   keyboard use, visible units and mobile layout. Confirm reference amplitude/phase remain
   unchanged when only the signal amplitude/phase changes.
3. Play the matching original clip for each of the four placards through the authenticated
   media API once private delivery is approved/configured. Confirm pause/seek/speed, language
   switching, missing-English behavior and navigation cleanup. Do not fabricate English
   audio for this concept.
4. Verify lesson reading/language, artifact interaction, check/feedback, saved position and
   reload on the agreed integration learner. Artifact exploration must not grant assessed
   practical proficiency.
5. Re-run C-AM-08 bilingual audio and phase rendering as regression checks; preserve its
   existing English assets and media revision until an explicit replacement is prepared.
6. Return the exact web revision and a pass/fail/blocked record for each item. A fixture
   renderer pass does not establish connected private delivery or full-course completion.

## Actual backend verification

- Full root unittest suite: 132 passed, including both web-bridge tests (no skips).
- New slice: 8 contract/bridge tests, included in that total.
- Node conformance: 13 vectors agree with preserved `cam-packets/3` browser model.
- All-ten legacy dry-run records match the prior export; C-AM-08 v1 revision is unchanged.
- 130 pinned source files and the frozen screen baseline pass integrity checks.
- 96 recovered files / 40 placards / 22 recordings / 793.8 seconds pass media verification.
- New Python files pass Ruff; `git diff --check` passes. BB8 validation passes; its existing
  `bb8/adapters/discovery/index.json` freshness failure remains unrelated and unchanged.
- BB8 helper suite: 34 pass, two error at symlink setup because this Windows account lacks
  the required privilege (WinError 1314). No privilege/policy change was attempted.
- Provider calls: zero. Cloud writes: zero. No browser/renderer/audio quality approval.

Next: Mac contract/renderer adoption and a C-AM-01 acceptance receipt. Then implement the
agreed concept-audio variant with C-AM-04 and expand the remaining scene projectors.
