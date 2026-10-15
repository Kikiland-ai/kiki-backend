# Producer contract proposal: findings and drawing from one analysis

15 October 2026. **Proposed interface, not agreed or runtime-enabled.** Branch `experiment/analysis-owned-guidance-producer`, coordination base `c805d3799dbef5cfd734c9dd9844b9d9b075e677`; latency-control base `ae234dcdd78b91ef7d6e6b528b14f2e9196808bb`. Read the [coordination handoff](analysis-owned-guidance-experiment.md) and [design 0007](../decisions/0007-analysis-owned-screen-guidance.md).

This commit publishes schema, synthetic examples and contract reference checks first. It changes no active model prompt/parser, committed projection, browser client, build, Worker route, generated bundle, Site, secret or learner session. It does not implement a renderer or prove target localization/paint. The latency control, reader/writer baselines and PR #1's code/review state remain separate. PR #1 only received the requested latest latency observation in its description.

> Implementation update: an opt-in producer v1 now exists on this branch. See the [v1 build/export/testing handoff](analysis-owned-guidance-producer-v1-build.md). The proposal-publication descriptions below refer to commit `08229428a712a5cd3c71847490d09502a7a8d5da`; they do not describe current implementation status. Renderer agreement and live integration remain pending.

## Version and compatibility proposal

| Boundary | Proposed new contract | Existing control |
| --- | --- | --- |
| Complete model response | `lab-observer-drawing/v1` | `lab-observer-decision/v1` |
| Analysis event stream | `lab-analysis-stream/v3` | `lab-analysis-stream/v2` |
| Bounded committed state | `committed-decision/v2` | `committed-decision/v1` |
| New trusted input / committed / cancellation envelope | `analysis-owned-guidance/v0.1` | None |
| Deterministic drawing packet and paint ACK | Existing `screen-writing/v0.2` | Unchanged |

The new model response is **exactly four fields**, in requested serialization order: `criteria`, `action_findings`, `uncertainties`, `screen_guidance`. It is not accepted by the existing strict three-field parser. Do not append the new field silently or deserialize it with the old parser. Model version selection is trusted request configuration, not a model-authored version/provenance field. Both Python and Worker adapters need explicit new-contract support before any connection is enabled.

Schema exports:

- [Model response](../../contracts/lab_observer_drawing.v1.schema.json), root `$id=urn:kiki:lab-observer-drawing:v1`.
- [Trusted input/committed/cancel bundle](../../contracts/analysis_owned_guidance.v0_1.schema.json), `$id=urn:kiki:analysis-owned-guidance:v0.1`; exports `#/$defs/analysis_input`, `#/$defs/committed_guidance`, `#/$defs/cancel`.
- The bundle references `urn:kiki:screen-writing:v0.2` from the existing [schema](../../contracts/screen_writing.schema.json). Register that pinned local schema; do not fetch schemas over the network or rewrite v0.2/catalogue in place.

These are JSON Schema 2020-12 acceptance contracts, **not a claim that Gemini supports every keyword directly**. The next producer implementation must construct the provider-supported request schema with per-request authored enums and keep the complete final validation. Do not drop final checks when compiling a restricted provider schema.

The proposed v3 opt-in uses request headers `X-Kiki-Model-Contract: lab-observer-drawing/v1` and `X-Kiki-Stream-Contract: lab-analysis-stream/v3`, with exact accepted contracts returned before findings. Unknown/unsupported versions fail before a model call; no downgrade or reinterpretation. The stream/client/build/route negotiation is not wired by this proposal and belongs on the integration branch.

## Input and single model response

`analysis_input` records the trusted admitted frame/context, request ID, owner-bound ephemeral handle, source binding and ordered authored action catalogue. The first eligible action is the current action at admission; at most one following entry is its authored immediate successor. The producer must derive this list from the tracker, not from model text or a renderer. The model receives the **exact admitted JPEG** plus the authored drawing catalogue alongside the existing checkpoint/findings context. Frame hashes/IDs alone cannot locate controls.

Every action descriptor supplies its exact ID/checkpoint, teaching intent, canonical instruction/reason, one or two required target IDs with labels/subcriteria, at most one authored relationship, and up to four authored overlay-text references. `overlay_texts` values must fit the existing v0.2 160-character text limit exactly; do not silently truncate an instruction. Longer canonical instructions remain available through tracker/guide text, and must not be offered as an anchored text reference unless an independently authored short label exists. Initial targets are restricted to the existing v0.2 catalogue; new target identities require a separate compatible catalogue/contract decision.

`screen_guidance` contains zero to two unique action candidates. Per candidate:

- `action_id` must occur in the admitted eligible catalogue.
- `mode=annotate` has all required targets resolved and one to four marks. Regions are normalized to the **encoded analysed frame**, not CSS pixels, device pixels or the current tab viewport.
- `mode=text_only` contains every required target, at least one unresolved/ambiguous target, and **zero anchored marks**. A visible target cannot compensate for another missing required target.
- `mode=none` contains no targets or marks. An empty `screen_guidance` array also explicitly declines drawing.
- Marks are `box`, `ellipse`, `arrow` or `text`; cue IDs are unique within each candidate/selected packet. Targets may repeat in different candidates, but action candidates may not repeat.
- Arrow endpoints use target-relative `{target_id,u,v}` anchors and an authored relationship ID/direction. Box/ellipse reference a target ID. Text uses an anchor and authored `text_ref`, never free instructional prose.

No raw SVG/HTML/CSS/script, arbitrary URLs, model-authored clocks/frame/context/sequence/expiry or additional teaching/model pass is allowed. Existing finding IDs, evidence/unknown semantics, exact array membership, duplicate-key rejection, buffer limits and provider STOP remain mandatory. A malformed drawing field, late trailing output or missing STOP rejects the **whole response**; partial valid findings are not salvaged into checkpoint progress.

## Admission after the tracker commits

The tracker owns canonical instructions and practical progress. Once the whole response is valid, the tracker applies the existing current-context/freshness/two-frame/explicit-report gates and saves its result. The producer then selects only the candidate whose `action_id` equals the **resulting committed current action**.

Selection does not relabel geometry. If the action advanced and no matching successor candidate was supplied, emit `outcome=none`, `reason=no_matching_candidate`, `packet=null`: this full replacement clears old marks and notes. Wait for the next normal periodic frame; do not make a repair/localization model call. If the matching candidate declined, use `reason=model_declined`. Terminal lab completion retires/cancels the stream using the last authoritative context; it does not invent a current action/checkpoint.

A normal tracker transition may change checkpoint/visit/lab revision. Source-semantic fields must still match the trusted admission: session, experiment, workspace, capture epoch, view revision, parameter revision and condition. A changed condition, view or parameters invalidates the result; old geometry cannot migrate merely because the new action has a matching ID. Eligible successors crossing a condition/source boundary must not be offered. Concurrent invalidations discard the whole result and issue an ordered clear; they are not unresolved-anchor text fallbacks.

For a matching candidate, the producer deterministically wraps its marks in `screen-writing/v0.2`:

- `resolved_targets.method=model_vision` records localization in this same analysis; the model cannot claim an OCR/DOM/human adapter method.
- Region/status/target identity stay exactly those validated in the selected candidate. `target_criteria` comes from the authored catalogue, not the model.
- Authored relationships, `meaning=lab`, accessibility labels and text-ref expansion are mechanical. Box/ellipse/text accessibility labels use the authored target label; arrows use a bounded authored relationship-kind label, so a long canonical instruction cannot overflow the legacy label limit. The renderer receives final operations/text and does not infer a teaching action from criterion findings.
- `frame`, admitted and current contexts, source binding, request/stream IDs, sequence, handle and validity are server/runtime metadata. Packet and wrapper identifiers/frame/context/validity must agree exactly.
- Text-only packets have empty operations and the **current canonical instruction** as fallback. A stale packet is discarded completely, including fallback. Tracker panel text remains a separate authoritative state projection.

### Committed handoff location

The proposed v3 `guidance_committed.state` has `projection=committed-decision/v2` and one new `screen_guidance` field containing a `committed_guidance` or terminal `cancel` envelope from the bundle. Do not duplicate it in the event tail or make the consumer fetch a second semantic result. It is emitted only after durable tracker commitment; provisional findings/critical-ready events never draw. The existing independent committed/completion promises and blocked-tail protection are retained.

At the initial proposal commit there was **no new production callable export**. The [v1 build handoff](analysis-owned-guidance-producer-v1-build.md) now lists the opt-in implementations. Initial producer code was planned in `prototypes/json_stream/guidance.py` with a Python admission adapter and equivalent isolated Worker producer helper. Existing `analysis.py`, strict parsers and committed projection will select this version explicitly. Shared client/build/route/generated-bundle edits remain integration-owned.

## Replacement, ordering and cancellation

One producer-generated `guidance_stream_id` is scoped to an authenticated lab/workspace/capture attachment. Its durable `cue_sequence` increases for **every** complete replacement or cancellation, including no-cue clears; it does not reset at an action/visit change. Rotate the stream ID only with an authenticated attachment lifecycle and retire the old stream.

Consumers deduplicate packet/cancel IDs and maintain a high-water sequence even after clearing. An older/equal sequence cannot replace, clear or resurrect a newer layer. A higher sequence still needs the current context/binding; sequence alone never authorizes stale geometry. `replacement=replace_complete_guidance_layer` is literal: no accumulated marks. No-cue/empty-operation replacement removes old anchored notes as well as shapes.

Producer pause, disconnect, step/workspace/parameter/view change, expiry and stream retirement send the new version's ordered `cancel`, mechanically convertible to the unchanged v0.2 cancel shape. Renderer source/navigation/resize invalidation clears locally immediately and fences that binding/view without inventing a server sequence; later producer cancellations reconcile the server fence. Pending delivery and queued captures cannot restore a locally invalidated layer.

Periodic frame arrival or a changed screenshot hash is **not itself a view revision or blanket cancellation of in-flight analysis**. Source identity/layout invalidation and final live-content freshness are separate. Delivery must still verify the current source pixels/geometry according to the agreed adapter proof; removing that final check is not a latency optimization.

### Rapid observation changes during streaming

User-reported integration risk, 15 October 2026: “when the streaming is going on the what can I see changes rapidly.” This is a required regression scenario, not a confirmed diagnosis or an implemented fix. It may mean changes in the shared source, repeated provisional panel updates, or overlapping/late responses; test each separately.

- Pin every analysis to its immutable admitted frame, request ID and context. Stream fragments update only that request's private assembly buffer. Do not assemble findings or drawing geometry from different frames, retries or requests.
- Keep the last accepted observation coherent in “What I can see,” labelled with its frame/capture age while a newer read runs. Do not rewrite that panel from each provisional finding or auxiliary snapshot. Publish the next accepted observation atomically with its committed now/next projection; an obsolete completion cannot overwrite it. Invalidation may immediately mark it historical/unavailable and clear guidance. Historical text must not masquerade as current observation or fallback instruction.
- The browser needs a local attachment/request-generation fence as well as server context/sequence checks: abort is best effort, and an already queued callback can still run. Recheck identity and freshness immediately before tracker save, committed-event application, and visible paint. The server save must be conditional on the expected authoritative revision (or serialized against invalidation); a read followed by an unguarded save is not sufficient. A late auxiliary tail cannot replace the committed projection.
- Source/layout/parameter/visit changes fence invalid work immediately. Capture-source changes, pan, zoom, resize, modal or scroll changes invalidate geometry as applicable; ordinary new frames or changed hashes alone do not. A same-layout content change can still make an instruction obsolete: final source/target freshness must reject or clear stale live cues even when `view_revision` is unchanged. Captured-frame preview remains explicitly historical, never proof of live freshness.
- Coalesce waiting captures to the latest eligible frame under the existing bounded analysis scheduler, while retaining the admitted frame for the in-flight request. Do not restart on every frame or wait indefinitely for a motionless screen. If source motion prevents safe live placement, keep current tracker text available and omit anchored marks until a fresh validated result arrives; do not recycle stale packet fallback.

Required deterministic integration tests use controlled stream barriers: newer frame arrival without layout change; source/view invalidation between chunks; invalidation between final validation and durable save; older request/tail completion after a newer commit; queued callbacks after abort; source-content movement with unchanged layout revision; invalidation between source verification and paint. Assert no observation regression, mixed-frame marks, stale progress save, resurrected layer or capture-starvation loop. Record frame age at commit/paint, invalidation/discard reasons and reschedule counts alongside latency. These tests are planned in addition to the existing 50 reference cases; they have not run in the live pipeline.

Producer owns immutable admission, parsing, conditional tracker commit and ordered output. Integration owns panel updates/request-generation fencing and capture scheduling. Renderer owns final source freshness, local invalidation and pre-paint checks. Existing fields suffice for the documented proposal; any new wire generation or state-version field needs an explicitly agreed contract revision.

## Proposed transport, clocks and live connection gate

These are explicit proposals for renderer review, not an agreed or working live connection. [Negotiation metadata](../architecture/examples/analysis-owned-guidance/v0.1/negotiation.proposed.json) sets `live_connection_enabled=false` and `controller_origin=null`.

- **Site origin:** use a new private integration Site, with its actual native returned URL pinned in the reviewed extension allowlist. No new Site is allocated here and no origin/project ID is guessed. Do not point the experiment at either existing Site. Exact origin remains an integration prerequisite.
- **Frame transport:** retain the immutable selected JPEG from the same capture/analysis transaction; reuse it for healthy-path identity verification. The same-owner ephemeral handle is a fallback for the **identical** frame, with hash/bytes/dimensions verified; never substitute the latest capture. No second healthy-path frame download or model call is required by the contract.
- **Authentication/delivery:** owned same-origin POST/SSE on the private controller; existing trusted owner, origin and frame-receipt guards remain. Controller-to-extension delivery requires an authenticated connection nonce, exact pinned origin, selected native tab/source binding and trusted adapter records. A page message, chosen tab ID, supplied hash, boolean adapter flag or viewport smoke alone is not proof. No credentials belong in model output, URLs, examples or chat.
- **Binding/transform:** the wrapper records binding ID/revision, surface and transform revision. Live delivery needs the trusted native source proof and matching current transform. The initial reference harness rejects missing/boolean-only live proof; it only accepts synthetic captured-frame contracts and makes no live capability claim. Actual tab source identification, permitted proof details and paint/capture serialization are renderer/integration responsibilities.
- **Clock authority:** capture elapsed time is client-monotonic provenance; receipt/admission/creation/expiry use observer server UTC. Capture time is not receipt time. The server requires receipt <= admission <= creation; expiry is at most creation + 8 s, receipt + 20 s and handle expiry. Never extend validity during retries, translation, reordering or rendering.
- **Consumer deadline proposal:** establish server clock offset/RTT bounds during authenticated version handshake, record a clock-sync ID locally and subtract uncertainty from remaining lifetime. Reject live delivery when clock uncertainty exceeds 250 ms. Renderer uses monotonic timers after synchronization; arbitrary client wall time cannot extend expiry. Recheck before first paint and record both actual consumer paint time and server ACK receipt separately.
- **Capture versus paint proposal:** one coordinator reserves final source verification through actual visible paint, with capture queued behind a bounded 500 ms presentation transaction. A new view/context/cancel preempts immediately. Expired/contended transactions reject rather than block capture indefinitely. These bounds need renderer agreement and measured integration acceptance; they are not implemented by this commit.
- **ACK:** reuse `screen-writing/v0.2` delivery ACK. Correlate `request_id` to `analysis_request_id`, plus packet/cancel/stream/sequence/context and actual surface/binding/transform. Emit rendered status only after actual visible paint, not enqueue. Owner-authenticated persistence records hint exposure and consumer/server timestamps separately; it never supplies checkpoint evidence or an understanding assessment. The persistence route is not added here and remains an integration decision.

Unsupported negotiation, missing source binding, failed freshness or transform validation must block live connection/paint. A model response containing coordinates cannot close that acceptance boundary.

## Examples and offline acceptance

All examples are authored **synthetic protocol fixtures**. The constant-colour JPEG provides real byte/hash/dimension checks; its regions are not detected controls. There is no learner screen, real localization, compositor execution or success-shaped paint ACK in this proposal.

[Example directory](../architecture/examples/analysis-owned-guidance/v0.1/):

| Fixture | Purpose |
| --- | --- |
| `input.single.json`, `model.single.json`, `committed.single.json` | Admitted catalogue, one response and one resolved current-action packet |
| `model.comparison.json`, `committed.comparison.json` | Two stable waveform targets, authored comparison relationship and typed arrow/notes |
| `model.text-only.json`, `committed.text-only.json` | Unresolved current target; canonical text without anchored operations |
| `model.multi-unresolved.json`, `committed.multi-unresolved.json` | One ambiguous required target disables the entire multi-target drawing |
| `model.none.json`, `model.declined.json`, corresponding committed files | Empty candidates or explicit refusal; complete clear with no fallback note |
| `model.action-advance.json`, `trusted.action-advance.json`, `committed.action-advance.json` | Select the successor candidate after authored action advancement |
| `committed.no-matching-candidate.json` | Advancement without a successor candidate clears until the next normal frame |
| `invalid/stale-{view,visit,condition}.json`, `invalid/stale-text-only.json` | Shape-valid but context-invalid packets: reject everything, including fallback |
| `cancel.view-change.json`, `ordering.trace.json` | Ordered cancellation and late/newer-sequence stale-view rejection |
| `acceptance-report.json` | Retained reference-check outcomes; not an end-to-end acceptance report |

If the validation dependencies are absent, install the isolated [contract requirements](../../contracts/analysis_owned_guidance.v0_1.requirements.txt) into the test environment. Exact offline command:

```sh
python scripts/check-analysis-owned-guidance-contract.py
```

The script registers local schemas, checks all typed fixtures and emits 50 contract outcomes: valid input, single/multi/declined/text-only, advancement, foreign frame/hash/dimensions/source, duplicate IDs/JSON fields, out-of-frame coordinates, unrelated operations, invented note references, malformed late output, missing STOP, expiry, stale fallback, cancelled ordering and missing/boolean-only live adapter capability. These are **reference contract checks**, not the production strict parser/tracker or renderer pipeline. Consumer/compositor interoperability is still unverified.

Next integrated gate must use the actual delayed single analysis response while periodic frames continue, strict Python/Worker parsers, tracker commit, negotiated consumer and real compositor, independent expected pixels and persisted post-paint exposure ACK. Cover capture/paint contention, duplicate UI renders, pause/source/view/visit/parameter invalidation, ordering, incomplete/malformed output and blocked auxiliary tails. Measure added output tokens, complete decision/commit, delivery validation and actual paint against the unchanged latency control under the same configuration; retain all slow, failed and discarded outcomes. No latency or native Simulink overlay success is asserted here.

## Ownership and exact next action

Producer owns schemas, model request/output, strict parsing, committed current-action admission/projection and ordered cancellation. Renderer owns deterministic operation consumption, source/viewport transforms, presentation lifetime/cancellation and actual paint ACK. Integration owns shared `assets/lab.js`, build scripts, routes, generated Worker and authenticated wiring. Neither side independently edits those integration hotspots.

This first exchange ends after publishing the proposal commit. Renderer can validate these fixtures and identify compatibility changes before both implementations are coupled. Next producer phase implements the explicit versioned Python/Worker parsing and admission on this branch, retaining batched routing, fresh per-chunk context checks, complete STOP gates and independent auxiliary delivery. The exact live origin/source-proof/clock/paint-lock/ACK-persistence agreement and actual renderer acceptance remain unresolved; none is inferred from these schema tests.
