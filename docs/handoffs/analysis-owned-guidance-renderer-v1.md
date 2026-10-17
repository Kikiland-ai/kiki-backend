# Renderer v1: deterministic live-tab delivery

15 October 2026. Renderer branch `experiment/analysis-owned-guidance-renderer`;
combined runtime belongs on `integration/analysis-owned-guidance`. This renderer
accepts the producer's `analysis-owned-guidance/v0.1`, negotiated stream v3 and
committed-decision/v2, with unchanged screen-writing/v0.2 packets and ACKs.

The extension is **0.4.0**, pinned to the existing receiver origin after the user
explicitly changed the new-Site request to reuse its configured secrets. The
latency-control Site and PR #1 are separate. Old 0.3.1 cannot supply the new signed
source/paint protocol. No operation in the extension chooses a lab action or
recognizes a target. Primitive intent and geometry come from the accepted model
packet; canonical notes are producer-authored text references.

`assets/guidance-consumer.js` exports `KikiWriting`: capture preparation/finish,
JPEG admission, request negotiation headers, attachment/context updates,
committed-state receive, immediate invalidation and bounded diagnostic history.
`assets/guidance-protocol.js` validates context and compiles box/ellipse/arrow/text
into the compositor's normalized operations. Its identical extension copy is
checked before publishing. `writing-frames.js` samples the existing capture track;
`writing-protocol.js` contains only source/fingerprint checks, not a resolver.

Transport implemented for integration:

- `writer_identity` creates a non-exportable P-256 signing key inside the extension
  service worker; its public key identifies the owner-authorized connection.
- The owned same-origin `guidance/connect` route returns an attachment nonce and
  exact model/stream/projection/payload versions. `writer_handshake` pins them.
- Every selected JPEG is checked by the extension for SHA-256, encoded dimensions
  and all 96 capture-marker cells. It signs `kiki-native-binding/v1` containing
  the nonce, session, source descriptor, ticket and exact server frame receipt.
  The Worker verifies the signature and admitted frame/context. This authenticates
  the owner-authorized extension connection; it is not hardware/installation
  attestation or protection against a malicious owner replacing their own client.
- A final capture excludes teaching ink, verifies the current pixels against the
  retained exact JPEG and preserves the source revision/transform. The healthy
  path does not download the JPEG again. The capture track requests 10 fps to
  bound marker visibility; JPEG uploads remain one per two seconds and existing
  paid-analysis cadence remains in force.
- One mutex owns final verification through paint ACK, with a 500 ms presentation
  reservation. A redundant status round trip was removed; the prepared descriptor
  transfers a conservative renderer deadline. Capture queues and resumes; a newer
  source/context invalidation preempts immediately. UTC offset uncertainty is at
  most 250 ms and local timers remain monotonic. Failure clears and records a
  rejected attempt; it never extends expiry or reuses stale fallback text.
- The extension replaces its full pointer-transparent shadow/SVG layer and
  acknowledges only after visible compositor frames. Paint/cancel ACKs use v0.2
  and are signed by the connection key. Rejected consumer attempts are separately
  recorded without claiming verified paint. Exposure persistence never changes
  a tracker revision, checkpoint, criterion or understanding assessment.

Source events clear locally at once. Ordered producer cancellations preserve the
high-water sequence; an older cancellation cannot preempt an already admitted
higher-sequence delivery. Late signed exposure receipts may be recorded as history
with `late_context=true`; this does not authorize drawing, revive a packet or
extend its lifetime. Source hashes alone never authorize a live cue.

Actual controlled browser tests exercise native getDisplayMedia in a persistent
(non-incognito) Chromium context, the real capture/reader/Worker/broker/consumer
and compositor, signed frame/paint validation, independently checked blue pixels,
periodic frames during a delayed single analysis and stored exposure receipts.
Chrome API dispatch and localization are explicit fixtures. These are not an
installed-extension or real-Simulink recognition acceptance claim. Initial
incognito source-binding and exhausted-reservation failures are retained in the
integration evidence, not relabelled as successes. The original viewport smoke
is not used as a tutor acceptance gate.

## Hosted timing correction — 17 October 2026

The controlled local browser proof did not reproduce hosted DB/clock latency. Live drawing analyses committed on 17 October, but inspected exposure rows contained only rejection/cancellation receipts; no paint was established. Old rejection receipts used the generic `consumer_validation_failed`, preventing exact historical stage attribution.

Renderer now computes a conservative clock-offset interval from the clock endpoint's request-received and response-sent UTC timestamps. Server processing is excluded from network uncertainty; the 250 ms limit and integer timestamp margin remain. Legacy endpoints without receive timestamps retain the previous conservative whole-round-trip treatment. Excess actual network uncertainty still rejects drawing. Integration must add the receive timestamp while preserving owner checks.

Actual paint establishes a minimum readable interval of up to 2.5 seconds, bounded by the packet's original expiry; `nextCheckDelay` lets integration defer automatic rechecking during this interval. Source/context invalidation still clears immediately. Rendering/ACK never advances a checkpoint. Client rejections now retain their bounded actual reason in the existing v0.2 ACK field, instead of discarding it behind a generic label. These changes affect reader assets; the installed extension protocol/version is unchanged.
