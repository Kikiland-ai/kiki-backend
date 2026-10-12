# Seven backend prototype directions for Kiki — revised

12 October 2026 · Proposal for the separate backend repo · Source checkout: `420f291`

The product needs a teaching medium as well as an adaptive learning backend: **source-grounded bilingual content, natural mixed-language speech, generated animated graphics, annotations synchronized with explanation, evidence-driven curation, diagnostic repair, and live lab guidance**. These seven directions are connected feature prototypes, with separate contracts for the systems underneath them. This revision supersedes the earlier proposal, which under-specified speech and graphics.

The two annotation uses are interpreted as **teaching on an image/diagram** and **guiding on a live software screen**. Uploaded notes and handwritten-answer feedback fit the first use. Both support drawing, shapes, labels, and writing; their anchors and lifecycles differ. This interpretation follows the user's correction and the existing lesson/lab journeys.

Start the learning demo with two or three diode concepts from the existing ledger. The current lab direction is MATLAB/Simulink Online; DSB-SC modulation/coherent demodulation is a proposed experiment with its own signals/communications prerequisites. It has not been selected or trialled. The backend and media engine described here are proposals, not implemented systems.

## 1. Grounded bilingual lesson compiler

**Product promise:** “Turn my class material into a lesson I can understand in Odia while learning the English terms.”

**Minimum viable prototype:** upload two pages of notes, extract page text, match existing concepts, confirm the outline, and compile one concept into definition, explanation, application, recap, an example, and practice tasks. Produce five student-selected language-support variants from the same canonical concept. Keep equations, units, facts, and canonical English terms stable. Every term stores English spelling, Odia-script pronunciation, and Odia meaning separately.

The output must be **renderable teaching content**, not one unstructured paragraph: stable block/span ids, term references, sources, an explanation script, visual teaching intent, and assessment objective references. This gives the speech and graphics engines something precise to consume. A visual intent identifies what the learner should notice, which quantities/relationships matter, and what motion would help; it is not yet a drawing program.

**First demo:** upload notes on reverse bias; see a page-linked concept lesson, equivalent Odia–English variants, and requests for narration and a depletion-region animation. Repeat the upload/question and reuse the same concept. Blurry pages enter a correction flow. Missing material is visibly supplied from reviewed content rather than attributed to the notes.

**Backend seed:** `intake`, `lesson-compiler`, and `localization` modules. Reuse `StudyRequest`, `SourceDoc`, `Resolution`, `GenerationJob`, `SourceRef`, `Concept`, `Term`, and `Localization`. Add `LessonPackage`, stable `ContentBlock`/`TextSpan` ids, `VisualIntent`, and versioned language variants. API starting points: `POST /study-requests`, `POST /study-requests/{id}/confirm`, `GET /lesson-packages/{id}`.

**Acceptance evidence:** reviewer checks page attribution, translation equivalence, preserved terms/formulas, and absence of unsupported claims. The ledger validator checks structural rules. Repeated requests preserve concept ids; attaching a syllabus later does not erase learner state. Content can become readable before its audio/animation jobs finish, with separate readiness shown.

**Bound the scope:** one PDF/photo path, one subject, Odia–English, and reviewed fixture content first. Student-selected language levels remain under student control. Existing Odia examples are placeholders requiring review.

## 2. Mixed-language text-to-speech and pronunciation bridge

**Product promise:** “Read the actual mixed-language explanation naturally, including the English technical terms.”

**Minimum viable prototype:** synthesize a short explanation containing Odia clauses, embedded English terminology, and one equation/value. Generate audio for two language-support levels first, then expand to all five. Keep visible spelling separate from spoken form: `0.7 V`, abbreviations, and symbols need reviewed spoken expansions without changing their on-screen representations. Term taps can request isolated English pronunciation and the Odia meaning.

Compile a `SpeechPlan` with ordered sentence ids, language spans, term references, spoken overrides, chosen voice, and pauses. Test coherent sentence-level multilingual synthesis first. If the available provider cannot handle the mix reliably, use sentence/phrase-level segments, preferably with a consistent voice; align loudness, pauses, and boundaries. Cutting at every English token can make speech unusably fragmented. A provider adapter may map pronunciation overrides to supported SSML/lexicon features or prepared spoken text; do not assume feature support.

Return audio plus **actual timing cues** for sentences and, where reliable, term spans. Use provider timestamps or a validated aligner. When word alignment is unreliable, use explicit sentence-level timing; do not fabricate word-accurate highlighting. Cache by text/glossary versions, voice/provider/model, language-support level, pronunciation overrides, and speech settings.

**First demo:** listen to one 30–45 second mixed explanation; English terms are recognisable, Odia clauses natural, and the spoken value correct. Tap a term to replay it. Change support level and switch at a sentence boundary, retaining progress. Listening remains optional; text and captions are always available.

**Backend seed:** a `speech` module with `SpeechPlan`, `AudioAsset`, `TimingCue`, and pronunciation lexicon. APIs: `POST /speech-jobs` and `GET /speech-jobs/{id}`. Store generated audio and timing manifests in object storage with job/readiness metadata in Firestore. Test available Gemini/Google speech options against the actual Odia–English samples before selecting one; this task has not verified a voice or provider capability.

**Acceptance evidence:** an Odia speaker checks intelligibility, code-switching, stress/pronunciation, values, and continuity. Measure first-play latency and timing drift. Cached audio remains valid only for the exact script version. Recorded fixture narration is a labelled prototype fallback if synthesis fails, not proof that the TTS engine works.

**Bound the scope:** one voice, one language pair, a small glossary, and sentence timing first. Student voice transcription/evaluation is a separate assessment capability. `VoiceScope` is a recording UI, not this TTS backend.

## 3. Graphics engine for animated explanatory diagrams and GIFs

**Product promise:** “Show the mechanism changing over time so I can see why the explanation is true.”

**Minimum viable prototype:** compile a reviewed visual intent into an editable scene using a small domain template library: diagram parts, connectors, arrows, axes, waveform curves, labels, highlight regions, and simple motion. Render a static poster plus an animated GIF where motion teaches the concept. Keep the semantic scene, parameters, phases, and object ids alongside exports.

Start with SVG/Canvas rendering from declarative geometry and bounded animation instructions. Gemini can propose a validated `GraphicsSpec`; deterministic rendering controls labels, equations, topology, and motion. Use model-generated illustration assets when useful, while retaining precise overlays/labels in the graphics engine. A generated raster image alone does not provide editable scientific objects or trustworthy geometry.

**First demo:** generate an 8–12 second forward/reverse-bias comparison: show depletion width changing, annotate terminals, and connect the change to a current/waveform view. Distinguish conventional current from electron motion if both appear. Replay or inspect individual teaching phases. Export the same scene as a GIF and a still image. Add a rectifier waveform template only after the first is reviewed.

**Backend seed:** a `graphics` compiler and render worker. Contracts: `GraphicsSpec`, `SceneObject`, `AnimationPhase`, and `RenderArtifact`. Store object ids, coordinate space/viewBox, units, scene version, source/objective refs, duration, and review status. APIs: `POST /graphics-jobs` and `GET /graphics-jobs/{id}`. Jobs validate a restricted drawing schema and approved formulas; arbitrary generated programs are not the rendering contract.

**Acceptance evidence:** domain reviewer checks polarity, connections, quantities, labels, arrow semantics, and temporal behaviour. Render repeatably from a saved spec, re-export after a parameter change, and ensure the scene is legible on a phone. Check render failures, Unicode/font layout, output size, and static/reduced-motion alternatives. A looping GIF should return cleanly to its start or disclose that it is a replay.

**Format decision:** GIF generation is an explicit deliverable. GIF contains no audio and offers poor seeking/pause control as a normal image element. Use the saved scene or a seekable video derivative for the synchronized lesson player, with GIF as a standalone/export format. Generate motion where it adds understanding; retain still diagrams for relationships that do not benefit from animation.

**Bound the scope:** two reviewed template scenes and a small primitive set. A universal graphics engine or arbitrary high-fidelity video generation can follow once these diagrams are scientifically and visually dependable.

## 4. Annotated teaching canvas: speech, writing, and graphics in sync

**Product promise:** “As Kiki explains, show me exactly which word, image region, or diagram part it means.”

This is **annotation use A: authored or captured content on a teaching canvas**. It covers generated diagrams, uploaded page images, and marked handwritten answers. Source media is immutable; annotations are separate editable layers that can be replayed, hidden, corrected, or exported.

**Minimum viable prototype:** compose one audio explanation with its captions, a generated scene or uploaded image, and a sequence of annotation operations: underline a phrase, circle a region, draw an arrow, reveal a box/shaded shape, write a label/equation, connect text to a diagram part, and move the companion pointer. Store geometry or a captured pen path for write-on animation. Preserve selectable text and accessible descriptions even when glyphs are animated. Support separate AI/teacher/student layers and undo for authoring or student marks.

**First demo:** a narrated diode lesson says “depletion region”; the relevant term highlights, the image region circles, an arrow appears, a label writes on, and the animation changes width at the corresponding teaching phase. Pause/replay one sentence and all tracks stay together. Run a second short demonstration on an uploaded notes image to prove annotations are not restricted to generated scenes.

**Backend seed:** a `lesson-composition` module returns `LessonTimeline` + versioned `AnnotationLayer`s. API: `POST /lesson-compositions`, `GET /lesson-compositions/{id}`, and an annotation-save endpoint. Each cue links sentence/term ids, an actual audio time range, an annotation operation, and a stable target. Timeline composition happens after audio duration is available; it can retime a scene phase or choose a reviewed narration pause without distorting the explanation.

Image targets use original asset pixel coordinates or an SVG viewBox, plus an explicit transform for crop, scale, rotation, and display placement. Text targets use localized span ids; scene targets use semantic object ids. Plain English phrase matching and unversioned display pixels are insufficient when text mixes languages or the image resizes. Caption and display spans can differ from spoken text and are mapped explicitly.

**Runtime contract:** the frontend owns playback and rendering; the backend compiles/stores assets and timelines. Use actual audio playback time as the master clock. Pausing, seeking, changing speed, or stepping back updates captions, shapes, pointer, and animation together. Language changes occur at a semantic sentence boundary; load that version's audio/timeline and cancel obsolete playback/cues. Existing fixed `stepMs` timers do not synchronize with speech.

**Acceptance evidence:** annotations stay on their intended targets after mobile resize/crop/zoom. Pause, seek, replay, playback-rate changes, and language switches have no stale audio or overlays. On a deliberately slow/failed media job, show readiness and permit text/still-image study. Caption-only and reduced-motion playback retain meaning. Test one uploaded page and one generated scene, not just a hard-coded demo diagram.

**Bound the scope:** six or seven annotation primitives, stable targets, and a short timeline. Shared drawing primitives with live guidance are useful; teaching-canvas anchors and live-screen anchors remain separate contracts. Do not flatten the only editable source into a GIF.

## 5. Evolving linguistic/domain learner graph and adaptive curation

**Product promise:** “Remember my particular gaps and choose the next explanation, exercise, or lab preparation that helps.”

**Minimum viable prototype:** a domain graph links concepts, prerequisites, objectives, terms, misconceptions, questions, and practicals. A learner overlay records criterion-level concept, vocabulary, English-expression, and practical evidence, plus support/hint history. A small rule-based curator selects one next action, eligible source content, language-support suggestion, and useful presentation: a term pronunciation clip, narrated diagram, plain text, targeted quiz, rewrite, or prerequisite lesson.

**First demo:** two learners encounter reverse bias. One demonstrates the idea but struggles with terms, so receives a pronunciation/usage drill and English rewrite. The other misunderstands depletion width, so receives the relevant animated explanation and prerequisite check. Their equivalent retries update only the evidenced dimensions and change the next recommendation.

**Backend seed:** `learner-evidence` owns append-only `LearningEvent`s and derived state; `learning-policy` reads that state and returns typed `LearningAction`s. Reuse `ConceptState`, `DimState`, `Goal`, `Route`, term links, misconception links, and stable concept ids. Extend with unassessed states, per-term/English-skill evidence, versions, and observation provenance. APIs: `GET /learners/me/graph` and `POST /learning/next-action`.

**Curation boundary:** assessment/lab workflows produce trusted evidence; curation selects a next activity and never assigns its own mastery score. Listening, watching a GIF, replaying an animation, or requesting Odia support is interaction telemetry, not proof of learning or failure. Use preferences/support needs to offer a format, avoiding claims about fixed visual/auditory “learning types.” The student controls language choice and can revise the route.

**Acceptance evidence:** replay events to rebuild the same projection; duplicate events do not count twice. Different evidence produces relevant different actions. Passing a theory check does not fill the practical/English dimensions. Generated content retains source/review labels and flagged material is excluded. Existing estimated exam weights stay labelled as estimates. New notes and plan merges preserve concept ids/history.

**Bound the scope:** Firestore documents/adjacency lists, explicit aggregation rules, and a small next-action policy. The four dimensions retain semantic keys; latest presentation mapping is green concept, red terms, yellow English, blue practical. A graph database and statistical proficiency model are later choices.

## 6. Diagnostic assessment, annotated exam repair, and retest

**Product promise:** “Separate what I understand from how I express it, show evidence on my answer, and help me improve.”

**Minimum viable prototype:** a reviewed five-question concept quiz, a ten-question chapter test blueprint, and an equivalent Odia/English open-answer task. Add one handwritten answer photo: extract/match the response, confirm uncertain transcription, evaluate concept/term/English rubrics, and produce an annotated repair plan plus equivalent retest. Typed answers provide an OCR-independent path for the first diagnostic trial.

**First demo:** contrast a scientifically correct Odia answer with weak English, a fluent but incorrect answer, and an unclear/unreadable answer. Return different supported recommendations rather than forcing a diagnosis for insufficient evidence. On the handwritten example, underline a term, box the relevant line, write a short correction beside it, and connect it to an English rewrite/repair task using prototype 4's image annotation layer.

**Backend seed:** `assessment` owns keys/rubrics/evaluations; `exam-practice` owns sets, submissions, and repairs. Reuse `Attempt`, `Diagnosis`, `EnglishRubric`, `Submission`, `MarkedAnswer`, `RepairPlan`, and `RepairItem`. Add quiz-level results, `insufficient_evidence`, rubric versions, actual page bboxes/source transforms, annotation references, and retest links. APIs: `POST /attempts`, `POST /practice-sets/{id}/submissions`, `POST /submissions/{id}/confirm-transcript`, and `GET /submissions/{id}/repair-plan`.

**Policy:** score MCQs deterministically; model-assisted open-answer evaluation returns criterion evidence/uncertainty. Keep **60% minimum for concept checks and 8/10 for the chapter test**, with explicit question coverage. MCQs cannot prove English writing/speaking fluency. Self-reported language confidence is not measured proficiency; unattempted questions do not automatically prove a concept gap. Grammar that does not block meaning does not reduce concept credit.

**Acceptance evidence:** compare contrasting answers with teacher/Odia-reviewer labels. Preserve concept evidence when English is weak. Each annotation points to the actual page/rubric evidence; uncertain OCR cannot silently become a mark deduction. Repairs update learning state only through retest evidence. Spoken answers can be added with transcript confirmation; speech-recognition mistakes alone cannot establish poor English/pronunciation.

**Bound the scope:** one photo/three answers first, then a small set. Display concept credit and English criteria separately; an exact “marks lost solely to English” claim requires a supported rubric/evidence basis, otherwise use a labelled estimate/range. `AnswerOverlay` currently renders a ruled-paper mock; it is not a finished arbitrary-image markup engine.

## 7. Live screen annotation, lab sessions, and Practical Copilot

**Product promise:** “Point out and explain the next action inside my actual software, while I perform it myself.”

This is **annotation use B: a temporary overlay on a changing software workspace**. Reuse the graphics primitives for arrows, circles, boxes, labels, pen strokes, and ghost demonstrations, but resolve targets against the latest observed workspace. An annotated screenshot can be saved as teaching/review material; its old coordinates cannot be reused as a live target after the workspace changes.

**Minimum viable prototype:** one experiment, five to ten known checkpoint states, a session tracker, a supported observation connection, and a client overlay on the real tool. Show a target/control, narrate its English name and Odia explanation, add a temporary arrow/shape/note, wait for the student's action, check evidence, and continue. Guided progress follows **predict → act → observe → explain → debug**.

**First demo:** prepare the proposed DSB-SC experiment on the phone and resume on a laptop. Locate the Product block, annotate a parameter field, guide a connection with a ghost path, explain the resulting waveform, and diagnose one receiver carrier mismatch. Stop guidance on disconnect/unknown workspace and resume only after revalidation. The student places blocks, edits values, wires, and runs the model; guidance never performs these operations.

**Architecture:** `lab-sessions` owns experiment prerequisites, checkpoints, observations, active device, connection status, and external project reference. A tool adapter returns workspace identity, capabilities, observations and fresh target anchors. The Practical Copilot selects bounded hints/steps from that evidence. The client overlay resolves geometry and renders timed drawing/speech; ordinary backend code cannot inject into another origin's application.

Define `ScreenObservation`, `ScreenAnchor`, and expiring `GuidanceCue`s with workspace/capture version, timestamp, coordinate-space metadata, target identity, confidence, and invalidation conditions. Map screenshot pixels to the actual viewport using capture dimensions, crop/zoom, scroll, and pixel ratio. Prefer semantic DOM/tool object anchors where accessible. Simulink may use canvas surfaces; do not assume DOM selectors cover its model objects. Re-observe/re-resolve after scroll, resize, modal opening, workspace change, or scene movement. If a target cannot be resolved, pause/request confirmation rather than retaining a plausible-looking old arrow.

Speech cues use prototype 2's pipeline; on target invalidation cancel related audio/highlights. Keep ordinary overlays pointer-transparent, placing pause/resume controls in the companion UI. Explain one step, then wait: lab cues are event/checkpoint-driven, not a continuous lesson timeline. Temporary ink must not obscure tool labels or imitate saved changes to the model.

**Activation policy:** experiment confirmed → required concept checks passed at 60% → correct model workspace opened → observation connection confirmed. Preparation is available anytime; the chapter's 80% test does not gate lab entry. States include preparing, ready, connecting, active, paused, disconnected, completed, and ended. Same-account handoff uses a single active-device lease/version; the session link identifies a session rather than granting private access. The Kiki session and external model save are separate.

**Backend seed:** `Practical`, `FaultCard`, and `PracticalRun` need required concepts, explicit checkpoint predicates/output tolerances, evidence provenance, tool capabilities, session revisions, and external model references. APIs: `POST /lab-sessions`, `POST /lab-sessions/{id}/observations`, `POST /lab-sessions/{id}/next-guidance`, and a handoff endpoint. `LabGuide`, `Spotlight`, and Kiki assets seed client visuals; they currently address their own demo DOM rather than real Simulink.

**First feasibility gate:** trial the model and baseline/fault/recovery outputs on the actual Simulink Online account. Test a supported tool API/export mechanism or consented browser extension for observations and overlay access. Account/licensing, canvas targeting, cross-origin/frame access, capture mapping, and overlay injection remain unverified. Start the overlay prototype on a small page you control to test geometry/invalidation, then prove the real tool connection. The controlled page alone cannot satisfy acceptance for live lab guidance.

**Acceptance evidence:** highlight a correct real target, track verified checkpoints, cancel stale cues, pause/reconnect, and persist phone/laptop evidence without conflicting writes. Distinguish structured observations, screenshot-reviewed evidence, and student reports. If the connection cannot be established, deliver a clearly labelled screenshot/manual companion guide alongside the simulator, not a connected live pointer. Hardware support later distinguishes preparation, student-reported work, and reviewed evidence.

## Annotation boundaries: one primitive library, two execution modes

| Concern | Teaching image/diagram | Live software screen |
| --- | --- | --- |
| Base | Versioned scene, notes image, answer photo | Current externally owned workspace |
| Anchor | Asset coordinates, semantic scene ids, localized text spans | Fresh tool/DOM anchor or mapped capture region |
| Shapes/writing | Persistent editable layers; optionally baked into an export | Temporary pointer-transparent overlay; saved separately if reviewed later |
| Timing | Audio-clock lesson timeline; pause/seek/replay | Live step/checkpoint state; cancel on observation invalidation |
| Geometry | Recompute display transform of a stable source | Re-observe/re-resolve when workspace changes |
| Wrong/missing target | Flag composition or offer original content | Pause guidance and request clarification/reconnection |
| Ownership | Student/teacher/AI layers with author/version | Observer/guide session with limited lifecycle |

Shared `AnnotationOp` primitives can include `highlight`, `underline`, `circle`, `arrow`, `box`, `path`, `text`, `equation`, `spotlight`, and `pointer`. Prototype only a small subset initially. Each operation has id, layer/author, semantic purpose/dimension, target, geometry/style, and visibility duration. Validate the target type against its execution mode. Neither drawing a shape nor generating a cue proves learning or lab completion.

## Shared backend and graphics runtime foundation

Start with one TypeScript API application and workers for extraction, model requests, audio synthesis, alignment, graphics rendering, and composition. Keep module boundaries inside that application; separate deployments are unnecessary for the prototype. The client owns audio playback, live scene/annotation rendering, geometry measurement, and the actual external-tool overlay adapter.

```text
contracts/                 # reconciled content, speech, scene, annotations, evidence, lab
modules/
  intake/  lesson-compiler/  localization/
  speech/  graphics/  lesson-composition/
  assessment/  exam-practice/
  learner-evidence/  learning-policy/  lab-sessions/
adapters/                  # model, TTS/alignment, storage, tool observation
workers/                   # durable generation and render stages
fixtures/                  # reviewed scripts, scenes, answers, captures
```

Use Firebase Auth for learner identity, Firestore for content versions/jobs/events/sessions, and object storage for originals, audio, graphics exports, and timing manifests. Authorize private source/capture access. Each generated media job records dependency versions, idempotency key, readiness, bounded retries, failure reason, and review status. Changing text, glossary, scene, or pronunciation invalidates dependent assets. Repeated requests reuse the same valid result; stalled jobs surface errors rather than silently completing.

Core proposed contracts:

```text
LessonPackage: concept/objective/source refs, stable blocks/spans, variants, media readiness
SpeechPlan: script/version, sentence/language/term spans, spoken overrides, voice
AudioAsset: storage ref, duration, timing cues, timing granularity, provider/version
GraphicsSpec: scene/version, semantic objects, coordinates, parameters, phases, sources
AnnotationLayer: source/version, author, operations, transforms
LessonTimeline: language version, audio ref, sentence/span-to-scene/annotation cues
LearningEvent: id, learner/task/concept refs, evaluated dimensions, evidence, support, versions
LabSession: experiment, prerequisites, checkpoints, device lease, connection, external project
ScreenObservation/ScreenAnchor: workspace/capture version, timestamp, geometry, confidence
```

Persist evidence events idempotently and derive learner state with an explicit versioned policy. All model outputs are runtime-validated data. Deterministic generation/render/evaluation workflows support two eventual agentic boundaries: the Learning Orchestrator and Practical Copilot.

## First integrated prototype and sequencing

The smallest integrated learning demonstration is **one source-backed concept → one mixed-language audio explanation → one generated GIF/scene → a synchronized annotated canvas → one diagnostic attempt → an evidence update → a different next activity**. This proves that media is part of the learning system rather than a disconnected export pipeline. An independent early lab spike proves the second annotation mode.

**Now:** build a reviewed fixture script and scene, compiler contracts, actual mixed-language TTS trial, and graphics/image-annotation prototype. Use fixture learner evidence to show curation. In the same early phase, test real-tool observation/overlay access to expose the lab feasibility risk.

**Next:** synchronize actual speech timing with the teaching canvas; connect diagnosis, learner graph, and adaptive curation; add handwritten-answer annotations/repair; expand the verified lab connection into the bounded experiment.

**Later:** more languages/voices, larger scene/template libraries, richer media, offline packs, new tools/hardware, expanded viva/interview practice, and aggregate teacher analytics. Speech, generated graphics, and both annotation modes are core directions now.

## Repo seeds, reconciliation, and what was actually checked

- [Current student journey](../ux/student-journey-odia-ece.md) governs language control, progression, lab entry, navigation, and colour mapping; [lab recommendation](../ux/experiment-recommendation-simulink.md) describes the pending experiment.
- [content.ts](../../data-model/types/content.ts), [intake.ts](../../data-model/types/intake.ts), [learner.ts](../../data-model/types/learner.ts), the existing ledger descriptions/excerpts, and [validator](../../data-model/validate.js) seed the contracts. `Visual.description`/`assetId` does not yet model a scene or timeline; `WalkStep` lacks audio timestamps and robust cross-language anchors.
- [KikiWalkthrough](../../design-system/project/components/KikiWalkthrough/README.md), [LabGuide](../../design-system/project/components/LabGuide/README.md), [Spotlight](../../design-system/project/components/Spotlight/README.md), [AnswerOverlay](../../design-system/project/components/AnswerOverlay/README.md), [VoiceScope](../../design-system/project/components/VoiceScope/README.md), and relevant sections of [bundle.js](../../design-system/project/components/bundle.js) were inspected for this revision.
- The current walkthrough changes steps on fixed `stepMs` timers; its term-pronunciation control calls browser speech with `en-IN`. It is not mixed-language TTS with timing. `VoiceScope` simulates audio in its preview. `LabGuide`/`Spotlight` address in-app demo targets. `AnswerOverlay` renders mocked ruled paper rather than a general image annotation layer.
- The current component/backend walkthrough shapes differ (`action` versus `mark`, localized lines versus source `say`), and old components use blue concept/green lab colours. Reconcile runtime contracts and latest semantic-colour mapping before porting. Add quiz-level policy, signed-in journey fields, unassessed learner states, speech timing, scene objects, image transforms, and live anchor invalidation.
- Relevant UX/feature/build/data-model documents, original vision/architecture DOCX text, transcript passages, and handover informed the prior review. This revision specifically inspected speech, walkthrough, graphics-related and overlay contracts/source. The private live documents, every component, and all original assets were not audited.

BB8, product-strategy, and engineering-architecture remain local reference guidance. No TTS provider, graphics renderer, synchronized player, or real Simulink integration was executed in this direction-redrafting task. Reviewer and student trials are still needed to establish intelligibility, scientific fidelity, and learning impact.
