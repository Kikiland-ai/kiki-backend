# Analysis-owned guidance integration v1

Updated 15 October 2026, Asia/Kolkata. Deployment receipt is appended after publication.

The user authorized combining producer `1c658b63ef0a0ebce827168040bc057d92fa4c77` with the independent renderer on `integration/analysis-owned-guidance`. The renderer branch ends at `e916986`; the integration uses explicit merges, so its Worker/client/build changes do not enter the producer branch. Baselines, the latency-control branch/Site and PR #1 are unchanged. The user explicitly selected updating **https://kiki-screen-receiver.woodsycarp256.chatgpt.site** instead of provisioning another set of model secrets. Preserve its private audience, secrets and D1 sessions. The separately allocated `kiki-guidance-experiment` project is unpublished and unused.

## Delivered path and decision boundary

One native browser-tab capture supplies periodically sampled exact JPEGs. The connected 0.4.0 adapter verifies a capture marker, the JPEG hash/dimensions and its selected source, then signs the admission. The Worker verifies this before mutating tracker state or calling the provider. The same analysis call emits the reader fields and drawing intent, using offered authored actions/target IDs and normalized geometry. There is no second localization/model call in the consumer or extension.

The tracker supplies canonical current/next instructions, offered action IDs and practical evidence rules. A model request to annotate is projected only after complete schema validation and current-context checks. An unresolved required target permits canonical text only in a valid current context. Stale packets are discarded entirely. `none` means no drawing; connecting is not a drawing trigger. The consumer verifies the selected source and fresh pixels again before applying a full layer. A source/view change cancels local guidance immediately; ordered Worker cancellation handles context changes and reconnects. Paint and acknowledgement never supply criterion evidence or complete a checkpoint.

This is browser-tab guidance, including Simulink rendered inside MATLAB Online. It does not implement an OS desktop overlay or drawing over arbitrary native applications. Concept graphics/Manim rendering remain separate from this lab cue path.

## Compatibility review

Preserved interfaces: `lab-observer-drawing/v1`, `analysis-owned-guidance/v0.1`, `lab-analysis-stream/v3`, `committed-decision/v2`, `screen-writing/v0.2` packets and delivery ACKs. The old three-field/v2 control remains available when drawing negotiation is absent. The producer's helpers were not wired into the runtime builder/routes; integration adds trusted admission, durable publication and projection plumbing.

The real provider rejected the original nested mark-union generation schema with HTTP 400. `LiveDrawingRunJS` therefore supplies a flat provider-facing mark object with a kind enum and optional geometry fields. This is a generation overapproximation only: the unchanged published typed validator remains mandatory before committing; malformed kinds/geometry/operations cannot bypass it. The revised request succeeded on the constant-colour synthetic JPEG and returned `none`. This tests API acceptance, not component recognition.

## Integration-owned transport

All routes are owner-scoped under `/lab-sessions/{id}/guidance/`; mutating requests also require the existing same-origin guard. Existing Site sign-in supplies identity. No new browser secret is introduced.

| Route | Purpose |
| --- | --- |
| POST `connect` | Registers the connection public key and active capture session; returns nonce, stream ID, exact version tuple and clock/reservation bounds. Replacement atomically retires/cancels old connections. |
| GET `clock` | Server UTC sample; client rejects calibration uncertainty above 250 ms and uses monotonic local deadlines. |
| GET `events?connection=…&after=…` | Bounded ordered outbox replay, at most 32 entries, scoped to this connection and owner. |
| POST `ack?connection=…` | Validates v0.2 receipt. Paint/cancel receipts require the extension signature; rejected attempts do not claim paint proof. |

Negotiated analysis carries `X-Guidance-Contract`, connection identity and signed admission. The connection nonce, exact JPEG receipt/hash, capture handle, source descriptor, transform, frame/context and attachment generation remain bound throughout. Extension signing keys are non-exportable P-256 keys, lost on worker restart; reconnect/re-admission is then required. This authenticates the registered owner-authorized connection, not a malicious-owner-resistant installation attestation.

D1 migration **0004** appends streams/outbox/ACK tables after the receiver's existing 0003. Publication uses a D1 batch/CAS against the actual lab revision, stream high-water sequence and cancellation fence. Sequence allocation and outbox insertion are atomic; duplicate publication returns the prior message. Tracker mutation and its cancellation append share a batch. Publication completes before `guidance_committed`; auxiliary SSE history is independent. `capture_active` is retained in the committed projection. UI callbacks, queued requests and polling are fenced by generation/context; accepted observations remain coherent while provisional findings stream.

The presentation mutex reserves capture exclusion, fresh verification and paint for at most **500 ms**; it does not extend packet expiry. The capture track requests 10 fps for marker responsiveness; uploads remain one per two seconds and inherited analysis budgets/cadence/failover controls are preserved. A pending capture can delay delivery before reservation starts; both timing scopes remain visible. Paint receipts are signed only after the compositor reports visible frames. Historical late ACKs may be stored with `late_context=true`; they never revive stale rendering permission or alter tracker state.

## Checks and scope

Retained evidence: [integration-v1-evidence](../experiments/analysis-owned-guidance/integration-v1-evidence/README.md). The offline producer/control gate and 114 Node tests passed, including actual Worker CAS, replay, cancellation, signature rejection, blocked auxiliary tail and consumer validation. A controlled browser test uses native getDisplayMedia, real periodic capture, actual reader/Worker/broker/consumer/compositor and independently counted blue pixels at an authored control, followed by a persisted signed paint ACK. An injected view move between verification and paint produces no paint receipt and records a rejection.

Chrome API dispatch and model localization are explicit fixtures. The streamed browser check uses an explicitly labelled localhost controller-origin substitution and a pinned ephemeral test certificate; production pins remain unchanged. It proves browser SSE coherence and the local vertical slice, not an installed-extension or real Simulink test. Real model samples include timeouts, a 503, schema 400s, successful controls and one validated drawing `none` response. No latency improvement or recognition accuracy is claimed.

## Operation and next acceptance

Download adapter **0.4.0** from the receiver, reload the unpacked extension and refresh both tabs so old service workers/bridges cannot persist. Connect the MATLAB tab, share that same tab from the receiver and start the lab. Status distinguishes capture, analysis and delivery; the annotation trace retains bounded connection/rejection/paint events. Drawing is conditional on a current validated model intent, not a fixed smoke test. If it declines or fails, retain the reason and frame/request IDs rather than inventing a shape.

Next acceptance is the installed adapter on an actual MATLAB/Simulink task: confirm correct target placement and semantically correct canonical direction, move/resize the view to prove clearance, and retain analysis-to-commit plus commit-to-paint logs. Existing Site secrets are reused; do not copy masked values or ask for keys in chat. Pause/stop should clear guidance. Practical progress and concept assessment remain separate.
