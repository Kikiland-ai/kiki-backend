# Short decision before auxiliary delivery

15 October 2026. Implemented on `experiment/screen-reader-json-stream` after publishing the immutable [pre-change latency checkpoint](json-stream-latency-checkpoint.md) at `47ae4669efac7ea281aa862891723167727e0d08`. The original buffered baseline and pre-change Site source remain available by their recorded SHAs. This is the user-selected next JSON experiment, not the TOON branch.

Published successfully at https://kiki-json-stream.woodsycarp256.chatgpt.site. Exact Site source `958fd7fb4ae94e0af5ffe592a2fcb09f406af5fb`, deployment `appgdep_6ad006becae081919d16fa678134c2f6`, saved version `appgprj_6acfd4c6e6e48191b9110067ba86d556~appgver_1ddf6e67d61c8191ac9d10abf8e058da`, environment revision 8, MCP enabled, existing owner-private audience. Terminal status succeeded at 04:18:43 IST on 15 October. No reset, new secret or schema migration was needed.

## Runtime behavior

The model now returns a complete **three-field decision**: `criteria`, `action_findings`, `uncertainties`. All authored stable IDs/statuses/evidence and critical uncertainties remain required; no positional shortcut or partial decision is accepted. The model closes this object and ends with provider STOP. Its schema/prompt exclude summary prose. A bounded visible-state sentence is derived locally from validated evidence (mismatch first, then match, then unknown); there is no second paid summary request.

The parser/analyzer validate the entire short decision before returning. The existing service rechecks current owner/session/visit/workspace/view/parameters/condition, capture and frame age, updates the distinct-frame support counts, evaluates every checkpoint criterion and atomically saves the journal/projection. Only then does the server emit `guidance_committed`. The provider reservation and service verification slot are already released. The model does not author canonical now/next instructions, and one matching frame still cannot finish an automatically observed checkpoint.

`guidance_committed` carries a bounded `state` projection alongside its canonical guidance, queue, committed revision, admitted/current context and post-save timing. It includes the current candidate/provenance and tracking information needed to schedule the second read. Full evidence/history/learner-response collections are omitted; the owned GET and paginated journal remain available. The server continues the full `state_snapshot` and timing tail independently. There is no additional background state mutation or auxiliary observation evidence.

The browser's `startAnalysisStream` returns separate `committed` and `completion` promises. It applies the committed state and releases `busy` from the former, then can immediately verify the latest *different* received frame without waiting for another capture tick. The existing three-second start floor, provider deadlines and two-distinct-frame rule still apply. Tail failures cannot roll back the saved decision. Old snapshots never overwrite current guidance; replacement/context changes cancel old tail delivery, and request/revision/sequence fences prevent revival of stale instructions. The previous partial heading override has been removed, so the current instruction/settings/reason update from one committed state.

## Compatibility

The HTTP path/body remain `POST /lab-sessions/{lab_id}/check-stream` and the existing owned check request. SSE advances from `lab-analysis-stream/v1` to **`lab-analysis-stream/v2`** because `guidance_committed.state` is now the authoritative early scheduling boundary. The internal model wire format is **`lab-observer-decision/v1`**, prompt **`dsb-step-observer/v4-short-decision1`**. A v1 consumer must be updated/refreshed; it must not treat a provisional finding or `critical_fields_ready` as committed. The new parser helper can still consume v1 for controlled compatibility/reference tests.

Original `/check` remains the original buffered JSON/prompt. No database migration, key change, user reset or baseline Site publication is required. The experimental Site continues existing saved sessions after refresh. The consolidated Python app serves the new lab UI/client while retaining Python's native WebSocket capture implementation; Sites still runs the matching Worker adapter until a real Python cloud origin is connected. Screen-writing/v0.2 and renderer ownership are unchanged.

## Timing boundaries

The server now emits `commit_finished_ms` only for an actual committed decision, after the durable save, and `auxiliary_finished_ms` separately. Worker logs label `decision_committed` and `timing_scope`; a retained cooldown projection is not a fresh successful check. Existing analyzer first-finding/critical-field/provider clocks and their limitations remain. The browser details show first feedback, committed-event arrival and auxiliary completion on a browser-local clock. These are not calibrated capture-to-paint durations; actual complete checkpoint timing still needs the real user's second-read/next-instruction run.

The original eight-second multi-key attempt cap, twenty-second provider budget, twenty-five-second browser timeout and sixty-second failed-cycle cooldown have not been changed by this experiment. The short response reduces generated work but does not remove provider slowness or quotas. Coordination of those deadlines remains a separate measured follow-up.

## Bounded recognition and timing smoke

[Ten retained provider calls](evidence/2026-10-15-short-decision-paired-smoke.json) compare the previous full JSON stream (`stream-reference`) with the short decision (`stream`), one call per arm for each of the five saved synthetic cases, with alternating arm order. Both arms passed **5/5 focused semantic checks**, including wrong phase, wrong Carrier/Local identity, occluded paths and the fully visible positive-wire control. The same model, exact image hashes, authored context and token budget were used. Prompt/schema hashes intentionally differ; this measures the combined short-decision change, not an isolated transport effect. Provider/cache/load variance and the tiny sample limit inference.

| Measure | Previous full stream | Short decision |
| --- | ---: | ---: |
| Median first complete finding | 5.933 s | 4.664 s |
| Median complete validated model result | 6.725 s | 5.574 s |
| Median output tokens | 466 | 428 |
| Slowest complete model result | 8.710 s | 6.289 s |

The complete-result medians differ by 1.151 s (17.1% descriptively); first-feedback medians differ by 1.269 s (21.4%). Four cases completed faster and the hidden-wire case completed slower with the short decision (6.038 vs 4.968 s); it is retained. This does **not** establish a 20% verified-next-action improvement, a production p95 or a live Simulink speedup. The smoke runs in the coding cloud's provider path, not the deployed Site's browser/egress/storage path.

## Mechanism verification and next live test

Python and Worker tests hold the first auxiliary tail open, receive its committed core, verify the provider reservation is released and start a second owned check before that tail completes. Late first-response snapshots leave the newer revision intact. The actual UI scheduler is executed with DOM stubs to prove that a blocked tail does not hold `busy` and cannot restore the first reading. This is unit-level UI verification, not native browser sharing acceptance. Existing non-STOP, duplicate/missing/foreign IDs, stale context, disconnect, ownership, cooldown and distinct-frame checks remain.

Final checks passed: **107 Python tests, 65 Node tests**, the frozen-source/fixture/policy checker, 130 pinned source files, lab-design checks, 39 screen-writing/v0.2 synthetic acceptances and BB8 package/discovery/twelve reference checks. The exported OpenAPI retains 29 HTTP paths and explicitly describes SSE v2. No native browser-control capability was available, no substitute browser was launched and no actual Simulink progression trial or Python cloud deployment is claimed. Native successful publication verifies the Site deployment, not the full sharing interaction.

For the live test, refresh the existing experiment URL, resume the saved model/share, and compare the delay from first recognized result through the second verification and displayed next instruction. Progress and technical details should identify **Short decision + async details** and show committed guidance separately from auxiliary delivery. Do not reset the user's run merely to load this change. Preserve failed/slow cases and compare with the pre-change evidence record. Actual Simulink overlay acceptance remains separate.
