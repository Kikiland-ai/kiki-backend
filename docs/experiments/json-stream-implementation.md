# JSON streaming implementation and test record

Current continuation: [short-decision implementation](short-decision-implementation.md) introduces the complete three-field decision and `lab-analysis-stream/v2` committed-state handoff. The original v1 implementation/trials below are retained as historical comparison evidence.

The [pre-short-decision latency checkpoint](json-stream-latency-checkpoint.md) records the first real user trial, sanitized timing evidence, timeout/cooldown findings and the code-level gap between early recognition and checkpoint advancement. It preserves the frozen baseline comparison and the requirements for the next experiment. No verified progression-latency improvement is claimed.

15 October 2026 (Asia/Calcutta). Implemented on `experiment/screen-reader-json-stream`; separate private test Site at https://kiki-json-stream.woodsycarp256.chatgpt.site. Native deployment appgdep_6acfddb9682081918e30cf9f9c558939 succeeded with environment revision 8 and MCP enabled. The frozen baseline branch and its working Site are unchanged; TOON remains prepared only.

## What arrives first

1. `admitted`: server request ID/sequence, exact trusted frame ID/hash/dimensions/receipt metadata and frozen checkpoint/visit/workspace/capture/view/parameter/condition context. Provenance is server-generated immediately, never delayed model output.
2. `provisional_findings`: complete criterion objects first, then complete authored action objects. They are tentative, bounded, uniquely identified and displayed as text. Critical uncertainties follow. The short summary is the final model field.
3. `critical_fields_ready`: required finding arrays and uncertainties have arrived; still no progress mutation.
4. After provider STOP, complete strict JSON/schema validation, current-context/freshness recheck and atomic evidence/journal save: `guidance_committed`, containing the canonical now/next/current action and queue.
5. `state_snapshot`: larger current projection/history, followed by `stream_complete` timing metadata. The browser can display confirmed guidance before decoding the remaining state snapshot.

A streamed finding never supplies a new instruction, increments support or completes a checkpoint. All current criterion/action IDs must be present exactly once. Two distinct admitted matching frames, explicit save/report gates, unassessed understanding and stale-context rejection are retained. Missing STOP, duplicate fields/IDs, malformed or truncated JSON, foreign frame/context, disconnect and cancellation cannot promote partial output.

## Python and hosted integration

- `prototypes/json_stream/parser.py`: incremental UTF-8 and strict duplicate-aware JSON/SSE parsing. Arbitrary byte/string/object boundaries; bounded buffers; no invented closers or positional IDs.
- `analysis.py`: priority request/schema and `JsonStreamingAnalyzer`. Nonstream calls keep the original analyzer. A request-local ContextVar connects provisional events without shared mutable timing state.
- `provider.py`: streaming body consumed under the durable key reservation; 503/transport fallback, shared-project 429 cooldown, nonconsecutive key selection and failed-cycle recovery retained. The twenty-second total budget and multi-key eight-second attempt cap remain, so long first-token/model work can still time out.
- `api.py`: authenticated same-origin `POST /lab-sessions/{lab_id}/check-stream`, using the existing `CheckFrame` body, LabService admission/atomic save/cancellation. Original `/check` remains callable.
- `prototypes/backend/app.py`: mounts the stream with feature readiness in `/health`; OpenAPI now exposes 29 HTTP paths. The container includes the new module.
- `prototypes/json_stream_site`: the separate Worker/D1 compatibility adapter and UI, copied from its exact pushed Site source. Original `prototypes/hosted_screen_reader` stays hash-frozen. No new D1 migration or user-history import was required.

Sites does not host this ASGI/Python process. The public-facing test URL runs the matching Worker adapter until an actual persistent Python host is connected. This publication does not establish Python cloud hosting. The Site uses its own owner identity, D1 records, receipt signer and user-configured `GEMINI_API_KEYS`; baseline sessions/keys/access were not changed.

The packaged Sites helper was not available in this executor. The verified retained Worker template was built with its existing Node builder, pushed with the native Site-scoped credential through hidden stdin/process-only Git headers, then archived in the native publisher's required `.openai/hosting.json` + `dist/server/index.js` + `drizzle` layout. Initial packaging with `server/index.js` at archive root was rejected and corrected; no code/deployment change to the baseline was involved.

## UI and cancellation

The existing beginner now/next procedure stays primary. A separate “Tentative screen check” card shows complete field evidence while generation continues; it clears on replacement, failed attempts, context change, pause/stop and cancellation. It never draws in Simulink or modifies the model. Current/next copy changes only on a confirmed server event. Request IDs/sequences are fenced/deduplicated, and admission is matched against the selected frame/hash/dimensions/context before rows are displayed.

Progress and technical details displays browser-local first-feedback, confirmed-guidance and complete-response durations. These are not calibrated capture-to-display times. Baseline JSON is an optional reference mode; use separate runs for stage-duration comparisons because switching does not reset progress. This reference mode preserves the original frozen prompt. The automated priority-buffered control below uses the repaired streaming prompt to isolate transport effects.

Server `analysis_stream_timing` logs and `runtime.last_analysis_timing` record first byte/finding, critical fields, provider/check time, receipt age and output tokens where available. Provider duration includes routing/storage/HTTP; it is not isolated inference. Failed attempts do not supply the winning attempt's first-finding metric. Auxiliary timing is not evidence.

## Recognition gate and live synthetic trials

A first eight-call paired smoke found an occluded-wire false match in **both** the original baseline prompt and streamed v1. That trial is retained and rejected as a performance-win candidate. A first v2 check also rejected one response as invalid output; the precise cause was not captured. The schema now constrains both arrays to their exact authored item counts. Prompt `dsb-step-observer/v3-json-stream2` explicitly requires the entire connection path to be visible and forbids joining fragments through an opaque foreground window.

The repaired prompt/schema passed all four frozen focused cases in both streaming and priority-buffered control (eight calls), then passed a supplemental fully-visible-wiring case in both arms (two calls). That positive fixture was authored after the prompt was frozen, to check that the occlusion rule did not reject every wire. It is synthetic, not actual Simulink acceptance. Five labelled images, stable IDs, exact hashes and identical request/prompt hashes across those paired arms are preserved. Meanings/native language/mastery remain unassessed.

| Measure across the final five paired cases | Streaming | Same-prompt buffered control |
| --- | ---: | ---: |
| Focused semantic acceptance | 5/5 | 5/5 |
| Median first feedback | 2.178 s | 2.307 s |
| Median complete validated result | 2.861 s | 2.307 s |
| Slowest complete result | 8.626 s | 2.469 s |

Each streamed call exposed a complete first finding 0.683–0.897 s before its final result (median 0.768 s). This establishes incremental delivery in this small cloud-runtime smoke. It **does not meet the proposed practical latency-win threshold**, prove faster next-checkpoint advancement, estimate production p95 or establish deployed Site egress/actual user experience. One call per image/arm, provider/cache/load variance and synthetic screens limit inference. No slow case was removed from the final five-case summary. Twenty-two live calls were made across rejected and final smoke runs; all reports are retained under `docs/experiments/evidence/`.

To deliberately repeat, use `python -B scripts/compare-json-stream.py --live`; it makes paid calls and never mutates a learner lab. `--arms stream priority-buffered`, `--manifest fixtures/json-stream/manifest.json`, `--case` and `--output` select bounded trials. A larger balanced run and actual Simulink test are next evidence, not already completed.

## Checks and limits

105 Python tests pass, including nine new parser/stream/tracker/API acceptances. The new Site passes 61 Node tests, including ten stream/parser/client checks. These cover early row delivery before provider completion, admission provenance, unique IDs/fields, Unicode/fragmentation, full-response gates, stale visits/views, owner isolation, cancellation/latch and lease release, 503 key sweep/cooldown and guidance-before-snapshot ordering. Original 31 Python screen files, 43 hosted baseline files, four frozen image hashes and definition/policy parity remain unchanged. Pinned product sources and screen-writing/v0.2 are preserved.

Native browser QA/control was unavailable; no substitute browser was installed/launched. The publisher’s startup screenshot was inspected and shows the expected initial page; it does not test native sharing, SSE interactions or Simulink. Container hosting, deployed browser SSE behavior, real Simulink recognition/advancement latency and actual overlay acceptance remain user/integration tests. Finite provider quotas and first-token work still cause waits; streaming cannot eliminate them.

## Screen-writing consumer boundary

`lab-analysis-stream/v1` is an observation stream, **not** a `screen-writing/v0.2` cue stream. Provisional rows and `critical_fields_ready` are not admitted checkpoint evidence, canonical instructions or render packets. Wait for the committed state/current candidate and use its exact ephemeral frame handle. Frame IDs/hashes alone do not locate a semantic target. Continue to apply view/visit/condition invalidation and the separate renderer's cue sequencing, transforms, cancellation and delivery acknowledgements. Rendering never completes a checkpoint.
