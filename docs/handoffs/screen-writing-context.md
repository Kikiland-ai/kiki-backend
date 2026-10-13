# Provisional context for screen writing and DSB-SC lab guidance

14 October 2026 (Asia/Calcutta) · Contract proposal v0.1 · Reconcile with the parallel renderer before stabilizing

## Read this first

This handoff is for the user's parallel screen-writing work. The supplied chatgpt.com/local conversation link returned 404 through the available reader; its contents were not inspected. The interface proposed here is grounded in this thread and the scoped repository files. Use the user's corrections and the actual renderer's capabilities to reconcile it. No message was sent to the other chat.

The selected demo is **PR-AM-DSB: DSB-SC modulation and coherent demodulation in Simulink Online**. The student builds the model, runs baseline recovery, introduces a relative 90° receiver phase fault, then restores/reruns/saves/explains. The student performs every real action; the screen-writing component only marks/explains.

## Files to share

- ../../contracts/screen_writing.schema.json: proposed screen-writing/v0.1 cue packet.
- ../architecture/examples/screen-writing.synthetic.example.json: valid but wholly synthetic frame/geometry/context. Its coordinates and hash do not describe the user's actual screen.
- ../../contracts/lab_tracking.schema.json: proposed lab-tracking/v1 session/progress schema.
- ../architecture/examples/dsb-sc.demo-definition.json: twelve source-derived checkpoints with proposed subcriteria, block inventory and parameters.
- ../architecture/dsb-sc-lab-prototype.md: source analysis, learner/telemetry boundaries and prototype plan.
- ../../scripts/check-screen-writing-design.py and ../../scripts/check-lab-tracking-design.py: structural/reference checks; neither proves visual accuracy or a live overlay.

Fetch upstream main plus this handoff branch when using another checkout; use the exact commit supplied by the originating chat. The handoff commit contains these dependency files so relative references resolve. Treat this as a provisional agreement, not a claim the other chat adopted it.

## Provenance and selected experiment

The two authored source JSONs were read at Design-Thinking commit 2a6c843448d81062f89596b941516f8b7817ec79:

- data-model/ledgers/electronics/analog-modulation.json, lesson-ledger/v2; blob 7e54eabba9aee6108bf0f3d3b742fb8e6da1c797.
- data-model/cases/analog-modulation-odia.json, learning-case/v1; blob 78b47d2e7cd4f84b7f7f586f4af5dcfa6631acee.

IDs join as CRS-AC-ECE / LP-ANALOG-MODULATION / PR-AM-DSB. Twelve ledger steps and case checkpoints match exactly; ten blocks and eleven connections. The source is draft/unverified for real simulator execution and Odia review. Synthetic seeds are not the user's state. Do not rewrite the backend's separately pinned 130-file context snapshot.

Baseline: Message amplitude 1, bias 0, 100 Hz, phase 0; transmitter/local carriers amplitude 1, bias 0, 2000 Hz, phase pi/2. Continuous time-based Sine Wave Frequency uses 2*pi*f rad/s and SampleTime 0. Product -> receiver Product -> second-order 500 Hz Butterworth Transfer Fcn -> Gain 2. Stop 0.1 s, ode45, max step 1e-5 s. Filter numerator [9869604.40109], denominator [1 4442.88293816 9869604.40109]. Recovery is predicted near 100 Hz/unit amplitude with filter lag/ripple. Only receiver phase changes to pi for the intentional fault; this is a relative 90° error. Restore pi/2. Other fault variants are deferred.

Checkpoint IDs CP-DSB-01..12 mean: workspace; place sources; configure sources; transmitter; local carrier/receiver; lowpass/gain; scopes; simulation settings; baseline run; inspect recovery; phase fault; restore/run/save/explain. Use the definition file for exact English/Odia instructions, reasons, dependencies and subcriteria.

## Contract between observer, tracker and writer

Observer publishes actual analyzed-frame provenance and visible evidence candidates. The tracker owns the current checkpoint/visit, conditions, parameter version, reviewed completion, queue and conceptual evidence. The writer consumes a **bounded cue packet** derived from that accepted context. Drawing a cue never marks a step done or proves learning.

Every packet binds lab_session_id, experiment_id, checkpoint_id, visit_id, lab_revision, workspace_id, capture_epoch, parameter_revision and condition. It identifies the observation and actual analyzed frame ID/hash/receipt time/encoded dimensions. A stale response may remain in historical evidence, but must not mark the currently active workspace.

The v0.1 operation set is pointer, box, ellipse, arrow, polyline and text. Polyline can reveal a bounded path over time; this is a rendering duration, not invented audio alignment. Operations include an accessible label, stable cue/layer IDs and meaning. Meaning colours stay concept=green, words=red, english=yellow, lab=blue. Render text as text, not HTML. No arbitrary JavaScript, raw SVG programs, selectors or autonomous clicks are in this contract.

## Coordinates, validity and fallback

Coordinates are normalized [0,1] in the **encoded analyzed frame**, never guessed desktop CSS pixels. The runtime checks that rectangles stay in-frame. For a preview renderer, map through its actual contain/crop/scale transform; letterbox offsets matter. The external Simulink workspace needs a separately proven adapter/transform. Schema validity does not establish target recognition.

The schema can describe captured_frame or live_workspace delivery. Current proof covers sharing/analysis, not a supported overlay in Simulink's origin. The live renderer must reject packets unless its actual adapter and workspace mapping are verified. A captured-frame cue cannot be credited as a real workspace overlay.

Maximum cue lifetime is eight seconds, with an absolute expiry and source-frame age ceiling of twenty seconds. Invalidate/reobserve on workspace/epoch/step-visit/parameter-version changes, scroll, zoom, resize, canvas pan, modal changes or disconnection. Fixed expiry alone does not detect these changes; the adapter must deliver invalidation events. Do not continue showing a mark when observation is paused/stale or target identity is uncertain.

For unresolved anchors, operations is empty, target region is null and the plain-text instruction remains. All drawn layers are pointer-transparent, clipped to the opted-in frame/surface and removable. The implementation must enforce these rules; putting pointer_events:none in JSON alone does not enforce browser behavior.

Keep scene-object anchors for authored graphics separate from these expiring screen-frame anchors. Reuse rendering primitives, not one misleading universal target lifetime. Audio synchronization remains a separate verified timing contract.

## Prototype state and coordination

The working private Site is https://kiki-screen-receiver.woodsycarp256.chatgpt.site. The user confirms capture and generic Gemini frame descriptions work. Source is a separate Sites repository checked out at /workspace/sites/kiki-screen-receiver, project appgprj_6ace6ce34218819198dfd778a822aed5. Runtime key/signing secrets remain server-side and must not enter this handoff/source.

The local FastAPI receiver remains receipt-only; Python is still the selected product backend. The thin Worker gives this interface private HTTPS access. This thread continues focused lab-tracker/contextual-observation implementation. At handoff creation, persistent lab integration and an authorized live read tool for this chat are not yet verified; consult the originating thread's next update for the published state. The writer can build against the committed synthetic packets while those adapters advance.

The current trial caps are thirty-minute capture segments and thirty model starts; an authored forty-minute lab needs persistent lab state across capture restarts and explicit model admission. No image/video archive exists. Compact experiment events and selected frame provenance are enough for early telemetry, but a hash cannot reconstruct discarded pixels for later visual re-review.

Normal learner prerequisites remain seven relevant concept checks at 60%, with no 80% chapter gate. Builder trials can record an explicit operator override without inventing passed checks. Language/self-confidence and conceptual evidence remain separate. Student-reported or unreviewed model completion is not verified completion.

## Parallel implementation boundaries and next action

This thread owns observation/progress/context and canonical now/next instructions. The parallel screen-writing work can own packet validation, semantic-anchor resolution, preview rendering, a proven live adapter, clipping/coordinate transforms and cancellation. Confirm changed field names and capabilities through a versioned revision of this document/schema. Do not mutate source experiment IDs or treat synthetic example coordinates as actual anchors.

First renderer acceptance: render the synthetic packet on a controlled captured-frame preview; reject stale/foreign/expired/unresolved/out-of-frame packets; verify mapping after resize/crop and pointer-transparent interaction. Then prove actual Simulink adapter geometry separately. Last completed action at initial handoff: schema/example/context prepared and checked. Exact next action: use these files to reconcile the parallel renderer's input contract while the lab loop is implemented here.
