# Analysis-owned drawing producer: implementation v1

15 October 2026. Branch `experiment/analysis-owned-guidance-producer`. Builds on the published contract proposal `08229428a712a5cd3c71847490d09502a7a8d5da` and its [interface handoff](analysis-owned-guidance-producer-v0.1.md). “Producer v1” names this first implementation; wire contracts remain the proposed `lab-observer-drawing/v1`, `analysis-owned-guidance/v0.1`, `lab-analysis-stream/v3`, `committed-decision/v2` and unchanged `screen-writing/v0.2`. It is not a silent protocol promotion or evidence of renderer agreement.

## Implemented boundary

Python and isolated Worker adapters make one streaming model request for findings and bounded typed drawing candidates. Findings serialize first. Complete four-field JSON, all authored findings, drawing validation and provider STOP are required before findings reach the tracker. Invalid drawing tails reject the complete analysis. The existing three-field control stays the default, with its prompt/decision policy preserved. Drawing validators are lazy imports on the control path; the experiment's additional Python dependencies are isolated in [contract requirements](../../contracts/analysis_owned_guidance.v0_1.requirements.txt).

The provider schema expands local references, scopes finding/action/target enums to the admitted authored catalogue, uses structural `anyOf` alternatives and omits unsupported conditional/pattern annotations. The independent full contract and runtime semantic validation remain mandatory. Provider acceptance of this compiled schema has **not** been tested with paid generation. Runtime evidence clauses retain the existing 180-character bound (a stricter subset of the proposal's 300-character model limit). The output token limit and routing/context modes remain unchanged.

Python exports:

- `prototypes/json_stream/guidance.py`: `DrawingRun(admit, trace=None)`, exact JPEG/hash/dimension admission, schema compilation, semantic validation, `build_committed` and `committed_state`.
- `prototypes/json_stream/guidance_check.py`: `check_with_drawing(service, lab_id, owner, body, *, run, outbox, stream_id, project_runtime)`. Call only from an authenticated, explicitly negotiated SSE adapter with `STREAM_SINK` installed. It invokes the real `LabService.check`, then the guarded drawing outbox and returns a proposed `guidance_committed` event with `state.screen_guidance`. It does not create a route or send/paint that event.
- `prototypes/json_stream/guidance_outbox.py`: explicit `GuidanceOutbox(store)`, installed only when invoked. Uses the existing single-instance SQLite `LabStore`, `BEGIN IMMEDIATE`, owner/session/revision matching, durable stream sequences, publication IDs, cancellation fences and atomic outbox append. A cancellation also fences any analysis admitted at or before its revision, so assigning a higher sequence cannot revive a cancelled request. Duplicate publications roll back without consuming a sequence. This is **not** a D1 or cross-service transaction implementation.
- `prototypes/json_stream/guidance_trace.py`: `GuidanceTrace` writes allowlisted `guidance-producer-timing/v1` records through an injected logger. No screenshots, keys, teaching text or raw provider errors are logged.

`admit(pixels, checkpoint, state)` must synchronously derive an `analysis_input` from the exact trusted admission. Integration owns the authored eligible current/immediate-successor catalogue, owner-bound immutable frame retention/handle and source binding. This callback is not a client/model-supplied packet. `project_runtime(state)` runs synchronously inside the outbox transaction and must derive the current action and canonical instruction from tracker state, matching current frame/source/owner records. It supplies expected finding IDs, UTC time and trusted live capability records. No I/O/await is permitted inside that callback. The helper checks the actual persisted revision/context and selects only the resulting current action; absent successor geometry yields a full no-cue replacement. It does not infer new teaching instructions.

Worker exports in `prototypes/json_stream_site/worker/guidance.js`: `DrawingRunJS`, `DrawingFindingParserJS`, `runDrawingAnalysis`, `buildCommittedDrawing`, `GuidanceTraceJS`. The existing `analyzeLabFrameStream` takes an optional final `drawingRun` argument; its default call remains control. The new helper is deliberately **not included in the shared builder/routes**. Worker projection is pure and does not allocate durable sequences, append D1 outbox rows or publish events. Integration must add that atomic adapter before connecting delivery. `guidance-contracts.js` contains pinned local schema constants; regenerate only with `python scripts/sync-guidance-contracts.py`, verify with `--check`. The Worker validator supports the exact pinned vocabulary and is checked against independent Python schemas/fixtures; it is not a general-purpose JSON Schema library.

No existing Site, baseline, shared `assets/lab.js`, build script, route, generated Worker bundle, model key, learner state, control branch or PR #1 code is changed or deployed by this implementation. Test builds may regenerate the local bundle transiently; it must not be committed on the producer branch.

## Streaming race behavior and remaining integration work

A `DrawingRun` is private to one request. Analysis uses its immutable admitted pixels while newer periodic frames continue arriving. Provisional findings never update progress or draw. `LabService` still conditionally saves against its expected revision; view/visit/parameter/source invalidation during analysis prevents an obsolete result from saving. Drawing publication separately checks the latest persisted tracker revision, then atomically allocates its sequence and appends the packet. Tracker save and outbox append are two transactions: an intervening invalidation suppresses the drawing publication; it does not undo previously valid tracker evidence. Invalidation/cancellation append must be wired by integration, not inferred from the presence of the helper.

The producer does not implement browser panel updates, request-generation fences, latest-waiting-frame coalescing, live content-motion detection, source proof, transforms or verify-to-paint serialization. The integration/renderer must keep “What I can see” as one coherent accepted snapshot, reject queued callbacks/old tails, discard stale fallback text, and clear local marks immediately on invalidation. Ordinary frame arrivals/hash changes must not continuously cancel otherwise valid analysis. Same-layout content changes still require actual live freshness checks. Existing packet expiry remains capped by creation +8 s, receipt +20 s and handle expiry.

Outbox callers must send ordered cancellation on pause/disconnect/action/view/parameter invalidation, retire streams at attachment boundaries, and recover/reconcile persisted outbox messages under authenticated ownership. Completed labs need a terminal cancellation using the last authoritative non-null checkpoint/visit context; the current helper is bounded to an active-checkpoint attachment. New origin allowlisting, owned negotiation, immutable handle serving, the Worker D1 outbox, terminal/attachment lifecycle, client application, final source/clock/paint validation and actual paint/exposure ACK persistence are integration gates. No boolean proof, returned packet or durable append establishes that anything appeared on Simulink. Rendering still never completes a checkpoint.

## Transparent measurements

Every JSONL record includes schema, experiment arm (`control` or `drawing_v1`), run/paired case/request IDs, event sequence, runtime, configuration ID, source revision/fingerprint, model, sample kind, stage, sanitized reason and server UTC timestamp. `elapsed_ms` uses one local monotonic clock; never subtract elapsed values across different requests or runtimes. Integration must record real deployed commit/configuration identifiers rather than leave defaults.

Stages distinguish admitted, analysis validated, tracker committed, packet prepared/published, failed/discarded/cancelled. The Python orchestrator's `published` means **durable producer outbox append**, not browser delivery or paint. The Worker wrapper logs analysis; its commit/publication stages must be logged by the future D1 integration adapter. Existing routing/context counters and provider-reported input/output/cache/thinking tokens are retained. Missing token counts remain null, not guessed. Provider offsets include retries; compare first-attempt and retried samples separately using `provider_http_attempts` instead of silently excluding retries. Packet/frame age and packet preparation are logged after outbox append. No renderer/ACK timing is fabricated.

Analysis timings include first finding, critical findings ready, drawing field ready, provider STOP, full validation, request preparation and the remaining drawing/validation tail. These overlap; they are not additive stage durations. Python/Worker base request preparation starts at slightly different existing boundaries, so compare within the same runtime. Extra drawing tokens and schema/catalogue input are a real cost on the full-response critical path; one request eliminates a second localization call but does not guarantee a latency improvement.

A [retained offline evidence bundle](../experiments/analysis-owned-guidance/producer-v1-evidence/) contains the raw logs, comparison, acceptance records and checksums.

Run the complete free experiment checks:

```sh
python -m pip install -r prototypes/screen_capture/requirements.txt -r contracts/analysis_owned_guidance.v0_1.requirements.txt
python scripts/run-guidance-evaluation.py --full
```

Artifacts are written to ignored `work/evaluations/guidance-v1/`: each check's log, `acceptance.json`, raw `timings.jsonl`, `comparison.json`, and full existing reader-regression artifacts. A new experiment-only GitHub workflow runs this command on producer-branch pushes and retains artifacts for 14 days. It uses no API secrets. The existing reader workflow/PR #1 remain unchanged.

The paired replay alternates order and executes the real Python streaming analyzer/provider pool, parser, tracker and (drawing arm) SQLite outbox against synthetic JPEG/findings through a mock HTTP transport. It includes an authored box candidate. It measures local overhead and request size, **not model generation/network/renderer latency or recognition quality**. Tokens stay null. The 10 control +10 drawing requests must all pass; failed/discarded records remain in the JSONL and comparison denominators. This is no substitute for matched live model/commit and renderer paint measurements.

To summarize future captured logs without rerunning a user lab:

```sh
python scripts/compare-guidance-traces.py path/to/control.jsonl path/to/drawing.jsonl --output work/comparison.json
```

Compare matching runtime/model/configuration/sample-kind groups and report all outcomes as well as per-metric sample count, median and p95. Partial, failed or discarded samples must not be silently turned into successful latency observations. The script reports pairing and source revisions; genuine live results must use `sample_kind=live_provider`. End-to-end rendering comparison still needs the renderer's separately correlated post-paint ACK.

## Acceptance and next action

Eleven isolated Python checks, eleven Worker checks and fifty independent reference cases pass. The existing reader regression suite also passes: 117 Python tests and 98 Node tests (87 existing plus 11 producer checks). Producer checks cover all proposal modes, single/multiple targets, successor/no-successor selection, exact pixels, foreign provenance, malformed/nonfinite/duplicate/incomplete output, private logs, periodic-frame arrival during a delayed analysis, view invalidation before tracker save, missing STOP, malformed drawing tail, outbox duplicate/ordering/cancellation fences and revision change between tracker save and publication. The Worker tests run its actual stream function with one controlled provider response. These checks do not run a browser/compositor or establish live interoperability.

Next: renderer reviews this implementation and fixtures. Integration wires negotiated private transport and an atomic Worker outbox, then runs the shared capture-to-committed-to-paint acceptance against a new private Site. Preserve the current latency Site and control until that gate passes. Compare added model-generation/commit latency and actual paint time before deciding whether to promote drawing.
