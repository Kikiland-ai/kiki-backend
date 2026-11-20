# Physical lab preparation through prescribed experiment packs

20 November 2026. User-authorised local implementation, starting from backend main
`c51b65417e3254489233d33e81715eba50c3d66d`, branch `codex/physical-lab-preparation`.

## Decision and scope

The student selects a confirmed prescribed experiment with a confirmed equipment
profile. Recognition, equipment ambiguity and experiment generation are outside
this pipeline. The backend serves reusable preparation sessions. DSB-SC is the
first complete content pack. Existing software guidance routes remain separate.

Use a modular extension of the unified FastAPI app, not another service. Packs
are validated Pydantic documents. A deterministic renderer asset builder emits
glTF 2.0 with embedded geometry and stable semantic targets. The session engine
owns progression and evidence. Behaviour adapters own numerical observations.
No LLM grades connections, changes laboratory hardware, or declares readiness.

Pack authoring and student runtime are separate. Adding an experiment requires
its reviewed content and assets. `declarative/v1` supports action-check packs;
experiments with different physical behaviour add an adapter behind the same
`observations(pack, apparatus)` and `expected_measurement(pack, apparatus, rule)`
interfaces. The engine preserves interleaved action/measurement order. This is extensibility, not a claim
that all scientific simulation models are already implemented.

## State and evidence

Orientation → prerequisites → demonstration → independent rehearsal → virtual
observations → fault diagnosis → readiness assessment → prepared.

Concept checks pass at 60% by default; readiness at 80%. Packs may specify their
own thresholds and mandatory questions. The DSB-SC handling question is mandatory.
Rehearsal actions are checked in procedure order, including target, connection,
setting, unit and tolerance. One source drives each input. Moving the CRO probe
replaces its previous source. Viewing demonstrations does not create independent
practice evidence. Incorrect attempts remain in the evidence history.

Concept evidence is separate from practical preparation. Vocabulary and English
expression are explicitly not assessed by this slice. Physical execution remains
`not_performed`; physical observation rows are empty in the preparation receipt.
Existing learner mastery is not inferred from this preparation or copied across
unrelated experiments. Future reuse must consume trusted, version-compatible
learner evidence rather than a client-supplied passed flag.

## Persistence, security and versions

SQLite WAL, immediate write transactions, owner-scoped creation idempotency,
body-bound event IDs and optimistic revisions provide durable single-instance
sessions. The complete private pack is snapshotted per session. A pack digest
and an asset digest identify the exact content used. Asset names are versioned;
keep old asset files when publishing a new pack version. Mutations use existing
same-origin checks; owner identity uses the existing cookie or trusted proxy
boundary. Clients cannot submit stage completion or prerequisite-pass flags.
Answer keys stay server-side. Requests are bounded to 16 KB and sessions to
2000 accepted events. No extra provider budget or screen observer is involved.

This SQLite store is suitable for local/single-instance testing with persistent
disk. It is not a multi-replica Firestore implementation. The separate hosted
`prototypes.cloud_lab` app is unchanged. Deployment or migration to shared cloud
persistence needs its own implementation and verification.

## DSB-SC grounding and limitations

Source: [ANITS ECE-319 manual, experiment 3](https://ece.anits.edu.in/labmanuals/AC%20%26%20DC%20LAB%20MANUAL%20%5BR-19%5D.pdf).
The pack follows its balanced modulator, null adjustment and synchronous detector
sequence. The equipment layout is an original schematic reconstruction because
the source does not establish an exact manufacturer panel geometry. Supply
wiring is not inferred from the procedure's brief supply instruction; receiver
schematic details require the actual instructor-approved equipment documentation.

The original questions, explanations and checkpoints are authored for Kiki. The
signal adapter is an ideal teaching model with declared normalised amplitudes,
unity receiver gain and ideal filtering. Its residual-carrier coefficient is a
pedagogical control. No adjustable phase knob is invented for the trainer.
The manual's AM-style envelope-index table is not used to grade DSB-SC. Virtual
amplitude is not a prediction of unspecified hardware gain.

Technical and native Odia reviews are pending. The pack is explicitly marked
`development_testing`. Exported receipts retain those review labels.

## Alternatives and rollout

Generating arbitrary 3D hardware at runtime was rejected: visual plausibility
does not validate terminals or behaviour. A separate service was unnecessary
for this local vertical slice. Rendering is frontend-owned; the backend provides
portable assets, semantic targets, state and observations. The included browser
harness is a development integration preview, not a replacement Kiki frontend.

Ship additive routes and content on the branch. Verify the first pack, then
add a different experiment to prove reuse. To roll back the feature, remove its
router/service registration; existing software-lab routes/data are untouched.
Preserve the separate physical preparation database for later migration.


## Demo mode addition — 21 November 2026

The user explicitly requested a demo that assumes prerequisite knowledge and
focuses on conducting the experiment with fewer clicks. Add an explicit
`experiment_demo` session mode; preserve `guided_preparation` as the API default.
The authored demo profile presets only controls and omits selected setup actions.
Validation rejects omitted connections/measurements and unsupported settings.
Actual wiring, null adjustment and readings are still checked server-side.

Demo completion is a distinct `experiment_complete` stage and result document,
not `prepared`. It cannot claim concept checks or a preparation receipt. Existing
normal sessions and their gates remain intact. Browser session references are
separate, and the original normal creation-body digest remains compatible.

The development preview defaults to direct demo mode, with a draggable guide
inside the apparatus workspace. Keeping the guide, readings and controls in the
same fullscreen subtree avoids disconnected browser popup windows. The guide
avoids current targets; camera movement and orbit/zoom remain available.
