# Stream context batching — 15 October 2026

Current arm: `stream-context-batch/v1`, based on the frozen provider-I/O source `c67fc3a5537ddcf98b8d8bfacbb606749687f693`. Provider routing stays batched for the paired context comparison. `KIKI_STREAM_CONTEXT_MODE=per_chunk` is the default; `per_event` is the control/rollback. No model input, prompt, output schema, progress policy, key pool or deadline changes.

Already decoded findings from one incoming provider byte chunk share one fresh authoritative context read. Empty fragments need no read. No context is cached across chunks, no timer holds findings, and no partial response can commit. Pause/view/visit/parameter/workspace/capture fences and final durable-save context/freshness checks remain. SSE v2 event shapes/order are unchanged. Python can yield several SSE messages in one byte chunk; consumers must use normal SSE framing rather than assume one message per network read.

New timing fields: `context_validation_mode`, `context_batches`, `context_events`, `context_max_batch`, `provider_chunks`, alongside `context_db_reads/ms`. These permit automatic measurement during ordinary use. Raw chunk count includes empty fragments and all attempts, so use context batches/events to assess effective batching. Python delivery checks have separate tail-only `context_delivery_db_reads/ms` counters.

The backend's free `python scripts/run-screen-reader-evaluation.py` gates the arm with both complete lab replays, malformed/fragmented streams, changed views/visits/pause, last-finding-before-STOP races, disconnect, wrong settings and two-frame progress rules. `node scripts/benchmark-context-batch.mjs` compares one, three and seven event-bearing chunk groups under injected DB delay, retaining the no-gain case. These automated checks need no user screen-sharing run or paid API. Production gain remains unmeasured until the new code receives ordinary traffic.

---

# Provider database I/O arm — 15 October 2026

Current source implements `provider-db-io/v1`. `KIKI_PROVIDER_IO=batched` is the default; `serial` selects the unchanged routing control. The model prompt, three-field decision schema, SSE v2, authored IDs, complete STOP and two-frame gates are unchanged. Healthy four-key routing uses four DB calls rather than seventeen, including three before HTTP rather than fifteen. This count reduction is not a production end-to-end latency claim.

Private timings now include provider DB operations/time, first dispatch, HTTP headers/consumption, context DB reads/time, actual prompt/cache/thinking/output/total token usage, image bytes and text characters. Null token fields mean the provider did not supply a valid count. HTTP duration includes awaited stream parsing/context checks; these phase timings overlap and must not be summed. `/health.latency_experiment` identifies the selected mode.

Run `node scripts/replay-lab.mjs --io-mode batched` and again with `serial` for a full twelve-checkpoint synthetic replay through the actual Worker/receiver/tracker. This uses mocked vision, explicit simulated student confirmations and two distinct matching frames. It injects contradictory settings to verify support reset. `node scripts/benchmark-provider-io.mjs` is an offline DB-delay simulation, not a live provider benchmark. Existing `node --test scripts/test-*.mjs` covers stale contexts, cancellation, lease contention and quota/failover semantics. No default command calls a paid API.

The backend experiment branch contains the combined evaluation command, CI workflow, experiment registry and optional five-case live vision smoke. The existing Site remains Worker/D1; the Python FastAPI mirror is implemented/tested but not hosted. Native browser sharing and real Simulink readability still require sampled integration acceptance.

---

# JSON streaming experiment

This is the private hosted compatibility adapter for the Python implementation on `experiment/screen-reader-json-stream`. The frozen baseline Site is unchanged.

The experimental stream emits trusted session/frame context, full-ID tentative criteria/actions, confirmed canonical guidance, then the full state/timing tail. Whole output/provider STOP/current context/two-distinct-frame gates still own progress. Save/explanation gates remain explicit and unassessed.

The model prompt is dsb-step-observer/v3-json-stream2. A first v1 smoke inferred occluded wires; it was rejected. v2 adds mandatory entire-path occlusion rules and exact array counts. Five controlled cases including a positive fully-visible wiring check passed in streaming and the same-prompt buffered control. These are synthetic Google API checks, not actual Simulink accuracy or a production latency SLO.

The Site is still Worker/D1 because Python hosting is unconnected. The same stream protocol exists in FastAPI; publishing this Site does not deploy Python. Browser QA is unverified in this managed environment; Node stream/client and Python API tests cover the mechanisms. Runtime secret GEMINI_API_KEYS is configured separately on this new project, with a separate receipt signer.

Open the Site in its own tab, start a new lab, and share Simulink. JSON stream is the default. Progress and technical details shows feedback/confirmed-guidance/full-response timings and an optional Baseline JSON reference mode. Use separate runs for stage-duration comparisons; switching modes does not reset progress. The reference mode retains the frozen prompt, whereas the automated priority-buffered control uses the repaired streaming prompt.

Source and evidence: https://github.com/Kikiland-ai/kiki-backend/tree/experiment/screen-reader-json-stream
# Short-decision continuation — 15 October 2026

The experiment now uses `lab-observer-decision/v1` and `lab-analysis-stream/v2`. The model emits every required criterion/action finding and uncertainty, closes the short object and finishes with STOP. Validated evidence still needs two distinct matching frames; canonical instructions remain tracker-owned. Display summary prose is derived from validated evidence, without another model request.

Only after durable commit, `guidance_committed.state` supplies a bounded current projection. The client releases its verification slot from this event and can check a newer received frame while the state/timing tail continues. Tail errors or old snapshots cannot restore older guidance. Existing sessions, private audience and key pool are preserved; refresh old v1 clients. Provider deadlines/cooldown are unchanged. `commit_finished_ms` is post-save; auxiliary completion is timed separately.

The pre-change evidence record was published first in Kikiland-ai/kiki-backend at `47ae4669efac7ea281aa862891723167727e0d08`, `docs/experiments/json-stream-latency-checkpoint.md`. The current build record is `docs/experiments/short-decision-implementation.md` on `experiment/screen-reader-json-stream`. Five paired synthetic cases passed in both arms; this is not actual Simulink/browser latency acceptance.

The earlier implementation record below is historical.
