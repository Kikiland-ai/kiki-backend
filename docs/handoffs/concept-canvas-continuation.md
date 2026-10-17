# Continue the concept-canvas system

All ten complete C-AM packets are stored in a queryable SQLite database with
versioned audio/artifact files on this branch. Start with
`prototypes/concept_library/README.md` for the read API and publishing commands.
The user clarified that the web media integration is already built and merged;
the deliverable here is the content and pipeline in a usable stored form.
The adapter reuses the merged app publisher and schemas rather than replacing them.

## Start reading here

1. `prototypes/concept_library/README.md`, then this handoff and
   `artifacts/cam-review/recovery-manifest.json`.
2. `artifacts/cam-review/site/dist/review-manifest.json`: ten concepts and revisions.
3. One `dist/concepts/C-AM-XX/packet.json`: source placards, mixed display/spoken
   text, narration hashes/scope, semantic scene and pending review status.
4. Its `models.js`, `player.js`, `scene.json` and `index.html`: working browser
   behavior. All ten pages use identical trusted model/player code.
5. Existing `prototypes/mixed_script/README.md`, `pipeline.py`, `speech.py`:
   preserved text/TTS adapters. Reuse these; do not build another translation or
   speech pipeline.
6. `context/README.md` and the pinned prototype directions/student journey for
   product source precedence.

Live review: https://kiki-canvas-studio.woodsycarp256.chatgpt.site/

Run locally from the backend repository root:

```sh
python -B scripts/verify-cam-review.py
python -B scripts/concept-library.py list
python -B scripts/concept-library.py get C-AM-08
python -m http.server 8000 --directory artifacts/cam-review/site/dist
```

Then open `http://localhost:8000/`. The earlier VCO demo is at `/vco/`.
No provider key or cloud identity is needed to review these saved packets.

## What is preserved

All 40 authored placards, English source and mixed Odia–English display/spoken
representations; 22 real WAV recordings totalling 793.8 seconds; ten editable
analytic scenes, posters and interactive pages; a library with cross-concept
navigation; original VCO demonstration; original Site build helper and hosting
identity. Scientific, native-Odia and pronunciation reviews remain pending.

| Concept | Focus |
| --- | --- |
| C-AM-01 | Amplitude, frequency and phase |
| C-AM-02 | Message, carrier and the purpose of modulation |
| C-AM-03 | Conventional AM, envelope and modulation index |
| C-AM-04 | DSB-SC generation and sidebands |
| C-AM-05 | SSB and VSB compared with DSB-SC |
| C-AM-06 | Coherent demodulation and recovery gain |
| C-AM-07 | Lowpass filtering and waveform comparison |
| C-AM-08 | Carrier mismatch and debugging |
| C-AM-09 | Frequency modulation and deviation |
| C-AM-10 | Phase modulation and FM–PM distinction |

C-AM-01/02/03/08 use per-placard narration; the others have one whole-concept
recording with manual placard navigation. English reading is available; English
audio is absent. There are no sentence timings or narration-driven scene cues.
Controls change analytic curves/readouts; these are teaching examples, not lab
measurements. No generated base image is claimed for these ten SVG models.

Text was reused exactly from the authored Odia case after fresh translation
attempts failed validation/provider availability. Existing recordings were reused
when their exact speech/audio hashes matched. New recordings used the existing
Gemini 3.8 Flash Lite/Flash TTS adapter; the full model was used after Lite quota.
Provider model provenance remains in packet narration rows. Rejected candidates
and provider responses were not published and are not recoverable here.

## Recovery boundary — read before implementation

On 18 October 2026 the execution checkout contained only committed baseline
`2f8eb62`, with no earlier uncommitted files or ignored `work/` artifacts.
The current task recovered the exact previously pushed Sites source commit
`b1c293c11400ea20156c39999a6e14b67c309feb` using the Sites repository connector.
Every copied file is SHA-256 listed in the recovery manifest. This is saved
published work, not regenerated narration or a replacement implementation.

The earlier uncommitted `prototypes/topic_canvas/` Python module, canvas JSON
contracts/fixtures/tests, `prototypes/concept_packets/` generator/export/publisher
code, associated CLI/tests, and newer architecture/handoff documents are absent
from this reset checkout and were not present in the Sites source repository.
The original `cam-concept-packets-v1.zip`, generation journals, source input
files and `*.audio.json` sidecars were ignored local outputs and are also absent.
This branch does **not** claim to recover those original files or their prior
54-test verification. Restore them from an original workspace/archive if one
exists; otherwise reconstruct the missing orchestration deliberately and test
it against these immutable packet examples. The existing committed mixed-script
adapters remain available. Do not run the old Site build helper expecting its
original batch input files to exist; use the saved static library directly.

## Frontend/backend ownership and next build

The original content source is the frontend consolidation at
`ba40218d7bf07637debe530019bcf8faf6afb61a`. The user confirmed the implementation
is merged. This publication inspected current `kiki-web` main at `93cce9b`
(PR #5 merged), including `apps/api/src/kiki_api/concept_media.py`,
`media_models.py`, the native publisher, and the web media contract. Manifest
delivery/private reads and media rendering are already implemented in that app.
The historical reading directive posted in PR #2 is
https://github.com/Kikiland-ai/kiki-web/pull/2#issuecomment-6222578532.

The reviewed source catalog version is `am-51187527300cba2fa3cca868`.
Media additions must preserve its immutable source documents and learner
progress/assessment records. Use an additive media revision, not a source
catalog reimport just to attach audio or an artifact.

Backend owns source-bound concept planning, reuse of the text/TTS adapters,
rendering with trusted models, validation, review state, resumable generation,
asset upload, immutable media manifests and authorized delivery. Preprocess
concept assets before lesson playback: Firestore stores text, scene definitions,
revisions and file references; private object storage holds WAV/SVG bytes.
No generation should be required during ordinary frontend lesson navigation.

Existing merged app namespace (used by the adapter):

`conceptMedia/LP-ANALOG-MODULATION/catalogVersions/{catalogVersion}/concepts/{conceptId}/revisions/{mediaRevision}`

Maintain a separate current media pointer. Upload content-addressed assets first,
verify hashes/read-back, then activate a reviewed immutable revision. Check the
catalog version before writing; make identical publication retries idempotent.
Do not change access rules or provision a bucket as a side effect. The user has
explicitly deferred production Firestore/object publication until their existing
cloud identity/bucket is available. Firebase browser configuration alone is not
the server identity. Sites preview publication is separate and already complete.

Web owns the concept/placard layout, artifact placement beside content on desktop
and below it on mobile, language selection and existing Listen state. Fetch a
manifest by concept/version, mount the allowlisted scene renderer, and expose
native audio pause/seek/speed plus model parameters/reset. Language changes select
matching audio or show its absence. Pause on hidden/navigation and avoid competing
audio/model playback. Automatic narration-driven transitions require reviewed
timing cues; these packets support manual exploration. Browser autoplay limits
still apply. Artifact exploration is not assessment or practical lab evidence.

The merged app currently accepts per-placard recordings and one allowlisted
phase-recovery renderer. The new adapter projects 16 recordings (C-AM-01/02/03/08)
and the C-AM-08 phase scene, with explicit exclusions for the other scene types
and six whole-concept recordings. All originals remain queryable in SQLite.
This is a measured contract boundary, not missing basic frontend integration.
Next: publish compatible records through the existing app after cloud access is
available; extend its trusted scene/audio-scope contract to consume the rest, or
generate true per-placard recordings. Do not invent timing cues. Keep the current
C-AM-08 English audio in mind before explicitly replacing its published revision.

## Verification for this handoff

`scripts/verify-cam-review.py` verifies all recovered file hashes, WAV
measurements, speech/display hashes, exact mixed text, four-placard coverage,
scene consistency and unchanged publication status without provider calls.
The current execution's actual test/check results are recorded in the active
plan. Earlier browser checks and successful Sites deployment are historical
session evidence, not a new authenticated browser test in this reset environment.
