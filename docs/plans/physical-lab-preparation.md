> Current repository boundary: student-facing UI/rendering has moved to kiki-web `codex/physical-lab-ui`; backend preview routes/modules are removed. See [the updated handoff](../handoffs/physical-lab-preparation.md). Earlier implementation notes below retain history.

# Direct experiment demo update — 21 November 2026

Completed the user's demo request: skip theory interactions in the preview while
retaining the original backend prerequisite pipeline. The explicit demo mode
presets setup controls only; all six connections, null adjustment and two output
readings remain student actions, checked by the backend. Correct actions advance
without a Next button. Incorrect actions stay at the current step.

The 3D workspace includes a bottom-right native fullscreen control and a draggable
Kiki guide with current targets, inline setting/measurement controls and live
waveforms/readings. Automatic guide placement avoids obscuring required sockets.
The CRO uses the backend trace corresponding to its current probe connection.

Native Chrome completed the entire nine-step path, tested an incorrect lead,
observed 1000 Hz and 0.5 V peak recovery, and entered/exited fullscreen. Automated
verification: 222 Python tests, 35 skips, no failures; seven JS checks. Mode/evidence
separation and the normal prerequisite gates are covered. No provider calls or
production changes. Draft pack is 1.2.0; current asset is unchanged v3.

Handoff: docs/handoffs/physical-lab-preparation.md. Last completed: native demo
acceptance. Next: user review and existing Kiki web integration work.

---

# Refinement update — 21 November 2026

User feedback: the first model's generic coloured pegs were confusing and the
prerequisite button did not open lessons. Native Chrome reproduced the failure
at seven of ten explored parts. Fix: apparatus exploration no longer gates lesson
entry, and a serial client queue preserves rapid selections instead of dropping
them. Concept readiness still gates later procedure stages.

Draft pack 1.1.1 adds reference-informed green PCB/cream enclosure geometry,
printed labels/traces, physical socket contacts, gray indexed knobs, switch,
ICs and resistor details. Source references: SS Labs AC-07 and BIET Future Tech
trainer photos. Original scene artwork is code-authored; downloaded reference
photos remain under ignored work/, not shipped as assets or claimed as our work.
There are 17 semantic targets plus 242 details, and 22 printed labels. Earlier
asset versions remain byte-identical for pinned sessions.

The preview now provides direct 3D picking, orbit/view controls, dial exploration
and input/output socket selection for rehearsal. A portable canvas renderer draws
the actual glTF mesh geometry and artwork without a WebGL/CDN requirement.

Verification: 219 Python tests, 35 skips, no failures; four JS checks; full HTTP
smoke; glTF validator zero errors/warnings/infos/hints. Native Chrome confirmed
lesson entry without apparatus clicks, a 100% first quiz followed by concept two,
and a 1000 Hz exploratory control confirmation. No provider calls, push or
production changes. Local preview is running on port 8771.

The implementation record below preserves the first slice's historical checks.

---

# Physical lab preparation implementation

## Mission

Build a reusable backend for confirmed physical experiments and complete the
DSB-SC preparation pack so Kiki can integrate and test it. The student should
recognise the apparatus, understand prerequisites, rehearse independently and
carry a preparation record into the college lab.

## Source and decisions

- User approved a prescribed-experiment catalogue; recognition/ambiguity paths
  are out of scope. The college assigns the experiment and equipment profile.
- Started from backend main `c51b65417e3254489233d33e81715eba50c3d66d` in a new
  worktree on `codex/physical-lab-preparation`; existing checkout edits preserved.
- ANITS ECE-319 experiment 3 grounds the DSB-SC procedure. The pack records its
  source URL and distinguishes manual facts from ideal-model assumptions.
- Pack contracts, state machine and numerical behaviour are separate. The
  generic engine preserves procedure order, including interleaved positioning
  and measurements, as checked by a second optical geometry fixture.
- No provider requests, production deployment, commit or push is part of this
  local implementation. Existing screen-reading budgets remain unchanged.

## Completed workstreams

| Workstream | Result | Evidence |
|---|---|---|
| Pack contract | Validated targets, prerequisite order, controls, procedure and questions; exported JSON schemas/OpenAPI | Pack validation and contract export checks |
| Session pipeline | Orientation through prepared; owner-scoped, durable, version-pinned and retry-safe | Acceptance, restart, concurrency and ownership tests |
| DSB-SC content | 17 parts; 5 concepts/25 checks; 14 procedure steps; 3 faults; 5 readiness questions | Full synthetic HTTP traversal |
| 3D assets | Original schematic glTF geometry with stable semantic node IDs | Khronos validator: zero errors/warnings; deterministic regeneration |
| Signal model | Explicit ideal DSB-SC/recovery assumptions, waveforms, sidebands and readings | Numerical tests |
| Preview | Local interactive harness; WebGL with software 3D fallback | Native Chrome render, part explanation, selection and saved revision observed |
| Integration | Additive unified-app routes, local Docker packaging and frontend handoff | Existing routes regression checks |

## Verification record

- Python 3.12 environment installed from the repo's existing pinned requirements.
- Full backend suite: 217 tests run, 35 conditional tests skipped; no failures
  after restoring the existing LFS audio prerequisites. The first system-Python
  3.10 run was interrupted because existing code requires newer asyncio APIs.
- 15 physical-lab tests cover DSB-SC completion, another equipment/adapter pack,
  interleaved measurements, 60%/80% thresholds, mandatory handling question,
  incorrect actions/units, restart/version pinning, ownership, retries, concurrent
  revisions, answer-key redaction, finite values, pack validation and geometry.
- HTTP smoke: all eight stages, 50 events, zero providers; expected virtual
  recovered frequency and amplitude; physical execution explicitly not performed.
- Source integrity: 130 pinned files unchanged. BB8 validation/discovery checks
  and 12 reference-adapter checks pass. JavaScript syntax check passes.
- Khronos `gltf-validator` reported zero errors, warnings, infos or hints.
- No dedicated 3D skill was installed. The assets were built deterministically
  from code using glTF 2.0 and visually checked in the native browser. Chrome's
  WebGL context was unavailable; the software renderer was observed working.
- A full-disk write failure interrupted editing. Disposable npm download-cache
  cleanup recovered space; no project files were removed. Git LFS was installed
  to restore the existing audio assets for regression verification.

## Assumptions and limitations

- The confirmed equipment is represented by a manual-based schematic layout;
  exact manufacturer panel measurements were not supplied or fabricated.
- Technical, Odia and equipment-fidelity reviews remain pending. This pack is
  for development testing. Questions are currently English; core apparatus,
  concept and procedure explanations include draft Odia support.
- The SQLite session store targets a single instance with persistent disk.
  The deployed Firestore/cloud engine and Kiki web proxy/UI are unchanged.
- Vocabulary, academic English and physical proficiency are not inferred from
  virtual completion. Actual college readings remain separate.

## Now / Next / Later

- **Now:** reusable backend, DSB-SC pack and local developer preview are implemented
  and verified. Finish review of the branch diff and hand over integration docs.
- **Next:** wire Kiki web's physical-lab entry, backend proxy routes, asset player,
  activity UI and preparation receipt to these contracts; obtain instructor and
  native-language review before student release.
- **Later:** additional reviewed packs/behaviour adapters, shared cloud session
  persistence and trusted learner-evidence reuse as separately scoped changes.

## Cold pickup

- **Last completed:** backend/pack acceptance and native preview verification.
- **Open first:** `docs/handoffs/physical-lab-preparation.md`, ADR 0012, then
  `contracts/physical_lab.py` and `prototypes/physical_labs/service.py`.
- **Do not repeat:** experiment recognition design, runtime 3D generation, or
  screen-sharing trials; these are outside this pipeline.
- **Exact continuation:** integrate the listed `/v1/physical-labs` routes into
  Kiki web using a physical-preparation session, separate from software guidance.
