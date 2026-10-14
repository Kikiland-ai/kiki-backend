# Screen awareness: Now / Next / Later

Date: 13 October 2026 · Status: capture works in the user browser; bounded hosted analysis implemented, tested and privately published; durable history/evidence and graphics remain next

## Implemented first slice

The user subsequently requested starting the MVP with Share screen -> small server receives screen data. The [receiver](../../prototypes/screen_capture/README.md) is implemented and running locally, with native Chromium fixture tab capture and 41 repository tests passing. It displays actual received frames and receipt JSON. The separate private hosted Site now adds a bounded Gemini analyzer, observation JSON and source-frame provenance: see [decision 0003](../decisions/0003-selected-frame-analysis.md). Adaptive sampling, archived evidence, durable hosted history and broader execution design below remain subsequent work. See [decision 0002](../decisions/0002-screen-capture-receiver.md) and [active continuation](active.md) for actual results and the user-access boundary. The historical design-only scope below describes the original planning phase, not a prohibition on the now-authorized receiver.

## Objective and success

Build a bounded browser screen/tab observation capability: sharing starts, the system analyzes selected frames, and a JSON observation updates with evidence and a chronological history from session start. The first milestone is awareness of visible screen state. Subsequent milestones turn that evidence into instructional steps and graphics cues.

Success means observations reference actual analyzed frames, uncertain or unseen details stay explicit, old results cannot replace newer state, interruptions are recorded, and cost/storage remain bounded. A sampled session must never claim uninterrupted visual coverage.

## Current state and authority

- The user selected browser screen/tab sharing and an updating observation JSON with provenance. They asked for endpoint design and a build document, and requested help choosing video versus images at a possible 0.5 Hz cadence.
- FastAPI and a logical worker/actor hierarchy are existing backend directions. A queue, actor framework, store and screen provider remain unselected.
- Recommended MVP: sampled images over WebSocket, a transport-independent frame contract, append-only events and a latest-observation projection. WebRTC is an alternative requiring its own feasibility comparison.
- These documents authorize no implied implementation, provider calls, deployment, commit or push. This task writes design documents only. Existing translation/audio code and pinned source files stay unchanged.
- Repository baseline inspected: main contents at 1b68183776d4476a19529c428f0d09950af949f6; product snapshot at 73d16c0d967a5d81dd74f1f28ef0defc48c8a778. See [build document](../architecture/screen-awareness-mvp-build.md), [graphics handoff](../handoffs/graphics-and-annotation.md) and [backend execution design](../architecture/mixed-language-fastapi.md).

## Intent and boundaries

User-stated first outcome: an observation field in JSON that keeps updating with provenance since screen recording/sharing started. Interpretation: evidence-grounded current awareness plus session history, with sampled coverage disclosed. Full-video retention is a separate product choice, still open.

The broader workstream is a teaching companion that observes, understands, proposes an instructional step, draws a cue, waits for the student's action and verifies the result. This capability supplies the evidence boundary. A model description is not a verified lab checkpoint or mastery score.

## Now: design and then the smallest observation prototype

The current documentation phase is complete once the design, tradeoffs, arithmetic and continuation are checked. The following build sequence remains pending implementation authorization.

| Sequence | Work | Completion evidence |
| --- | --- | --- |
| 1 | Define session, frame, event and observation runtime schemas; choose one authoritative store and configure budgets | Reject malformed inputs, unowned sessions, stale epochs and unsupported references |
| 2 | Browser sharing and frame sampler; a fixture observation adapter; FastAPI session/read endpoints and WebSocket ingress/events | Sharing produces ordered timestamped frame envelopes; latest JSON and event replay work without a live model |
| 3 | Bounded per-session coordinator and shared analysis workers; persistence and recovery | One in-flight analysis plus one replaceable pending frame; duplicates, disconnects and restarts do not corrupt history |
| 4 | Evidence retention and status display | Every analyzed frame has retrievable evidence within retention; expiry and capture gaps are explicit; configured byte/session caps are enforced |
| 5 | One live vision adapter on a labeled task set when provider trial scope is authorized | Compare claims with reviewer labels and measure freshness, accuracy, latency, model usage and retained bytes |

Prototype starting assumptions: candidate sample every 2 seconds (0.5 Hz), forced model refresh at most 10 seconds apart when capacity permits, maximum 0.5 analysis admissions/second, 30-minute session, 20-second client ring buffer, 100 MB raw-evidence budget/session, raw evidence retained up to 24 hours and JSON history up to 7 days. These are tunable proposals, not measurements or accepted production policy. Stop/pause if reliable provenance cannot be preserved within the budget.

At 100 KB/frame, a continuously changing 30-minute session contains up to 900 candidates and 90 MB. Adaptive selection can reduce that; measure it instead of assuming a reduction percentage. Storage batching can follow after object-operation measurements warrant it.

## Next: validate cadence, then connect decisions and drawing

1. Compare fixed 0.5 Hz sampling, change-filtered 0.5 Hz sampling and a short authorized WebRTC video trial on the same scripted interactions. Score persistent states separately from short transitions, motion and action order. Record missing intervals.
2. Choose image-first if visible-state recognition passes the agreed task criteria; choose video if transient-event or sequence failures remain consequential and video improves them within bandwidth/compute limits. WebRTC transport alone does not fix a model still reading only every two seconds.
3. Test the selected capture mode on the actual Simulink account. Screen sharing can expose pixels without DOM access; actual tool content, legibility and correct workspace recognition still need proof.
4. Define bounded next-step instructions with reasons, semantic target references and evidence-based completion predicates. Preserve student actions and distinguish observed results from inferred or manually confirmed completion.
5. On a controlled page, connect fresh anchors to shared SVG/Canvas pointer, halo, arrow and text primitives. Prove geometry mapping and stale-cue cancellation. Separately establish a supported real-tool overlay integration.
6. Measure object-operation overhead before adding evidence packs; test higher local sampling and slower analysis separately if short transitions warrant it.

Completion: reviewed visible observations become a correct proposed step and a fresh cue; the student acts; new evidence confirms the checkpoint. Reading a screen and drawing over the real tool remain separate acceptance gates.

## Later: richer graphics, temporal understanding and scale

- Editable reviewed VCO scene, poster and GIF export; scene-object, uploaded-page and localized-span annotation targets.
- Teaching-canvas synchronization using validated real audio times. Existing total clip duration supplies no sentence/word alignment. Live guidance remains checkpoint-driven.
- Optional full recording or bounded video clips, temporal model analysis, WebRTC receiver/TURN where justified, more tool integrations and longer sessions.
- Shared worker capacity controls, larger traffic benchmarks, more reviewed templates, device handoff and learning-evidence integration.

## Tradeoffs and unresolved decisions

| Item | Recommendation or question | Resolution |
| --- | --- | --- |
| Transport | Recommend frame WebSocket for the first JSON-awareness slice | Reviewer task results determine whether video is needed |
| Recording | No full-video archive by default; selected evidence only | Confirm whether users need full replay versus observation traceability |
| Cadence | 0.5 Hz is a starting measurement point, not video continuity | Test brief parameter changes, dialog transitions and drags |
| Provider | Hosted trial uses gemini-3.1-flash-lite; two controlled image checks passed | Validate structured output, text legibility, latency, quotas and actual charges |
| Retention | Short-lived raw evidence, longer bounded JSON history | Agree product policy; measure bytes; maintain explicit expiry |
| Runtime | One FastAPI codebase, durable session coordinator and bounded shared workers | Select store/queue before implementing restart behavior |
| Graphics | Reuse drawing primitives; keep target/timing contracts distinct | Prove controlled-page geometry and actual tool overlay separately |

## Risks and controls

- Short actions can fall between samples: report sampled coverage; compare video or faster capture against labeled interactions.
- Small parameter edits can be filtered out: use tile/region-sensitive change detection, forced refresh and a dedicated tiny-text test.
- Model calls can lag or exhaust quota: bounded queue, age check, admission budget and degraded-state reporting.
- Summaries can carry old errors: facts reference direct frame evidence; bounded summaries remain derived; new frames may correct prior claims.
- Raw evidence can grow without limit: enforce byte/duration/retention caps and explicit pause behavior before capacity is exceeded.
- Cross-window pointers can be misplaced: obtain separate overlay/geometry proof; observation pixels alone grant no injection capability.

## Cold-pickup handoff

- Last completed action: implemented/tested capture and bounded hosted frame analysis; actual publication and verification records are in active.md.
- Current state: native capture, receiver endpoints and bounded hosted analysis exist. The original FastAPI remains receipt-only. No WebRTC media receiver, durable hosted observation/evidence journal, planner or overlay exists.
- Exact next action: review real shared-screen descriptions after refreshing the private Site, then evaluate labeled states and implement durable session/evidence controls before attaching instructions/cues.
- Open first: this plan, the linked build document and graphics handoff. Reuse the accepted FastAPI/worker hierarchy.
- Do not repeat: translation/audio generation, source refresh or broad backend scaffolding.
- Keep: append-only event history plus current observation; separate capture/analysis/retention; explicit sampled gaps; student performs actions.
- Next intent checkpoint: after the fixed/adaptive/video comparison, resolve whether full recording or transient-action understanding is a requirement.

## Change log

| Date | Change | Reason |
| --- | --- | --- |
| 2026-10-13 | Added this scoped plan and MVP build design | User requested Now / Next / Later, endpoint design and help with image/video/storage choices |
