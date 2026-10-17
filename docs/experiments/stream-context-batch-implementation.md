# Stream-context batching without a manual lab run

15 October 2026. The user cannot promise repeated manual testing and authorized continued implementation. The free automated evaluation is now the release gate for this orchestration change. Native screen sharing/Simulink usability remains a sampled integration boundary, rather than a blocker on every code change.

## Experiment boundary

Branch `experiment/stream-context-batch` was fast-forwarded from its prepared registry ref to the validated provider-I/O control `4c3dd6f57b3da435b8b74ab534a926e4255f6850`. No history was rewritten. The provider-I/O branch remains frozen and both context arms retain its batched provider routing. The comparison changes context delivery only, rather than silently comparing old serial routing with the new context policy.

Prior Site source is `c67fc3a5537ddcf98b8d8bfacbb606749687f693`; new exact Site source is `c83ec7e6664025b7ca01d06f208af009269f8ad2`. `KIKI_STREAM_CONTEXT_MODE=per_chunk` is the default; `per_event` is the selectable control/rollback. `KIKI_PROVIDER_IO=batched` remains fixed for the context comparison. Original buffered/JSON/TOON baselines and the separate verifier/targeted-vision branches are untouched.

## How it works

Before this change, each finding awaited its own current lab-state read, including multiple findings already received together. The previous live first-attempt sample had seven such reads taking about 2.13 s. The eight-second HTTP attempt timeout also covers consuming the stream and these awaits, so provider slowness and local database work can combine to trigger a retry.

Python/FastAPI and the hosted Worker now collect complete parser events from one already received provider transport chunk. The events share one **fresh authoritative state read**, then are delivered in order as tentative findings. An empty fragment does no read. Every subsequent event-bearing chunk revalidates. There is no TTL cache, extra timer, second model call or speculative checkpoint completion. Batches are bounded to 64 events and existing parser/SSE limits remain.

The Worker checks cancellation again after the asynchronous read and synchronously enqueues the validated group. Python queues a group and revalidates it at delivery, yielding one valid SSE byte chunk containing the group's messages. Python's extra delivery read is counted separately in the completion tail rather than falsely recording an early zero in committed state.

The tracker still requires complete valid JSON, provider STOP, exact authored IDs, current owner/session/visit/workspace/view/parameters/condition, fresh matching frame provenance and two distinct supporting reads. Final context validation and durable-save concurrency checks are unchanged. Tests mutate state **after the final tentative finding but before STOP**: pause, view/parameter changes and revisit still produce discard, never canonical commitment. Rendering remains separate from checkpoint evidence.

SSE remains `lab-analysis-stream/v2`; event shapes, ordering and meaning are unchanged. Multiple SSE messages per byte chunk are standard framing; clients must not assume a one-message/network-read relationship. The repository's direct iterator tests now parse SSE delimiters correctly. A malformed later row may suppress the pending tentative group from that chunk; no invalid decision can commit in either mode.

The model prompt, request content and output schema are unchanged. The Python short-decision prompt still hashes to `5dc012e6ebec4384d5bf2eaf20ce48c62abd53105b9bfb912aa63cc08a809711`. Parser critical-ready timing is now captured before the grouped delivery awaits in both new arms; do not interpret its difference from the older source as an isolated model-generation improvement. Durable commit/wall timing remain the comparison endpoints.

## Automatic evaluation and latency mapping

Run from the backend checkout:

```sh
python scripts/run-screen-reader-evaluation.py
```

CI runs this automatically on this branch's pushes and relevant pull requests, retains logs/JSON reports for fourteen days and needs no provider keys. It builds the real Worker and runs 117 Python/87 Node tests, complete twelve-checkpoint lab replays for per-event and per-chunk modes with provider routing fixed, retained provider-routing controls, pinned/frozen source checks and chunk-shape A/B. Explicit simulated student confirmations and wrong-setting/support reset remain in the lab replay. Vision findings are mocked; these tests establish orchestration behavior, not broad screen-recognition accuracy. No API calls or learner data are used.

[Retained offline evidence](evidence/2026-10-15-context-batch-offline.json) includes every trial and the no-gain case. Controlled seven-event context batches, one trial at an artificial 300 ms/read:

| Event-bearing groups | Per-event reads / measured time | Per-chunk reads / measured time |
| --- | --- | --- |
| 1 | 7 / 2.105 s | 1 / 0.301 s |
| 3 | 7 / 2.104 s | 3 / 0.902 s |
| 7 | 7 / 2.103 s | 7 / 2.104 s |

This models the measured scale of database cost. It is **not a deployed end-to-end speedup estimate**. Provider chunking controls the saving; fully fragmented findings can gain nothing. The default CI benchmark uses 20 ms/read, three alternating trials per shape, and asserts event parity and read counts rather than a flaky elapsed-time threshold. HTTP integration tests additionally exercise coalesced/separate SSE messages and byte-by-byte transport fragments through the real decoder, receiver and tracker.

The existing `--live` runner option adds a bounded five-case real-model synthetic recognition smoke without asking the user to open Simulink. No new paid trial was run here because no vision input/prompt changed. Broader recorded lab screens would expand recognition coverage separately. Synthetic fixture correctness cannot certify real browser permissions or actual Simulink layouts.

## Production measurement without a special user test

Each ordinary check now logs `context_validation_mode`, `provider_chunks`, `context_batches`, `context_events`, `context_max_batch` and context DB time/read count, alongside existing first-finding/commit/wall/usage/retry fields. Raw provider chunks include fragments without findings and all retry attempts; use effective batches/events to calculate the avoided per-event reads. Python's `context_delivery_db_reads/ms` are completion-tail metrics and do not mutate committed state. The hosted Worker has no separate Python queue/delivery read.

Future production logs can automatically be compared with the retained provider-I/O sample when the user next uses the guide normally. No special full lab rerun is required to instrument or release the change. Until traffic arrives, actual hosted benefit and retry-rate changes remain unmeasured; simulation is not substituted for that evidence. The same model, eight-second attempt cap, twenty-second provider budget and two-frame policy remain unchanged.

## Release checks and rollback

Also passed 130 pinned sources, 31 frozen Python/43 hosted baseline files and fixtures/policy parity, lab design, 39 screen-writing v0.2 cases and BB8 package/discovery/twelve reference tests. OpenAPI export remains unchanged at 29 HTTP paths. Native browser-control tooling is unavailable; no simulated test is described as a real screen-sharing trial. Python FastAPI is implemented/tested, while Sites still hosts the Worker/D1 adapter.

Rollback context delivery with server-side `KIKI_STREAM_CONTEXT_MODE=per_event` and the Site's normal environment deployment, or restore the prior exact Site version. No keys, database migration, private audience or learner reset is required. The first hosted GitHub Actions result is unverified because available run-list access was denied/limited to PR runs; local execution of the same command passes.

Published successfully on the existing private Site: https://kiki-json-stream.woodsycarp256.chatgpt.site . Exact source `c83ec7e6664025b7ca01d06f208af009269f8ad2`; deployment `appgdep_6ad0a54cafe881919db038cc07bf6f61`; saved version `appgprj_6acfd4c6e6e48191b9110067ba86d556~appgver_60818f2b70d0819199581aad03e2c222`; environment revision 8, MCP true, unchanged owner-private audience, keys and saved sessions. Publication is verified by the terminal native deployment result; actual production latency is not yet measured for this source.
