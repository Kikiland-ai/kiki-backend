# Other-session handoff: direction 3 graphics, pointing and annotation

Date: 13 October 2026 · Status: ready for design/feasibility investigation; implementation scope not yet selected

## Mission and current user direction

The user accepted the mixed-language/audio prototype, selected FastAPI for future backend development, explicitly said **do not start building**, and requested a handoff for another session to figure out the graphics-generator direction together with onscreen pointing and annotation.

Investigate **direction 3 (graphics)** and its connections to **direction 4 (teaching-canvas annotation)** and **direction 7 (live-screen guidance)**. Deliver a concrete bounded design, contract proposals, renderer/provider options and a feasibility plan. Do not merge these three into one anchor/timing model or begin a broad backend build. This handoff does not independently authorize paid model trials, installing an extension into a real tool, external account actions, deployment or commit/push.

BB8 reference route: coordinator → `engineering-architecture`; use prompt-design guidance only if designing a model-to-graphics-spec prompt. Native host activation is not established by repository files. Do not rebuild the translation/audio pipeline or recruit extra agents just because another session is involved.

## Checkout and transfer warning

Repository: `Kikiland-ai/kiki-backend`, expected `/workspace/kiki-backend`. The session started on `continuation-mixed-script` at `00fbd8fa00199156a89a3d2202a005bf5a33b495`, matching `origin/main`. The user subsequently authorized committing/pushing all session work. This handoff is part of that publication: fetch the current `origin/main` and verify the BB8 skill, prompt/speech code and this document are present. A checkout of the original pipeline commit alone will not contain them. Report incomplete transfer/publication instead of recreating the pipeline.

The original ignored `work/` layout and separate Site checkout remain runtime-local, but the user-authorized [evidence archive](../../prototypes/mixed_script/evidence/2026-10-13/README.md) now preserves the generated text, requests, failures, historical drivers and actual WAV/MP3 recordings in the repository. Use it when the original paths are absent; do not automatically execute its historical drivers.

Inspect branch/HEAD/status first. Preserve dirty/diverged work. Pull `--ff-only` only when clean/on the appropriate main checkout; never reset, force-push or merge superseded history. Later explicitly authorized commits must follow `AGENTS.md`'s `arpanvihan5-sketch` identity checks.

## Reading order

Follow `AGENTS.md` and `CONTEXT-BOOT.md` first, using [context precedence](../../context/README.md). Read `SETUP.md`, source authority/known gaps and the pinned `SOURCE.json`; then:

1. [Active continuation](../plans/active.md), [chosen translation/audio pipeline](../decisions/0001-mixed-language-audio-pipeline.md) and [FastAPI assessment](../architecture/mixed-language-fastapi.md).
2. [Latest student journey](../../context/design-thinking/docs/ux/student-journey-odia-ece.md), [seven directions](../../context/design-thinking/docs/prototypes/backend-prototype-directions.md), especially 3/4/7 and annotation boundaries; [original handoff](../../context/design-thinking/docs/plans/backend-prototype-handoff.md) as historical proposal.
3. [Content contracts](../../context/design-thinking/data-model/types/content.ts) and [data-model notes](../../context/design-thinking/data-model/README.md). `Visual` and `WalkStep` are seeds, not implemented scene/timeline contracts.
4. Component READMEs: [KikiWalkthrough](../../context/design-thinking/design-system/project/components/KikiWalkthrough/README.md), [KikiPointer](../../context/design-thinking/design-system/project/components/KikiPointer/README.md), [Spotlight](../../context/design-thinking/design-system/project/components/Spotlight/README.md), [LabGuide](../../context/design-thinking/design-system/project/components/LabGuide/README.md), [AnswerOverlay](../../context/design-thinking/design-system/project/components/AnswerOverlay/README.md); inspect only the relevant [bundle.js](../../context/design-thinking/design-system/project/components/bundle.js) sections.
5. For live-tool feasibility, the [Simulink recommendation](../../context/design-thinking/docs/ux/experiment-recommendation-simulink.md). Account/model/overlay access remain unverified; DSB-SC is a proposed experiment, not an accepted running model.

Source pin: `73d16c0d967a5d81dd74f1f28ef0defc48c8a778`, 130 files. Keep it immutable; new decisions belong under `docs/`, eventual reconciled runtime contracts under `contracts/` when implementation is authorized.

## Available evidence and dependencies

The chosen flow is English → Odia-led translation → natural mixed script → validation → speech-ready text → Gemini TTS → checked audio. Two proficiency numbers independently condition language policy; 5/7 has been trialled, arbitrary values are not implemented. The v2 prompt is VCO-specific.

The user also endorsed a worker/actor hierarchy for backend job management: admission/supervision → durable per-job coordinator → bounded stage-worker pools → provider adapters. See the [architecture](../architecture/mixed-language-fastapi.md#worker-and-actor-hierarchy). A future graphics render worker can fit this execution boundary; live-screen guidance still needs a distinct interactive session lifecycle. No actor runtime/queue has been selected or implemented.

Four-sentence VCO and held-out cases completed both raw text stages. The longer eight-sentence candidate remains a translation draft with label-only repair, three phrase warnings and a 503-blocked final refinement. Its real Flash Lite TTS/Kore recording lasts 104.8 seconds. The user's positive response accepts the direction, not a recorded scientific/native review of every sentence.

Listen through the owner-private page: https://kiki-vco-listening-draft.woodsycarp256.chatgpt.site . Local results are under `work/longer-vco-tts/`; original completed text is under `work/prompt-hardening/`. Do not assume those files transfer to a new runtime. Preserve source/sentence/term IDs and use the accepted canonical source rather than inferring scientific facts from a generated translation.

**Only full-clip duration exists. No sentence/word timing or validated alignment is available.** Never divide total duration evenly across sentences or use the old fixed `stepMs` walkthrough timer as actual narration alignment. Any provisional manual timeline must be labelled an authoring fixture. Investigate sentence-level alignment/provider timestamp options separately and validate them on code-switched speech before synchronized claims.

## Workstream A: graphics generator

Compare a restricted semantic spec plus deterministic SVG/Canvas renderer with model-generated raster/video assets. Favor the semantic route when precise labels, equations, topology, editable parts and stable targets matter; generated illustration assets may be supporting layers. Do not treat arbitrary generated programs or a raster image alone as a validated scientific scene.

Propose a small `GraphicsSpec` containing scene/source/version, objective/claim references, semantic object IDs, coordinate viewBox, units, reviewed parameters, allowed primitive types, animation phases and review labels. Separate scientific intent from rendering. Keep labels selectable/accessibly described; latest source policy keeps SVG labels English with Odia explanation alongside them.

Recommended first **candidate**, not a new confirmed science lesson: a VCO input → oscillator → output scene tied to the existing equation and ±0.5 V examples, with stable targets for control input, frequency and the ideal-model qualification. Review any time-varying waveform assumptions explicitly. The original proposal's diode depletion-width comparison is a valid alternative with existing assets; choose one concept, not a universal engine.

Retain an editable scene, static poster and **GIF export**. GIF has no audio and poor seek control; use the live semantic scene or a seekable derivative for synchronized lessons. Motion should teach a reviewed relationship, not just decorate the explanation. Identify scientific checks (values/polarity/arrow meaning/waveform relation), repeatable re-rendering, phone legibility, font/Unicode handling, duration/size, reduced-motion behavior and loop continuity.

## Workstream B: generated-image/page pointing and writing

Propose separate `AnnotationLayer` and `AnnotationOp` data rather than baking the only editable marks into the base asset. A small first set can include pointer, highlight, arrow, circle/box, path and text/equation. Keep author/layer/version, semantic purpose, target reference and operation geometry. AI, teacher and student marks need distinguishable ownership; source media stays immutable.

Retain current semantic colours: green concept, red technical terms, yellow academic English, blue practical. Older component proposals do not supersede the current student journey.

Anchor generated scenes by **scene object ID**, mixed text by localized **span ID** plus script version, and uploaded pages by **original asset coordinates** plus asset version. Carry crop/scale/rotation/display transforms. Test one generated scene and one uploaded page; do not make annotations work only on the hard-coded demo.

The current script contract has stable sentence IDs and ordered language spans, but no persistent per-span IDs or display-to-spoken alignment map. Those annotation bindings are a proposed extension, not existing data. Preserve the sentence/term contract and propose a compatible versioned mapping rather than treating span positions as stable across different translations.

An eventual `LessonTimeline` maps reviewed speech/sentence/term references to scene phases and annotation operations using real audio times. The frontend owns the audio master clock and rendering. Pause, seek, replay, playback-rate changes, resize/zoom and profile/script changes must update/cancel all relevant tracks. Do not map translated text by English phrase search alone. A new audio or time-stretched derivative invalidates the old alignment manifest.

## Workstream C: live-screen pointer feasibility

Share drawing primitives with the canvas, but use a different live contract: `ScreenObservation`, `ScreenAnchor` and expiring `GuidanceCue`. Carry workspace/capture/session version, observed time, target identity/confidence, coordinate space, dimensions/crop/scroll/zoom/pixel ratio and invalidation rules. Prefer tool/semantic DOM anchors where accessible; simulator canvas objects may not have useful DOM selectors.

Ordinary FastAPI code cannot inject an overlay into another application's origin. Investigate a supported tool adapter, consented browser extension or separately permissioned integration; verify actual access before claiming a connected pointer. A controlled page can test geometry and stale-cue cancellation, but cannot establish real Simulink feasibility. Screenshots/manual guidance must be labelled as that mode.

Cancel/reobserve after scroll, resize, navigation, modal/canvas movement, workspace change or disconnection. Missing/low-confidence/stale targets pause guidance. Keep overlays pointer-transparent and bounded to the opted-in workspace. The student performs actions; the pointer may demonstrate a ghost action but must not click, wire, run or correct the actual model for them.

Retain the confirmed activation sequence: experiment selected → required concept checks passed at 60% → correct model workspace opened → observation connection confirmed. The chapter 80% theory test is a separate gate. Opening Lab mode alone does not activate observation. Stop/pause/disconnect and same-account device/session lease rules are part of feasibility, not cosmetic UI.

## Outputs, acceptance and next action

Deliver a source-linked design note, renderer/integration comparison, small proposed scene/annotation/screen-anchor examples, and a bounded feasibility plan with actual unknowns. Name what can be tested on a controlled page versus what needs real-tool access. Make scientific review and timing dependency explicit. Keep backend/client ownership separate and compatible with a future FastAPI job boundary; do not implement routes in this investigation.

Now: load the files that are actually present, assess the three boundaries and choose a candidate scientific scene plus the highest-risk timing/live-anchor questions. Next, after the user selects/authorizes a bounded prototype: demonstrate editable scene + still/GIF, canvas annotation transforms and stale-cue cancellation, then validate real-tool access separately. Later: integrate trustworthy audio alignment, more templates and the full lab workflow.

Completion evidence for a future authorized prototype should include reproducible exports from the saved scene; correct anchors after resize/crop; pause/seek/rate consistency using actual timings; rejection of stale live targets; a source/domain review record; and clear manual/disconnected states. Do not credit a mock, fluent generated description or invented timing as proof.

**Exact next action for the other session:** fetch current main only after inspecting/preserving checkout state, verify the published files/evidence archive, load BB8/context and this handoff, then report the bounded graphics/annotation design and which feasibility trial should come first. No translation reruns, FastAPI scaffolding, deployment or additional commit/push are implied.

Copyable kickoff:

> @bb8 Continue Kikiland-ai/kiki-backend using docs/handoffs/graphics-and-annotation.md. Inspect branch/HEAD/status and preserve all work. Follow AGENTS.md and CONTEXT-BOOT.md; current source pin is 73d16c0d967a5d81dd74f1f28ef0defc48c8a778. Reuse the chosen translation/audio pipeline. Investigate direction 3 graphics plus teaching-canvas annotation and live-screen pointing as separate contracts. Give renderer/integration options, a small proposed scientific scene, timing/anchor risks and a bounded feasibility plan. Do not start the FastAPI backend, provider trials, extension/account actions, deployment or commit/push. If this local handoff or new speech/prompt files are absent, report the transfer gap rather than rebuilding them.
