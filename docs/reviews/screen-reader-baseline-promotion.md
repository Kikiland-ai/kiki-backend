# Reader baseline promotion outcome

15 October 2026. **PR #1 merged following explicit user authorization.** Merge commit [`7c986dfb86daa2d8d939061db42ab576c7d4a183`](https://github.com/Kikiland-ai/kiki-backend/commit/7c986dfb86daa2d8d939061db42ab576c7d4a183) incorporates checked head `ae234dcdd78b91ef7d6e6b528b14f2e9196808bb` into `baseline/screen-reader-v1`. Hosted acceptance run [38718998905](https://github.com/Kikiland-ai/kiki-backend/actions/runs/38718998905) passed. There were no reviews or unresolved review threads at merge. The earlier CI failure remains in the trace below.

The user's later merge instruction supersedes the draft/wait status in the archived review below. It does not establish unreported native checklist results or full twelve-checkpoint acceptance. No Site was deployed and `main` was unchanged. Original baseline commit `681ad52d37ac0bfced86ceadeaaed6ef8128caf5` remains the immutable original comparison point.

The producer experiment incorporates this baseline merge separately. Continue producer/renderer integration and measured acceptance, promote accepted combined changes into baseline, then promote the tested baseline into `main`. See the [producer v1 build and integration boundaries](../handoffs/analysis-owned-guidance-producer-v1-build.md). This outcome is recorded on the producer continuation branch; the merge commit itself retains the historical review text.

## Archived pre-merge review record


Draft PR: [Kikiland-ai/kiki-backend#1](https://github.com/Kikiland-ai/kiki-backend/pull/1).

15 October 2026, Asia/Calcutta. Status: **draft PR; manual acceptance pending; do not merge yet**. The user requested the accumulated improvements be proposed to baseline, with a traceable record, and will do one manual acceptance run before deciding to merge.

## Exact review and test targets

| Item | Immutable reference / role |
| --- | --- |
| PR base | `baseline/screen-reader-v1`, currently `681ad52d37ac0bfced86ceadeaaed6ef8128caf5` |
| PR head branch | `experiment/stream-context-batch` |
| Last runtime implementation | `9af91d6d3019b602d506d4f3ef2a31662fe4c998`; subsequent review commits change documentation and CI failure reporting only |
| Manual test URL | https://kiki-json-stream.woodsycarp256.chatgpt.site |
| Exact deployed Site source | `c83ec7e6664025b7ca01d06f208af009269f8ad2`, also pinned by [SOURCE.json](../../prototypes/json_stream_site/SOURCE.json) |
| Successful deployment | `appgdep_6ad0a54cafe881919db038cc07bf6f61` |
| Saved Site version | `appgprj_6acfd4c6e6e48191b9110067ba86d556~appgver_60818f2b70d0819199581aad03e2c222` |
| Runtime configuration | Existing owner-private Site; environment revision 8; existing keys, receipt signer and saved sessions |
| Archived control | Baseline source/fixture [manifest](../baselines/screen-reader-v1.manifest.json) and original Git SHA remain immutable references even if the baseline branch later advances |

This PR targets the baseline branch, not `main`. Opening it does not promote the baseline runtime or change the original baseline Site. The existing experimental Site already serves the proposed runtime. This review/documentation step does not redeploy it. A failed PR check also led to adding bounded offline failure output to CI console logs, without changing application behavior. A later Git merge and any baseline Site rollout are distinct actions; this session performs neither.

## Before and after

Baseline buffered verification waits for the complete model response and state update. The proposed path admits exact frame provenance, streams complete stable-ID findings as tentative feedback, commits a short complete decision after all validation, and lets the browser adopt the bounded canonical now/next state before auxiliary history/timing delivery finishes. A blocked or failed auxiliary tail cannot delay a new verification or roll back newer guidance.

The full branch includes these implemented slices:

1. **Guarded JSON streaming:** incremental UTF-8/JSON/SSE parsing; exact authored criterion/action IDs; duplicate/missing/foreign/truncated-output rejection; owner/same-origin admission, frame provenance and stale-context fencing.
2. **Short decisions and independent delivery:** model returns `criteria`, `action_findings`, `uncertainties`; the server derives display prose without a second model call. Full JSON and provider STOP remain mandatory. `guidance_committed.state` releases the client verification slot before the larger auxiliary tail, subject to the existing cadence and fresh second-frame rules.
3. **Provider database I/O:** atomic lease acquisition, one deduplicated health snapshot per attempt, durable cursor reservation before HTTP and combined successful release. Healthy four-key routing uses four DB operations rather than seventeen. Snapshot refresh after 429 preserves shared-project quota behavior; key rotation, 503 failover, cancellation, deadlines and failed-cycle cooldown remain.
4. **Stream context batching:** findings already decoded from one provider transport chunk share a fresh current-state read. There is no TTL cache, artificial waiting timer or reuse across event-bearing chunks. Final authoritative context/freshness/durable-save validation is retained. Python also batches/rechecks queued provisional delivery.
5. **Automatic regression and telemetry:** full lab replay, chunk-shape and routing A/B, phase/token metrics, retained positive/negative evidence and an offline CI workflow. These replace repeated manual lab runs for routine regressions.

Canonical teaching instructions, placement/settings procedure, learner confirmations and the twelve-checkpoint DSB-SC/coherent-recovery experiment remain authored by the tracker. Model findings and rendering acknowledgements cannot complete a checkpoint. An automatic checkpoint still requires two distinct supporting frames; hidden controls/paths are unknown rather than invented evidence. Saving, identity and written-response gates remain explicit/unassessed as specified by the baseline.

## Reviewer reading order

| Area | Files to review |
| --- | --- |
| Parser and model contract | [parser.py](../../prototypes/json_stream/parser.py), [analysis.py](../../prototypes/json_stream/analysis.py), synthetic [manifest](../../fixtures/json-stream/manifest.json) |
| Provider lifecycle | [provider.py](../../prototypes/json_stream/provider.py); hosted [provider.js](../../prototypes/json_stream_site/worker/provider.js) |
| Context and SSE delivery | [api.py](../../prototypes/json_stream/api.py), [context_batch.py](../../prototypes/json_stream/context_batch.py); hosted [stream.js](../../prototypes/json_stream_site/worker/stream.js), [context-batch.js](../../prototypes/json_stream_site/worker/context-batch.js) |
| Committed state and client scheduling | [decision.py](../../prototypes/json_stream/decision.py), [stream client](../../prototypes/json_stream_site/assets/json-stream-client.js), [guide client](../../prototypes/json_stream_site/assets/lab.js) |
| App/container/frontend wiring | [app.py](../../prototypes/backend/app.py), [Dockerfile](../../deploy/fastapi/Dockerfile), [API handoff](../handoffs/frontend-api.md), [OpenAPI](../../contracts/frontend.openapi.json) |
| Automated acceptance | [runner](../../scripts/run-screen-reader-evaluation.py), [lab replay](../../prototypes/json_stream_site/scripts/replay-lab.mjs), Python `tests/test_json_stream.py`, `test_provider_io.py`, `test_context_batch.py`; hosted `scripts/test-*.mjs`; [CI](../../.github/workflows/screen-reader-evaluation.yml) |

The approximately 18,000 added lines before this review record largely include the separate hosted adapter snapshot, copied lesson/policy data, generated Worker bundle and retained trial reports. Review modular `worker/*.js` and `assets/*.js`; `worker/index.js` is their reproducible generated build. Original `prototypes/screen_capture`, `prototypes/lab_tracking`, `prototypes/hosted_screen_reader`, pinned product sources and screen-writing/v0.2 contract remain unchanged against the PR base. The original frozen-source checker still passes. The copied adapter's historical README/BASELINE sections describe earlier states; its current [experiment record](../../prototypes/json_stream_site/docs/json-stream-experiment.md) and source marker take precedence.

## Chronological trace and evidence

| Commit | Change | Detailed record |
| --- | --- | --- |
| `ec9cd4c` | Isolated JSON experiment preparation | [initial plan](../experiments/IMPLEMENTATION.md) |
| `08f1d89` | Guarded stream, client and private Site; retained rejected/accepted synthetic trials | [JSON implementation](../experiments/json-stream-implementation.md), [decision 0006](../decisions/0006-priority-json-streaming.md) |
| `b0a0003` | Accurate SSE OpenAPI description | [frontend contract](../../contracts/frontend.openapi.json) |
| `47ae466` | Recorded pre-short-decision production evidence | [latency checkpoint](../experiments/json-stream-latency-checkpoint.md) |
| `d333908` | Complete short decision and independent committed-state delivery | [short-decision record](../experiments/short-decision-implementation.md) |
| `42afb87` | Separated experiment definitions and acceptance gates | [registry](../experiments/latency-experiment-registry.json), [experiment plan](../experiments/latency-experiments.md) |
| `121aee9`, `4c3dd6f` | Provider DB I/O, replay/CI and verification limits | [provider-I/O record](../experiments/provider-db-io-implementation.md) |
| `9af91d6` | Fresh per-chunk context batching and fragmented/stale acceptance | [context-batching record](../experiments/stream-context-batch-implementation.md) |

The records link exact Site source/deployment IDs, model/prompt/image hashes and machine-readable reports. Rejected occluded-wire trials, invalid responses, timeouts and slower cases remain in the evidence; do not select only successful/faster outcomes. TOON streaming, verifier-input simplification, targeted crops and live Simulink annotation rendering are not implemented by this PR.

Evidence supports different claims at different levels:

- A five-case synthetic real-model smoke passed focused findings in both prior-stream and short-decision arms. Median complete model result was 6.725 -> 5.574 s; this small coding-cloud sample does not certify all checkpoints or deployed performance.
- Provider routing removes 17 -> 4 healthy DB calls, including 15 -> 3 before HTTP. This is a query-count reduction, not a 76% end-to-end latency claim.
- With artificial 300 ms context-read delay, seven events in one/three/seven groups took 0.301/0.902/2.104 s with batching versus about 2.1 s per-event. The fully fragmented no-gain case is retained. Actual new production latency/retry improvement remains unmeasured.
- Frame checks and whole-checkpoint completion are different: a checkpoint may need a second matching screen, explicit learner reports or several authored actions. Provider/HTTP/context timing scopes overlap and must not be added as independent durations.

## Automated verification

Recorded implementation gate: **117 Python tests and 87 Node tests**, complete twelve-checkpoint synthetic replays in both context modes with provider routing held fixed, original routing controls, contradiction/support-reset checks, stale view/visit/parameter/pause and after-last-finding-before-STOP races, cancellation, blocked auxiliary tails and fragmented/coalesced streams. Replays use mocked vision and local SQLite, never a learner's live journal.

Also passed 130 pinned-source hashes, 31 frozen Python/43 hosted baseline files and fixture/policy parity, lab design, 39 writer-contract synthetic cases, BB8 validation/discovery/twelve reference tests and unchanged OpenAPI export at 29 HTTP paths. The new stream endpoint accounts for the baseline-to-head OpenAPI path addition.

```sh
python scripts/run-screen-reader-evaluation.py
```

The default runner makes zero paid calls, exits nonzero on failure and writes JSON/logs under `work/evaluations/latest/`. CI retains those reports for fourteen days. `--live` explicitly adds a bounded five-analysis synthetic vision smoke, including failures; no new paid calls are required for this documentation PR. DOM stubs are client unit tests, not native browser acceptance. Hosted CI results must be read from the PR checks; configured CI and passing local execution alone are not a hosted green check.

## One manual acceptance run before merge

Use the existing private test URL above and your Simulink Online model. Resume the saved run if appropriate; a reset or a new key is not required. Complete the scope you choose once, and record the actual start/end checkpoints. A partial manual run must not be recorded as native acceptance of all twelve checkpoints.

- [ ] Sharing starts, frames are received and the guide describes the intended model/view. Existing saved progress is coherent on resume.
- [ ] Follow the authored current action and at least its adjacent next action. Placement, settings and instructions are understandable; canonical guidance advances only after sufficient visible evidence, without waiting for auxiliary details.
- [ ] Unknown/hidden or wrong-block evidence encountered during the run does not falsely complete work. Tentative findings stay distinct from committed now/next instructions.
- [ ] Pause/resume guidance or change the shown view while a check is pending. Obsolete findings/instructions do not revive after cancellation or replace the current step.
- [ ] If an explicit save or written-response gate is reached, it still requires the learner's action/report; mark this item not exercised if the chosen run does not reach one.
- [ ] Stop sharing and confirm capture stops and progress remains saved. Record any retry/error shown, rather than omitting slow or failed checks.

Record the result in the PR using this short form; do not paste keys or private screen images:

```text
Tested Site source: c83ec7e6664025b7ca01d06f208af009269f8ad2
Date/time (IST):
Browser / Simulink Online:
Checkpoint range:
Instructions and progression: pass/fail
Pause/view/stop/resume behavior: pass/fail/not exercised
Explicit confirmation/response gate: pass/fail/not exercised
Observed delays/retries or wrong guidance:
Merge decision: pending / approved after this test
```

Manual acceptance is currently **pending**. No result is prefilled as passed. A failed acceptance keeps the PR draft; fix/retest the affected behavior before requesting merge. No auto-merge is enabled.

## Compatibility, hosting and rollout

- The additional Python route is owned `POST /lab-sessions/{lab_id}/check-stream` with the existing `CheckFrame` request. SSE is explicitly `lab-analysis-stream/v2`; old v1 consumers must adopt committed-state handling. Partial findings/critical-ready events have no checkpoint authority.
- The model's streamed wire contract is `lab-observer-decision/v1`; the original nonstreaming `/check` remains callable. Python buffered analysis inherits the original nonstream pool; its batched optimization applies to streaming. The hosted shared router applies DB batching to both hosted request styles.
- The composed FastAPI app defaults to the streaming-capable analyzer/UI and exposes readiness metadata. It retains Python's native capture transport. Existing mixed-language text/audio APIs are already present in baseline and are not reimplemented here. Docker includes the new Python module and experimental UI assets.
- The live Site remains Worker/D1. A reachable persistent Python/FastAPI origin, text/audio Site bridge activation and real Simulink overlay integration are separate work. This PR does not claim any of them deployed.
- Current eight-second multi-key attempt cap, twenty-second provider budget, twenty-five-second client timeout, three-second start floor and sixty-second failed-cycle cooldown remain. Timeouts can still occur; key rotation does not create independent quota pools.
- No new database migration, secret rotation, original-baseline audience change or learner-history transfer is needed. The experimental source includes existing D1 migration files as part of its reproducible snapshot.
- Roll back only context delivery with `KIKI_STREAM_CONTEXT_MODE=per_event`, or provider DB routing with `KIKI_PROVIDER_IO=serial`, using the normal environment deployment. Full rollback is the recorded prior Site version/source. Do not silently reset learner data or force-rewrite the baseline branch.

The merge gate is the user's manual result plus acceptable PR checks/review. Merging the Git branch does not automatically switch the original baseline Site. Record the approved result and exact merge SHA in this trace when merge is subsequently authorized; this session stops with an open draft PR.

## PR check trace

PR-triggered acceptance run [38718645204](https://github.com/Kikiland-ai/kiki-backend/actions/runs/38718645204) passed on documentation head `41b87fc`. The next run [38718685987](https://github.com/Kikiland-ai/kiki-backend/actions/runs/38718685987), at documentation head `986b719`, failed the Node suite while Python, all replays, both benchmarks and integrity checks passed. The failed report was retained as artifact `11963996721`; it is not discarded or represented as a pass. Artifact retrieval to this executor is unavailable, so the runner now also prints bounded failed offline logs to the CI console for investigation through the supported job-log API. Runtime and deployed Site source are unchanged by this diagnostic addition. Manual acceptance and merge remain pending.
