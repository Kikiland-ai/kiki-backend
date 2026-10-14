# Current execution status

The JSON branch now implements the protocol and has completed bounded synthetic trials; see [the implementation record](json-stream-implementation.md). Its private test Site is a separate experiment, and a reliable progression-latency gain is not established. TOON remains prepared. The original preparation-time status below is historical.

# JSON streaming vs TOON streaming — shared experiment protocol

14 October 2026. Status: **prepared only**. No streaming runtime, paid trial or experimental deployment was added. Both branches must start from the same exact baseline commit and keep the [hosted baseline](../baselines/screen-reader-v1.md) available.

## Decision and hypothesis

Choose whether incremental generation materially improves the learner's first useful feedback and verified step progression enough to justify parser/delivery complexity. JSON streaming is the smaller initial integration change because Gemini already supports structured JSON. TOON is a parallel candidate for a compact table-based wire representation; it must decode into the identical canonical observation. Token count alone does not select a winner.

Branches are `experiment/screen-reader-json-stream` and `experiment/screen-reader-toon-stream`. Each carries an experiment config and build handoff. Implement/test independently, then compare each against the unchanged baseline. Never merge both feature changes into the baseline before measurement. The consolidated FastAPI composition is common infrastructure, locally tested but not the already-hosted runtime.

## Critical distinction: early feedback vs early advancement

Runtime provenance is already generated outside the model. Frame hashes, context, receipt times and IDs must be available **before** accepting any finding; they are not trailing model fields to wait for. Optional storage/logging can finish asynchronously after an atomic validated decision, with reliable persistence. Required evidence, uncertainty, cancellation state and provenance cannot be deferred.

An early complete JSON field or TOON row can show **provisional** feedback only. It does not increment support, move an action/checkpoint or replace canonical instructions. Preserve the baseline requirement for all current-checkpoint criterion/action IDs, statuses/evidence, critical uncertainties, full response validation and provider `STOP` termination. Partial, truncated, corrected, duplicated or stale output never becomes evidence. The frozen validator retains an empty-action-list compatibility path for old reviewed fixtures; the stream admission gate must enforce the intended full action set explicitly. Record that validation tightening separately from format and apply the same evaluation gate to the baseline arm. Two matching **distinct admitted frames** remain required; two chunks or two retries of one frame are not two observations.

If early fields improve reading comfort but verified progression is unchanged, report that as a perceived-responsiveness result. To advance before optional narrative completes, a later explicitly designed decision unit needs its own independent finalization/validation boundary, complete required evidence and current context. It could be a separately bounded completed primary response followed by ancillary work. It is a separate experiment from merely streaming one still-open generation. Do not silently relax full-response acceptance because a table or closing brace appeared.

## Common envelope and proposed transport

Keep observation/progress/canonical copy in Python. Use Gemini `streamGenerateContent` SSE upstream and a same-origin bounded SSE/fetch response downstream in the eventual implementation. This is **proposed transport**, not an existing route. Browser media capture stays 0.5 Hz sampled JPEG; WebRTC, video storage and provider/model changes are outside this comparison.

The trusted server creates an analysis request ID, immutable frame provenance and admitted context. A stream event has `request_id`, monotonically increasing `event_sequence`, `event_type`, server time and that frozen context. Suggested event types:

| Event | Meaning |
| --- | --- |
| `admitted` | Exact trusted frame/context admitted, no findings yet. |
| `provisional_findings` | Fully parsed IDs/status/evidence from partial output, clearly tentative. No support/progress mutation. |
| `observation_committed` | Entire completed response validated, context rechecked and atomic journal/projection update completed. Includes authoritative new now/next/queue state. |
| `analysis_failed` | Safe provider/parse/truncation/validation error, no partial evidence. |
| `discarded` | Changed visit/view/workspace/condition/parameter/lifecycle or aged/foreign frame; discard text as well as graphics. |
| `cancelled` | Local stream fenced; remote provider cancellation remains best effort. |

Deduplicate request/event IDs, reject older event sequences and late results after cancellation. Chunk boundaries are arbitrary bytes: buffer incomplete UTF-8, strings, JSON tokens/objects or TOON rows. Do not parse regex fragments or infer missing IDs. A reconnect/poll fallback obtains the authoritative projection, not a replay that counts tentative findings twice. State/event persistence must be idempotent. Screen-writing/v0.2 cue streams remain separate; analysis SSE is not a cue packet and rendering ACKs are not checkpoint evidence.

## Fixed controls

For a valid comparison, hold fixed model/version, exact JPEG/hash/dimensions, checkpoint/visit/workspace/condition, complete authored criteria/procedure, minimum two distinct matches, freshness deadlines, generation budget, thinking configuration, key/quota setup, admission cadence and UI instruction copy. Canonical output IDs must stay authored and stable. List every intentional representation/transport change; JSON key ordering is a prompt request, not a guaranteed semantic capability.

Use the same runtime/host for all three arms. A hosted Worker baseline and cloud-container FastAPI experiment are not an isolated format comparison. Choose either three isolated copies of the hosted runtime or run baseline and both experiments through the same Python deployment after its acceptance. Keep API consolidation independent and identical across arms. Same-project keys do not add quota; do not give one arm privileged fresh quota or a different fallback model.

TOON requires a pinned decoder version and a versioned strict grammar before implementation. Preserve stable IDs and arbitrary quoted Unicode/evidence safely. Retain critical uncertainty rather than hiding it behind a compact status code. Its output schema enforcement differs from Gemini JSON schema; record that confound rather than attributing every result to token savings. Do not reuse rejected positional-index compaction.

## Acceptance and replay cases

Use the four committed [synthetic images and expected focused findings](../../fixtures/screen-reader-baseline/manifest.json): correct Local carrier settings; wrong phase; Carrier mistakenly shown at the receiver checkpoint; obscured receiver wires. They establish focused labels, not broad actual Simulink accuracy. Expand held-out real-tool coverage only in a separately consented run; do not archive user pixels automatically.

Both implementations must also pass deterministic stream/runtime replay cases before any paid experiment:

- Fragment every byte boundary, escaped quotes/backslashes, multibyte Odia, braces/commas/newlines and quoted TOON delimiters.
- Missing, duplicate, foreign or reordered IDs; unknown/mismatch and later contradiction; hidden/offscreen target remains unknown.
- Incomplete response, non-STOP finish, invalid final schema, extra trailing content or parser size overflow: no support/action/checkpoint changes.
- Stale visit/view/workspace/parameter/condition, aged/foreign frame, pause/disconnect/revisit and cancellation midstream: clear provisional content; discard stale fallback too.
- Duplicate events/out-of-order response/reconnect: one final commit at most; two chunks of one frame never satisfy minimum matches.
- Provider 429/503/transport timeout, full failed-key sweep and recovery: keep capture/progress, use fresh frame after cooldown, no stream backlog.
- Save/explanation/report gates and wrong Carrier/Local identity unchanged; writer render success still cannot complete a checkpoint.
- First useful feedback and final result are attributed to the exact request/frame/context, including failure and discard cases.

## Instrumentation and measurement plan

Use server monotonic durations; retain server UTC timestamps and client-monotonic capture elapsed time with explicit clock domains. Browser-visible update time is a browser-local duration, not a calibrated absolute cross-device timestamp. Split or label routing/storage vs Gemini HTTP; existing `provider_ms` combines both.

Record, outside model-authored findings: arm/build/config/prompt/codec hashes; model/version; exact synthetic image hash; request ID/context; sample/pair/order; cache metadata; retries/key hash (never key); admitted time; provider first byte; first complete critical finding; first provisional browser display; provider STOP; full validation; atomic commit; next canonical instruction displayed; ancillary storage finished; input/output token count; outcome/error/accuracy labels. Logging must contain no credentials/private pixels.

Primary measures are **time to first useful visible feedback** and **time to verified canonical next action**, including the second matching frame. Keep provider generation, scheduling/queue delay, parse/validation, storage and browser display durations separate. Report p50/p95, success/discard/429/503/parse rates, token usage/cost and accuracy. Failed/timeout runs must remain in outcome denominators; a fast failure is not a latency success.

Cheapest staged plan:

1. Offline replay/semantic gates on both branches; stop on any false completion, stale-context adoption or malformed-stream acceptance.
2. When live trials are explicitly resumed, one small provider/protocol smoke per arm; establish that output/schema/termination work before expanding calls.
3. Predeclare an interleaved/rotating three-arm sequence: initially five repeats × four focused cases × three arms (60 calls maximum). Keep quota/budget fixed and stop on exhausted quota/unsafe output. Report descriptive paired results and uncertainty; this small pilot is not a production p95 claim.
4. Only if gates pass and the pilot is informative, schedule a separately agreed longer balanced run and actual Simulink user trial. Preserve baseline availability and user's saved lab.

Provisional practical threshold: at least 20% lower median first-useful-feedback time on paired runs, no accuracy/safety failure, and no more than 10% worse median verified-next-action time or higher failure rate. To claim **progression latency reduction**, require at least 20% lower median verified-next-action time too. These are proposed pilot decision rules, not already measured SLOs; freeze them before executing. A noisy/underpowered result calls for an explicit larger trial, not selective removal of slow/error runs. Any incorrect automatic advancement is an immediate stop/reject irrespective of token savings.

## Outcomes and rollback

| Outcome | Decision |
| --- | --- |
| JSON wins and all gates pass | Prefer the smaller JSON integration for the next controlled rollout. |
| TOON materially wins and all gates pass | Consider its parser/schema maintenance cost and held-out accuracy before rollout. |
| Only provisional feedback improves | Keep the gain labelled perceived responsiveness; do not claim faster checkpoint verification. |
| Neither improves or results are noisy | Keep baseline; choose the next bounded experiment from evidence. |
| Safety/accuracy regresses | Reject the branch implementation and retain baseline. |

No production rollout happens as part of preparing these branches. Record exact tested commits and result artifacts before discussing rollout. Revert/disable an experimental route to the untouched baseline implementation; do not migrate/reset the learner's scientific ledger or private live journal. Browser-local Gemma, alternate providers, prompt/context reduction and actual overlay acceptance remain later independent work.
