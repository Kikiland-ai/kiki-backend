# Experiment A — structured JSON streaming

Status: prepared, not implemented or deployed. Baseline: `681ad52d37ac0bfced86ceadeaaed6ef8128caf5`. Branch: `experiment/screen-reader-json-stream`.

## Hypothesis and controlled change

Streaming complete findings before the final JSON can improve first useful feedback with lower integration risk than changing representation. Keep the v3 full authored IDs, current-checkpoint criteria/actions, values/evidence and unknown semantics. Request actionable findings first, followed by summary/ancillary information, without assuming Gemini guarantees key order. Canonical instruction remains authored by the tracker.

The model still needs a full validated STOP response before final support/progress mutation. First complete fields are provisional. Actual verified advancement improvement is a separate measured result, not something promised by displaying early text.

## Build next, in order

1. Read `docs/baselines/screen-reader-v1.md`, `docs/handoffs/frontend-api.md` and the shared comparison protocol. Run existing offline checks; keep the original nonstreaming path callable for the baseline arm.
2. Add a separate Python streaming analyzer/transport using Gemini streamGenerateContent SSE. The existing `ProviderPool.post` is nonstreaming: deliberately adapt its durable lease/rotation/503/429/deadline semantics rather than bypassing them with a raw new API call. Cancel/discard partial output before trying another key; a fresh attempt starts a separate provenance/event sequence.
3. Reuse the original request builder and canonical validation. Add a bounded incremental JSON parser that handles arbitrary byte/UTF-8/string/object boundaries; publish only complete identified findings as tentative events. Reorder generation schema properties deliberately and record the prompt/request hash change; accept valid keys in any order.
4. Add an explicit experimental stream router to the composed app, preserving the original `LabService.check` admission, exact pixels, post-await context/freshness check, atomic save and two-distinct-frame progression. An analyzer may return a complete validated result through the existing seam while streaming provisional events to a per-request sink. Do not count sink events as observations. `prototypes/lab_tracking/service.py` owns final acceptance; do not recreate its logic in the browser.
5. Connect a separate experimental client with labelled tentative feedback, canonical final projection, dedupe/fences, pause/context cancellation and ordinary poll fallback. The frozen baseline frontend remains usable. Proposed stream event names are in the shared protocol, not live endpoints yet.
6. Pass offline negative/replay cases and the existing suites. Record source/build/request hashes before a deliberately resumed provider smoke and paired trial. No new provider calls/deployment are authorized merely by opening this prepared branch.

## Output and return contract

Return exact implementation commit, OpenAPI/SSE contract and typed event examples, parser/transport dependency versions, offline cases, any changed frozen-source files, safe result report and unresolved backend/edge/browser responsibilities. Separate provisional-feedback latency from verified next-action latency. Keep screen-writing/v0.2 intact; writer ACKs never complete lab work.

Configuration is `docs/experiments/experiment.config.json`, descriptive only. It is not read by the runtime and leaves the experiment inactive. Both experiments start from the identical baseline; API consolidation must remain identical across arms. Actual overlay acceptance and Python cloud hosting are separate gates.
