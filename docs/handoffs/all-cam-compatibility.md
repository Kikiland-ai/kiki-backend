# All ten CAM modules: one consumer integration

18 October 2026. This supersedes the C-AM-01-only handoff and proposed v2 decoder. The
original content handoff remains the architectural basis. Existing media services,
private delivery, player and renderer registry should be extended together.

Backend work is local/uncommitted on work/learning-content-compat, based on PR #7 f2dca8b.
It has not changed the live integration checkout or kiki-web source.

## Batch export

```sh
python -X utf8 -B scripts/publish-concept-library.py --web-root /path/to/kiki-web --contract candidate-cam --output work/all-cam
```

Every concept exports a scene and narration, with no exclusions. Existing v1 manifest,
revision and media-head formats are retained. `--apply` is blocked for the candidate.

| Concept | Scene kind | Consumer renderer | Audio |
|---|---|---|---|
| C-AM-01 | signal | common canvas | 4 Odia placard clips |
| C-AM-02 | flow | common canvas | 4 Odia placard clips |
| C-AM-03 | am | common canvas | 4 Odia placard clips |
| C-AM-04 | dsb | common canvas | 1 Odia concept clip |
| C-AM-05 | spectrum | common canvas | 1 Odia concept clip |
| C-AM-06 | receiver | common canvas | 1 Odia concept clip |
| C-AM-07 | filter | common canvas | 1 Odia concept clip |
| C-AM-08 | phase_recovery | existing phase renderer | Existing 4 English + 4 Odia clips |
| C-AM-09 | fm | common canvas | 1 Odia concept clip |
| C-AM-10 | pm | common canvas | 1 Odia concept clip |

Total: 10 artifacts, 26 recordings. Original backend assets are not regenerated or removed.
The C-AM-08 web package stays cm-e0f086007cc9f2062af093f3, byte-for-byte equivalent to its
existing fixture. Default legacy backend exports remain unchanged across all concepts.

## Exact shared changes for kiki-web

1. `apps/api/src/kiki_api/media_models.py`: add the common canvas artifact to the existing
   phase artifact union; add concept-scoped narration beside existing placard renditions.
   Reuse common audio/provenance/review types. Do not introduce another envelope/version.
2. `concept_media.py`: keep source/hash checks; bind concept audio to exactly the ordered
   covered placards, hash the corresponding texts joined with one space, and validate the
   full asset index. Make experience() produce a scope-aware media pointer. Keep published
   artifact metadata available independently of audio storage configuration; represent
   unavailable audio honestly and retain authenticated private-byte delivery.
3. `apps/web/src/contracts/concept-media.ts`: extend SCENES and SceneArtifact for
   cam-concept-canvas/v1. Add the concept narration union and corresponding pointer type.
   Extend checkManifestForLesson/findRendition for ordered coverage and language matching.
   Keep unknown renderer IDs unsupported; do not execute authored strings.
4. `features/learning/scenes.tsx`: register one common CAM renderer. Vendor the supplied
   shared model module as reviewed application code, never fetch/execute it from a packet.
   The module accepts validated scene.kind/controls and returns the saved analytic model's
   traces/readouts/flow/spectrum. Implement a typed React wrapper with common sliders,
   reset, units, alt text and review/source disclosures. Avoid duplicate C-AM-04 visuals
   when a common canvas replaces the existing lesson.visual slot. Keep C-AM-08 native.
5. Player/lesson state: select placard-specific clips first, otherwise the concept clip
   covering the active placard in the selected language. Keep the same concept recording
   and playback position across manual placard changes. Changing language/concept, hiding
   the page and sign-out must preserve the established pause/cleanup behavior. There are
   no trustworthy per-placard seek offsets for concept recordings.

The current data-only artifact gate and limited renderer registry are separate problems.
Simply restoring SSH, adding keys or switching on a bucket cannot add missing renderers.
Conversely a compatible renderer cannot see a scene the API has omitted.

## Bundle and validation

The transfer bundle contains all ten records, their 26 original WAV assets, complete
candidate JSON Schema, pinned model/control policy, 38 conformance cases, a reviewed-code
ES-module adaptation of the identical saved model, and producer changes. Verify its hash
manifest. The original model SHA is
41cb3e229a603040d7b1dea9e47e4f8563a347f15aaa1c731c64c02f9a3420a5.

Structural schema validation alone is insufficient: verify the pinned policy's kind and
controls, all source/model hashes, finite values, ordered known placard coverage, narration
identity/hashes and conformance behavior. The producer's semantic validators are the
reference for those checks. Stored formulas remain source metadata, never executable code.

Run one parameterized browser checklist across ALL concepts: discover/open, four placards,
language settings, available/missing audio, playback/cleanup, artifact controls/reset,
assessment feedback, saved position and reload. Use a dedicated agreed integration learner.
Distinguish schema/model fixtures from real authenticated media delivery. No fixture may
silently stand in for connected mode.

## Review status and acceptance limits

See decision 0013 for explicit saved-model limitations: two versus three traces in C-AM-01's
brief; fixed versus adjustable carrier in C-AM-04; normalized FM/PM; nine concepts without
English audio; no sentence alignment. The user subsequently marked scientific accuracy,
narration fidelity, Odia/technical pronunciation and audio quality verified on 18 October
2026; see [the review ledger](../reviews/cam-content-review-status.md) for evidence scope.
Original immutable records still carry their original review metadata. A successful
renderer does not establish practical proficiency or connected browser acceptance.

No cloud upload, IAM/billing change, source-catalog import, learner reset, push, merge or
deployment is part of this handoff. The Mac implements the shared consumer once, verifies
all ten modules, then reports exact revision, checks and remaining delivery/content gaps.
