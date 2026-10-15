# JSON streaming latency checkpoint before the short-decision experiment

15 October 2026, Asia/Calcutta. Record the current experiment before changing its decision/commit path. The user reports that steps feel considerably faster and also reports a delay between apparent verification and the next instruction. Earlier feedback is demonstrated; faster completed checkpoints versus the frozen baseline are not yet established.

## Versions being compared

| Version | Immutable reference | Role |
| --- | --- | --- |
| Frozen screen-reader baseline | GitHub `681ad52d37ac0bfced86ceadeaaed6ef8128caf5`; Site source `4e1d0c3d132ff2778216e5d7e4d987d3e04d7145` | Original buffered JSON, original working Site; already includes 3 s active cadence and two-frame verification. |
| Current priority JSON stream | GitHub runtime `b0a00033038ed8d2558ab6bf55c3ea7d229d9312`; Site source `cbaec32e47bbb53e49aa5d1a1f6f02d76ad81adc` | Live at https://kiki-json-stream.woodsycarp256.chatgpt.site; deployment `appgdep_6acfddb9682081918e30cf9f9c558939`, environment revision 8. |
| Next short-decision variant | Not implemented or deployed when this record was created | Complete short model decision first, durable commit, then independent auxiliary delivery. No measured result yet. |

The live experiment is the Worker/D1 adapter. Python/FastAPI has a matching implementation but is not its hosted origin. Both existing Sites and their histories remain intact while this record is prepared. The frozen source document remains unchanged.

## What has improved

The buffered baseline exposes findings only after its response completes. The JSON stream exposes complete, identified criterion/action findings while the provider response is still arriving. In the four recent successful live checks, a first finding was parsed **2.905–3.144 seconds before the analyzer's provider call returned**, median **3.025 seconds**. This is an incremental-delivery lead within each request; it is not a paired baseline speedup or a browser paint measurement.

The user independently describes the steps as considerably faster. Preserve that as real usability feedback rather than converting it into an unsupported percentage improvement. The implementation also sends a small committed canonical guidance event before the larger state snapshot. Browser timestamps showing how much this second change saves were not retained in the inspected logs.

## Historical baseline and latest live sample

The baseline numbers below come from the already published [baseline record](../baselines/screen-reader-v1.md#measured-latency-and-rejected-alternatives). A fresh native log query did not recover those older check invocations. The current numbers are reproduced in the [sanitized observation report](evidence/2026-10-15-json-stream-live-observation.json), collected from one bounded 100-event log page. Frame uploads dominate the page, so it does not cover the entire lab session.

| Measure | Frozen baseline sample | Current stream sample |
| --- | ---: | ---: |
| Successful check invocations retained | 13 | 4 |
| Completion timestamps, IST | 14 Oct, 23:38:28–23:40:56 | 15 Oct, 03:46:26–03:47:05 |
| Worker invocation wall time, median | 9.599 s | 10.920 s |
| Worker invocation wall time, range | 8.197–10.502 s | 10.595–11.302 s |
| First complete finding, analyzer-local median | Not exposed incrementally | 6.221 s |
| First finding to provider return, median | Not exposed incrementally | 3.025 s lead |
| Required arrays/uncertainties ready to provider return, median | Not exposed incrementally | 0.859 s remaining |
| Verified next-action/checkpoint transition latency | Not captured | Not captured |

These are different tasks/screens and provider-load windows, not randomized or paired runs. The current successful-request median is numerically higher; neither a causal full-response improvement nor a causal regression follows from this comparison. There is no established production p95 or completed-checkpoint speedup. Do not subtract the current analyzer-local first-finding time from the historical Worker wall time: the clock boundaries and samples differ.

### Clock boundaries matter

- `first_finding_ms` is stamped before the awaited database context read and event delivery. It is a parser-ready timestamp, not proof of when the browser displayed it.
- `critical_fields_ms` records parsed criteria, actions and uncertainties; it remains tentative.
- `provider_ms` includes key routing/storage and consuming the provider stream; it is not isolated model inference.
- `last_analysis_timing.total_ms` and `received_to_result_ms` are assigned in `worker/lab.js` **before** `guidedObserve` and the final `labSave`. Earlier conversational descriptions of these as saved-result timings were imprecise: they do not include the final durable checkpoint commit.
- Native Worker wall time includes server invocation work, but is not a calibrated capture-to-browser-display measurement. Client capture elapsed time and server UTC are different clock domains.

## Controlled comparison already retained

The final five synthetic cases used the same request/prompt per case in streamed and priority-buffered arms. The latter is a same-prompt transport control, not the original frozen prompt. There was one call per case/arm, so the following remain a small smoke result:

| Measure | JSON stream | Same-prompt buffered control |
| --- | ---: | ---: |
| Focused semantic acceptance | 5/5 | 5/5 |
| Median first feedback | 2.178 s | 2.307 s |
| Median complete validated result | 2.861 s | 2.307 s |
| Slowest complete result | 8.626 s | 2.469 s |

Every streamed call exposed a complete first finding 0.683–0.897 s before its own final result (median 0.768 s). Across arms, first-feedback medians differ by only 0.129 s and full completion was slower for streaming in this small sample. The proposed practical improvement threshold was not met. The slow fully-visible-wires case stays in the aggregate. Earlier rejected recognition trials and the invalid-output attempt also remain in the evidence archive; no selective exclusion is used to create a speedup claim. See [implementation and trial record](json-stream-implementation.md#recognition-gate-and-live-synthetic-trials).

## Failed checks and the countdown

The same latest log page includes two admitted failed checks at CP-DSB-06, completing at **03:47:32 and 03:48:03 IST**. Worker outcomes were cancelled after approximately 26.6 seconds. Four distinct key attempts recorded `provider_timeout_or_network_error`; none recorded an HTTP 429 or 503. Read-only pool inspection showed four failed keys, no retained lease, an empty quota-cooldown table and a retry deadline of **03:49:02.244 IST**. The complete failed sweep applies the existing sixty-second cooldown; the user's approximately thirty-second display was a remaining countdown, not a session-duration limit. Capture requests continued successfully.

Retain these failures alongside the successful timings. Four successes and two failures in this selected tail are not an entire-session failure rate. Logs do not distinguish provider slowness, transport interruption and local timeout expiry. The code has an eight-second multi-key attempt cap, a twenty-second provider budget and a twenty-five-second client timeout. Coordinating these limits remains a measured follow-up rather than evidence of quota exhaustion.

## Why the next instruction can still lag

The trace is grounded in the current source, with references below relative to `prototypes/json_stream_site/`:

1. `worker/stream.js` emits provisional rows immediately, but validates all fields and requires provider STOP before returning an observation. Even `critical_fields_ready` cannot update evidence.
2. `data/guided-policy.json` sets `minimum_matches: 2`. `worker/guided-progress.js` counts distinct source frame IDs; all checkpoint criteria, current condition and recent support must pass. A saved first match may still require another complete analysis. There is no intentional wait after `guidedFinish` has all required evidence: it changes the queue in that same call.
3. `assets/lab.js` holds `busy` until the entire stream returns, installs the full state afterward, and starts checks from `onFrame`. `assets/capture.js` schedules that callback after each upload, about every two seconds plus transfer time. The three-second start floor is measured from the previous start, so it is not an additional fixed three seconds after every long check.
4. The hosted `emit` awaits `labLoad` for each finding, adding serial database work while reading provider output. Its individual live contribution was not instrumented.
5. `guidance_committed` renders selected new instruction fields early, while `state_snapshot` clears that override before the full state is installed at stream completion. A capture callback can render the older state in that interval. This is a source-supported UI hazard, not a measured cause of a specific user delay.

Read-only verification at this checkpoint reran thirteen stream/cadence checks and the distinct-frame advancement test: fourteen passed. These controlled tests confirm mechanisms, not real Simulink semantic accuracy or a live speedup. Runtime source still exactly matches the published Site commit.

## Next experiment: freeze the measurement before changing the path

Keep the current stream as the pre-change reference. Implement the user-selected short-decision variant only after this record is committed. The authoritative model result must still contain every required stable criterion/action ID, status, evidence and critical uncertainty, validate completely, end with provider STOP and pass current-context/freshness checks. Two distinct matches, explicit confirmation gates, owner isolation and canonical server-owned instructions remain unchanged. Do not treat a partial `match` or `critical_fields_ready` event as checkpoint completion.

The decision call should finish before auxiliary summary/history work, releasing its provider reservation. A committed event should carry enough bounded state and revision/context for the client to apply the next instruction and release its verification slot without waiting for the auxiliary tail. Tail events must be tied to their request/revision/observation; they cannot restore stale instructions, overwrite newer state or complete checkpoints. Optional summary work can be derived from validated evidence rather than automatically adding another paid model call.

Record these boundaries for each attempt: admission, first finding, decision STOP/validation, durable commit finish, checkpoint/action change, guidance event sent, browser guidance applied, verification slot released, next frame check started and auxiliary completion. Pair request IDs with exact frame provenance and checkpoint/visit/view/condition. Use monotonic durations within each clock domain; never infer capture-to-display timing from unsynchronized clocks.

Compare the new variant with the current stream on the same hosted runtime/model/key-pool configuration, matching authored tasks and held-out fixtures. Keep all outcomes, retries and incorrect/unknown findings. In the real lab, measure the second matching read through the actual next instruction, not only the first visible finding. Apply the [existing comparison thresholds](screen-reader-streaming-comparison.md#instrumentation-and-measurement-plan): at least 20% lower median verified-next-action time to claim progression improvement, with no incorrect advancement or weakened acceptance gate. Report first-feedback and full-response changes separately. Larger balanced samples are required before a reliability or p95 claim.

Last completed action when this record was written: inspect current logs/pool state and trace scheduling/commit/display code without changing it. Next action: publish this evidence checkpoint, implement and verify the short-decision variant, then let the user test its live link against this retained reference.
