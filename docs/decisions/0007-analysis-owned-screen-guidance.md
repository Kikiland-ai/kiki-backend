# Analysis owns the drawing decision; the extension owns presentation

15 October 2026. Proposed integration following the user's correction and the
failed live writer trial. This document records the next interface; it does not
claim that interface is implemented or that live Simulink now works.

## Evidence and outcome

The required result is timely, semantically correct shapes and notes on the actual
shared Simulink tab, with placement derived from its analysed pixels. A selected
extension tab, a preview image or a drawing smoke test is insufficient.

The uploaded adapter 0.3.1 diagnostics report a selected MATLAB tab, no paint ACK,
and repeated `producer_cancel` events without source revision advancement. They
do not identify the reader's rejection reason. `producerConnected:false` is a
hardcoded field; `captureCount:0` describes the optional offscreen capture, not the
reader's live display stream. A startup `writer_clear` error can remain stale.
Later production logs include successful bound checks and exact-frame retrieval;
these later events cannot be assumed to describe the same attempt as the upload.

Inspection also found reproducible orchestration defects: capture pixel changes
retire pending analysis, and periodic capture can mask the source between final
verification and visible ACK. Local fixes and seven consumer regressions are on
`integration/screen-writing-v1`, pending integrated acceptance. These defects are
not independently proven to be the unique cause of the user's browser failure.

## Reader branch inspected

Fetched `experiment/stream-context-batch` at
`ae234dcdd78b91ef7d6e6b528b14f2e9196808bb`; last runtime change is
`9af91d6d3019b602d506d4f3ef2a31662fe4c998`. The branch's draft promotion PR is
[#1](https://github.com/Kikiland-ai/kiki-backend/pull/1). It has not been merged
into baseline by this session.

Relevant sources inspected with `git show`, without checking over local work:

- `docs/experiments/stream-context-batch-implementation.md`
- `docs/experiments/short-decision-implementation.md`
- `docs/experiments/provider-db-io-implementation.md`
- `docs/experiments/json-stream-implementation.md`
- `docs/reviews/screen-reader-baseline-promotion.md`
- `prototypes/json_stream_site/worker/stream.js`, `stream-core.js`, `context-batch.js`
- `prototypes/json_stream_site/assets/json-stream-client.js`, `assets/lab.js`
- `prototypes/json_stream/decision.py`

Its short model decision has exactly `criteria`, `action_findings`, `uncertainties`.
Both parsers enforce that field set. There is no geometry/drawing output. The
bounded `committedProjection`/`committed_projection` omits screen-writing runtime.
The original hosted reader is deliberately frozen in that branch; its active
hosted implementation is `prototypes/json_stream_site`, not
`prototypes/hosted_screen_reader`. Copying only the extension into that Site would
not wire a producer. Its Site origin is also absent from the current extension's
controller allowlist.

The writer integration currently requests target localization in the same model
call as observation. It does not make a second model call to draw. However,
`worker/writing.js` chooses operations separately and the browser performs extra
fetch/validation transactions. Missing model drawing intent and delivery races
are distinct issues; adding a JSON field alone cannot repair the latter.

## Decision boundaries

| Owner | Inputs and outputs | Decision allowed |
| --- | --- | --- |
| Reader analysis | Exact admitted frame, current/eligible authored actions, bounded target catalogue -> findings plus `screen_guidance` | Select a cue/primitive, locate its targets, or explicitly decline geometry |
| Tracker and admission | Complete validated response + current authoritative context -> canonical now/next + accepted drawing packet | Determine practical progress and canonical instructions; admit only the candidate for the resulting current action |
| Delivery coordinator | Accepted packet + source binding -> ordered replace/cancel/ACK | Check source, freshness, transform, context and expiry; no teaching interpretation |
| Extension compositor | Valid packet -> shapes/text on the connected live tab + paint ACK | Deterministic rendering, immediate source-event cancellation and exposure telemetry |

Model localization/shape intent happens once. There is no second LLM, semantic
resolver or generated teaching-prose pass after analysis. Mechanical validation,
coordinate conversion and freshness checks remain necessary. They must not be
confused with another reasoning/model stage.

For this instruction-based lab, note text references the tracker-authored
instruction or an authored setting/label. The model cannot invent parameter
values, actions, progress or instructions. Concept explanation/animated graphics
are a separate content path and are not put on the lab delivery critical path.

## Proposed model addition (not a published schema)

Use a versioned successor to `lab-observer-decision/v1`, with the existing three
fields and one bounded `screen_guidance` array. Example field only:

```json
{
  "screen_guidance": [
    {
      "action_id": "CP-DSB-03/message-settings",
      "mode": "annotate",
      "targets": [
        {
          "target_id": "message.frequency",
          "status": "resolved",
          "region": {"x": 0.25, "y": 0.325, "width": 0.18, "height": 0.07}
        }
      ],
      "marks": [
        {"kind": "box", "target_id": "message.frequency"},
        {
          "kind": "text",
          "anchor": {"target_id": "message.frequency", "u": 0, "v": 1},
          "text_ref": "canonical_instruction"
        }
      ]
    }
  ]
}
```

Numbers above are illustrative, not recognition of the user's screen. In the
first slice, bound the request to the current action and at most one authored
immediate successor, with at most two targets and four marks per candidate. Expose
only authored IDs/eligible actions, allowlisted primitives and normalized
frame-relative geometry. No raw SVG, HTML, script, CSS or model-generated clocks,
frame IDs, context IDs or expiry. Validate duplicates, bounds, target references,
operation limits, mode and target-resolution consistency. Explicit `text_only`
with unresolved targets has no anchored marks; `none` emits no marks or notes.

The optional successor candidate addresses a temporal problem: tracker support
can advance the current action after the observation is committed. Select only a
candidate whose action matches the resulting canonical current action. If none
matches, emit no drawing and use the next normal periodic observation. Never
relabel old-action geometry or add a second vision call to repair that response.
An instruction reference is resolved against the committed action, not arbitrary
free text generated before that action was known.

## Delivery and latency contract

1. The existing single display stream supplies a frame and source binding.
2. The same analysis request returns findings and its bounded drawing candidates.
3. Full JSON, provider STOP and authoritative context/progress validation admit
   one candidate. Unresolved required targets permit canonical text only in valid
   current context. A stale packet permits nothing, including fallback text.
4. The early `guidance_committed.state` carries the accepted writing packet. Do not
   wait for `state_snapshot`, summary generation or history to start presentation.
5. One coordinator owns final live-source verification through visible paint ACK.
   Capture queues behind that short transaction. A newer context/cancel preempts
   it; repeated UI renders do not start duplicate deliveries.
6. The extension replaces the complete layer, applies sequence/expiry/transform
   fences and reports actual paint. It does not interpret analysis findings.

Retain `screen-writing/v0.2` request/resolved/cancel contracts and provenance. A
small deterministic server adapter may wrap the validated model marks and resolve
instruction references into that packet; this is not another decision-making
stage. Version the model output and explicitly negotiate a successor stream
capability/version for the changed committed projection; do not append a field to
the current strict parsers and assume compatibility.

Use the immutable selected JPEG already retained by the capture transaction for
provenance verification where available. Avoid downloading that same frame again
on the healthy path. Broker fallback must retrieve the exact admitted frame and
verify identity; a newer screenshot is not a substitute. A current pixel/source
freshness check is still needed for remotely rendered canvas motion that DOM
hooks do not observe. It must not silently be removed to save latency.

Retain batched provider routing, fresh per-event-bearing-chunk context validation,
independent committed/tail promises and existing cancellation. Do not introduce a
state TTL cache or a DB read per mark. Bounded extra model output can increase
completion latency: measure decision STOP, commitment, delivery validation and
visible paint separately, including slow/discarded cases. No speedup is asserted
from moving fields alone.

## Concrete producer-side changes for the reader session

1. Extend `prototypes/json_stream/analysis.py` and hosted `worker/analysis.js` /
   `worker/stream.js` request/schema with authored eligible-action drawing context.
2. Extend both strict parsers (`parser.py`, hosted `stream-core.js`) and final
   validators for the complete typed field, including malformed-later-output and
   non-STOP negative cases. Provisional findings stay tentative and never draw.
3. Attach the admitted drawing to the authoritative result after action selection;
   add it to `decision.py` and hosted `committedProjection`. Supply it with the
   earliest committed state and ordered cancellation, not the auxiliary tail.
4. Update the stream consumer contract/client deliberately and cover blocked tails,
   newer revisions, candidate/action mismatch, omission and stale context.
5. Coordinate the chosen hosted origin, frame/binding transport, authentication,
   clock bounds and version negotiation with the writer before live coupling.
   Preserve current owner-private audience, receipt signer, keys and learner run.

This session owns compositor/delivery behavior and tests. These changes describe
cross-session coordination; no messages were sent to another person/session and
no unpublished transport/authentication contract is represented as agreed.

## Acceptance and staged migration

Preserve the frozen writer and reader branches. Work against a pinned copy of the
latency branch on an independent integration branch; promotion to baseline is a
separate decision. Do not replace either currently deployed Site while that
interface remains unresolved.

First pass offline tests through the actual producer, strict parser, committed
projection, consumer, broker and real compositor, with a delayed single provider
response and periodic captures. Require visible pixels at independently measured
control coordinates and a persisted exposure ACK, not just an ACK-shaped fixture.
Cover unchanged view, hidden/ambiguous target, wrong parameter, action advancement,
resize/zoom/navigation, stale/reordered/cancelled packets, blocked auxiliary tail,
and capture competing with painting. Compare latency and extra tokens against the
same branch without drawing; no second analysis call may appear.

Then sample installed Chrome extension + actual Simulink sharing. Existing local
Chromium blocks unpacked extension loading. A local native-capture integration
attempt also returned no cross-origin Capture Handle despite capturing the
correct controlled source pixels; it stopped at source matching and did not paint.
That failed attempt is not a successful full-path result or evidence that the
user's installation has the same issue. Do not substitute a smoke-test drawing or
relax source/freshness validation to mark it passed.
