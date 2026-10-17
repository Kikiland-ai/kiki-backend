# Screen writing interface v0.2: producer, resolver and delivery

14 October 2026 (Asia/Calcutta) · Provisional, breaking interface · Controlled captured-frame implementation can begin

## Compatibility and ownership

This replaces the v0.1 interface at e1d7510e5eded4e2a1dde07fbfcd0172191d6534. **screen-writing/v0.2 is not wire-compatible with v0.1.** Consumers reject v0.1 rather than inventing missing target identities, view revisions, frame handles or ordering. The archived schema is ../../contracts/archive/screen_writing.v0_1.schema.json; the old commit remains the authoritative v0.1 history. The current synthetic example now uses v0.2.

This session owns screen observation, lab progress, authored semantic identities, and canonical now/next instructions. The parallel session owns anchor resolution, cue rendering, coordinate transforms, cancellation and delivery acknowledgements. Rendering/acknowledgement never completes a checkpoint or establishes conceptual mastery. Actual Simulink overlay acceptance remains a separate integration test.

The supplied local ChatGPT conversation link could not be read (404). This document incorporates the user's explicit interface feedback; it does not claim unseen agreement with that conversation.

## Files and entry points

- [Protocol JSON Schema](../../contracts/screen_writing.schema.json): Draft 2020-12, oneOf four message types: cue_request, resolved_packet, cancel, delivery_ack. Each has schema=screen-writing/v0.2. Subschemas can be addressed as #/$defs/cue_request, etc.
- [Authored target catalog](../../contracts/screen_writing_targets.json): stable target IDs, precise block/parameter identities, applicable criterion IDs. This is authored identity, not a claim those targets are visible.
- [Single request](../architecture/examples/screen-writing/v0.2/single.request.json) and [single packet](../architecture/examples/screen-writing/v0.2/single.packet.json).
- [Multi-target request](../architecture/examples/screen-writing/v0.2/multi.request.json), [comparison packet](../architecture/examples/screen-writing/v0.2/multi.packet.json), [partial-resolution fallback](../architecture/examples/screen-writing/v0.2/multi-unresolved.packet.json).
- [Unresolved packet](../architecture/examples/screen-writing/v0.2/unresolved.packet.json), [view cancellation](../architecture/examples/screen-writing/v0.2/view.cancel.json), [delivery acknowledgement](../architecture/examples/screen-writing/v0.2/preview.ack.json).
- [Trusted synthetic runtime](../architecture/examples/screen-writing/v0.2/trusted.synthetic.runtime.json), frame.jpeg.b64 in that directory, acceptance-manifest.json and invalid/*.packet.json.
- [Reference policy](../../prototypes/screen_writing/reference.py) and [acceptance runner](../../scripts/check-screen-writing-design.py).
- [Lab schema](../../contracts/lab_tracking.schema.json), [lab analysis](../architecture/dsb-sc-lab-prototype.md), [definition](../architecture/examples/dsb-sc.demo-definition.json).

Every example is synthetic. The JPEG supplies actual hash/byte-count/dimension tests; it is a constant-colour image. Authored regions are protocol fixtures, not visual detections. Reference success ACKs use an injected fake compositor and do not establish real delivery. The parallel renderer should add controlled UI screenshots and actual compositor tests before claiming anchor accuracy.

## Selected lab and provenance

One demo: PR-AM-DSB, DSB-SC modulation/coherent demodulation in Simulink Online. The student builds, runs baseline recovery, introduces the receiver phase fault, then restores/reruns/saves/explains. Twelve checkpoints, ten blocks, eleven connections. The source JSONs were read at Design-Thinking commit 2a6c843448d81062f89596b941516f8b7817ec79; ledger blob 7e54eabba9aee6108bf0f3d3b742fb8e6da1c797 and learning-case blob 78b47d2e7cd4f84b7f7f586f4af5dcfa6631acee.

Baseline Message is 100 Hz, amplitude 1, bias/phase 0. Carrier and Local carrier are 2000 Hz, amplitude 1, bias 0, phase pi/2. Continuous time-based Sine Wave Frequency uses 2*pi*f rad/s, SampleTime 0. Transmitter Product -> receiver Product -> 500 Hz Butterworth Transfer Fcn -> Gain 2. Filter numerator [9869604.40109], denominator [1 4442.88293816 9869604.40109]. ode45, stop 0.1 s, max step 1e-5 s. Expected recovery is near-unit 100 Hz with filter lag/ripple. For the intentional phase_fault, only local phase changes to pi (relative 90°); restored_baseline returns pi/2. Source content/Odia review and real simulator execution remain draft/unverified. Never import synthetic learner passes.

## 1. Producer input to anchor resolution

A cue_request is created from a trusted admitted observation and the current tracker context. It carries:

- request_id; guidance_stream_id; cue_sequence; replacement=replace_complete_guidance_layer.
- Context: lab_session_id, experiment_id, checkpoint_id, visit_id, lab_revision, workspace_id, capture_epoch, parameter_revision, **view_revision**, condition.
- Teaching intent; canonical_instruction and canonical_reason owned by the tracker.
- Exact frame provenance: observation/frame IDs, SHA-256, byte count, encoded dimensions, client-monotonic capture elapsed time, server receipt/admission timestamps and captured view_revision.
- An owner-bound ephemeral frame_handle; requested semantic targets; explicit relationships; intended delivery surface and absolute validity window.

Targets requested by the producer have no region or drawing coordinates. The resolver must inspect the supplied exact pixels or a proven current adapter; frame IDs/hashes alone cannot locate anything.

### Frame broker contract

The producer creates a handle for the admitted JPEG. Its opaque handle_id resolves only through a negotiated trusted broker using the caller's authenticated owner/session, never an arbitrary URL in a packet. Proposed browser transport: GET /lab-sessions/{id}/frame-handles/{handle_id}; a tool/worker transport can expose the same operation. These routes are a producer implementation responsibility, not a currently verified service.

Successful retrieval returns the original JPEG bytes plus the trusted provenance record. The consumer verifies SHA-256, byte count, decoded MIME/dimensions, owner, handle/frame binding and expiry before resolution. A replaced, expired, deleted or inaccessible frame returns unavailable/410; never silently substitute the latest image. The writer asks the producer for a new observation/request. Handle lifetime must cover the request deadline and remain bounded; the fixture uses the same expiry. No continuous recording or indefinite archive is required.

## 2. Stable identities, multiple targets and operations

Use target_id values such as message.frequency, carrier.frequency, local_carrier.phase, recovery_scope.original_trace and recovery_scope.recovered_trace. Each request repeats the authored semantic identity (block ID, parameter/port/trace role, label) and relevant criterion IDs, limited to its current checkpoint. The consumer checks these against the catalog. It must not treat an arbitrary label as identity or interchange similarly named controls.

The resolved_packet returns one resolution record for each requested target: target_id; status resolved/unresolved/ambiguous; method model_vision/ocr/semantic_dom/simulink_adapter/human_review or null; normalized region or null; reason. All target IDs are unique. A resolved target requires a region and method; unresolved/ambiguous targets have no region.

Operations reference targets instead of supplying unrelated free coordinates:

- box/ellipse use the declared target's region.
- pointer/text use anchor={target_id,u,v}, where u/v are normalized within that target's region.
- arrow/polyline reference a declared relationship_id; endpoints must match its ordered from/to target IDs. Intermediate polyline anchors are restricted to those relationship endpoints.

This makes operation placement derivable from resolved geometry and rejects operations for undeclared or unresolved targets. Relationships include connects_to, compares_with and influences. Teaching arrows are explanations, not proof of existing wiring.

**Initial fallback policy:** if any target marked required_for_cue is unresolved/ambiguous, operations must be empty and fallback.reason=unresolved_required_target. With valid current context, display the unchanged canonical instruction in the guide panel. Optional unresolved targets cannot receive operations. The required target list cannot be empty.

Plain-text labels use text APIs, never HTML/script execution. Keep concept=green, words=red, english=yellow, lab=blue; accessible labels are required. Layers are pointer-transparent and clipped. Polyline reveal_ms is a rendering duration, not invented audio alignment.

## 3. View revision and observation admission

view_revision belongs to the geometry/view state within the selected workspace/capture segment. It increases on known scroll, zoom, resize, canvas pan, modal changes and other detected layout changes. It is not the frame counter. capture_epoch identifies a capture segment; parameter_revision identifies declared model configuration; a view can change while both remain unchanged.

The observation producer snapshots current view_revision **when capturing the frame** and again **when admitting analysis**. Admission succeeds for cue generation only if the frame's captured revision still equals the current view. Persist that value in the trusted observation, cue request and resolved packet. A late analysis/anchor result with an older revision cannot be promoted to the new view by rewriting its revision.

The parallel adapter detects geometry changes it can observe, immediately clears its layer and reports invalidation to the producer's authoritative view broker. The producer increments/publishes the revision, cancels old requests and admits a fresh frame. Resolution/analysis must recheck context on completion. Capture-dimension changes can be detected by the capture client; generic screen sharing cannot by itself detect every Simulink scroll/pan/modal. Missing detection capability remains explicit and prevents claiming a proven live overlay.

The proposed lab schema/example now carry view_revision in workspace and observation. The request frame and admitted-context fixtures carry it too. Actual source-event hooks and view broker transport are still producer/consumer integration work; these schema additions do not claim that all live events are already monitored.

## 4. Stream, replacement, ordering and cancellation

One guidance stream is negotiated for one authenticated lab session, workspace and renderer instance. Its opaque guidance_stream_id is allocated by the producer/broker. It remains stable across step/view/capture updates until explicitly retired; those updates invalidate old contexts. A new renderer/restarted stream receives a new ID through the handshake. Retired-stream messages are rejected, never silently adopted.

The broker allocates one strictly increasing cue_sequence for every cue request **and ordered cancellation**. Resolver packets echo the exact request sequence; resolvers never allocate a newer sequence to an old result. A sequence identifies an immutable request/cancel record in trusted state. Delivery ACKs echo the relevant sequence.

Each accepted packet replaces the complete current guidance layer, including its prior marks and fallback text. No accumulation or incremental patch semantics in v0.2. The consumer keeps a high-water sequence and a seen-message-ID set for the current stream; at most 500 typed messages, then retire/re-handshake rather than evict ordering protection. IDs are unique within the stream, including cue IDs within a packet. Duplicate IDs and sequences at/below the replacement/cancellation fence do not render. Older packets do not clear a valid newer layer.

Writer-detected pause/disconnect/context invalidation clears immediately; it does not wait for a network cancellation. Context and observation checks reject pending work from the old state. The writer sends the invalidation to the broker, which issues an ordered cancel message (reason/context/time/sequence). Accepting cancellation advances the high-water fence and clears the layer; old replies cannot resurrect it. A newer request issued after the fence can render if it matches current trusted context. Do not fence new-context requests merely because they have already been issued.

Step/visit, workspace/epoch, parameter/condition, view or admitted-observation changes clear the old layer. Pause/disconnect and expiry also clear it. Cancellation affects presentation and hint-exposure records; checkpoint evidence/progress is unchanged.

The reference implementation is synchronous with an injected compositor. A real asynchronous resolver must revalidate before an atomic main-thread compositor commit and before acknowledgement, using a fresh clock/context read. If a context/expiry change occurs during delivery, clear the result and do not report successful exposure.

## 5. Unresolved fallback versus rejection

These are different outcomes:

- Valid current context + unresolved required anchor: full replacement with empty operations and canonical text; delivery_ack=text_only, actual_surface=guide_panel.
- Stale checkpoint/visit/workspace/epoch/parameter/condition/view, stale observation, foreign frame, inactive session or expired request: discard the entire packet, including fallback. No packet text is displayed. The tracker independently supplies the actual current instruction.

An invalid packet does not overwrite a valid current layer. A trusted context-change event clears that old layer first. Malformed/unsupported-version messages get a transport/schema rejection; do not invent missing identifiers to manufacture an acknowledgement.

## 6. Runtime validation and timestamp authority

JSON Schema only checks structure. Mandatory consumer policy is in the reference and acceptance examples:

1. Authenticate ownership/current stream and immutable request admission. Match current session/observation status and the complete current context.
2. Compare frame ID/hash/byte count/dimensions/timestamps/view against the trusted admitted observation, not another packet-provided copy. Require the currently active admitted observation. Resolve and verify exact pixels through its owner-bound handle.
3. Enforce issued sequence, deduplication, absolute expiry (maximum eight seconds from request creation) and server receipt age (at most twenty seconds). Resolver packets cannot extend the producer's validity.
4. Validate authored target identity/criterion applicability, unique target/relationship/cue IDs, complete resolution records, in-frame regions and operation-to-target/relationship references.
5. For preview, match the image actually mounted in the preview to the admitted frame before committing. A latest-frame preview displaying different pixels is not an acceptable target surface.
6. Validate the actual mapping and clipping bounds. Initial controlled preview uses an invertible affine contain/letterbox mapping; all encoded-frame corners and cue geometry must fit the verified surface bounds. CSS cover/cropping that violates containment is rejected in this initial implementation. More general visible-source clipping needs an explicit verified extension.
7. For live delivery, a packet's binding ID/transform revision must resolve to a trusted capability registry entry bound to owner, workspace, epoch, view, exact source frame, adapter version, expiry, affine transform and actual bounds. Its proof_ref must resolve to a separately trusted integration record with report digest, verified dates, coordinate-space mapping and demonstrated scroll/zoom/resize/pan/modal/layout invalidation hooks. A packet boolean or nonempty proof string is insufficient. Never accept proof records from resolver packet data.
8. After real compositor delivery, recheck current context/time and emit an ACK for the actual surface/outcome. Failed/rejected delivery produces no hint-exposure success.

The raw capture clock is client-monotonic capture_elapsed_ms; it is labelled as such, not converted into fabricated wall time. received_at/admitted_at and request created_at/expires_at are observer/producer server UTC. Ordering is by sequence/context, not timestamps. Receipt freshness is not proof that an upstream delayed capture is fresh; the producer must also validate bounded monotonic capture-to-admission delay and source gaps. Consumers use a calibrated authoritative time estimate; uncertain clock synchronization requires rejection/recheck rather than guessed expiry.

Delivery delivered_at is labelled consumer_clock. The tracker adds its own server acknowledgement-received time in the event journal and retains both; it does not trust client delivery time as an assessment clock. The reference suite supplies a fixed synthetic trusted clock.

## 7. Acknowledgement and exposure events

A delivery_ack carries request/packet/cancel IDs, stream/sequence, the acknowledged context plus packet_context (the original packet context when clearing an older view), actual surface, consumer timestamp, status/reason and actual binding/transform identifiers where relevant. Rendering statuses are preview_rendered, live_rendered, text_only; rejection/cancellation are rejected/cancelled. actual_surface distinguishes captured_frame, live_workspace, guide_panel and none. Success is sent only after actual delivery, never after schema validation or renderer scheduling. A cancellation references the packet it cleared when one existed, retains that original packet_context, and reports the cleared surface. Its context/sequence identify the newer cancellation barrier.

The tracker deduplicates ack IDs and matches them to issued requests/packets/cancels before journaling. Record proposed hint, successful exposure and rejected/cancelled attempt separately. None updates criterion satisfaction, checkpoint completion, concept mastery or practical evidence. Review of the student's subsequent result remains a different event.

## Acceptance and what is still unresolved

Run python -B scripts/check-screen-writing-design.py (jsonschema and Pillow are already present here). The checked corpus covers valid single/multiple targets, one unresolved required comparison target, canonical text fallback, stale fallback rejection, stale visits/views/conditions/workspaces/parameters, foreign frame ID/hash/dimensions/handle owner, different mounted preview, stale observation, duplicate cue/target/packet IDs, unrelated operations/endpoints, out-of-frame regions, changed expiry, ordering, cancellation plus a valid post-cancellation request, pause/disconnect clearing, missing/boolean/expired-or-wrong live proof/transform constraints and expiry during delivery. See acceptance-manifest.json and executable temporal scenarios in the runner. A simulated complete live capability is explicitly a fixture, not actual Simulink acceptance.

Ready for the parallel session: consume single.request.json; retrieve the fixture pixels through the reference broker; implement semantic resolution returning single.packet.json-shaped output; render on a controlled captured-frame preview; port the trust/order/cancellation policy; emit actual ACKs. Add proper UI screenshots and resolver-quality checks rather than crediting synthetic regions as recognition.

Producer still owns implementing the authenticated ephemeral frame broker, authoritative request/sequence allocator, captured/admitted view-revision storage and view-change ingestion, current canonical instruction mapping, and ACK journaling. Consumer still owns proving real preview transforms/atomic delivery, detecting geometry changes it can see and reporting them, and publishing actual live-adapter proof if that later integration is attempted. The transport/handshake URLs and clock calibration implementation must be agreed before live coupling; schema field names and rejection behavior are concrete now. The current target catalog can be extended through an authored, versioned update when additional ports/controls are needed.

The existing private screen analyzer is https://kiki-screen-receiver.woodsycarp256.chatgpt.site. Local focused lab implementation has passed API and native fixture-browser checks, but its new persistent storage/MCP publication is not yet verified at this handoff update. The local FastAPI remains receipt-only; Python remains the selected product backend. Keep runtime secrets, unrelated media work and synthetic learner records out of this interface.
