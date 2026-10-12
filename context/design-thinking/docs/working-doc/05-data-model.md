# Data model

Oct 11, 2026 · @Arpan

The data model is subject-agnostic. One lesson pyramid holds a full chapter, a topic or a single concept, for any subject, built from a syllabus, a professor's notes or one typed question. Subject rules live in one place (the subject profile). Every input becomes a study request that is matched against existing content before anything is generated. Learner, practice and repair data all key to the same concept ids. Three worked ledgers in three subjects pass the validator and type-check: Electronics (a chapter), Chemical Engineering (a topic, from notes) and Mathematics (one question).

## Any subject, any scope

| Scope | Shape | Typical source | Worked example |
| --- | --- | --- | --- |
| Chapter | 2 to 5 broad concepts, each with 2 to 5 concepts | A syllabus or a class link | Diodes and rectifiers: 4 broad concepts, 12 concepts |
| Topic | 1 broad concept with 2 to 5 concepts | Notes, or a chapter name | Material balances on steady, non-reacting processes: 2 concepts |
| Concept | 1 broad concept with 1 concept | One question | Eigenvalues and eigenvectors of a 2 × 2 matrix |

The student never sees the scope as a difference: every scope plays through the same map, lesson player and practice. When the syllabus arrives, a concept-scope plan made from a question is folded into its chapter (`mergedIntoId`). Progress carries over because it is keyed by concept.

## The whole model

![data model · content, intake, learner](../diagrams/data-model.png)

Content is a pyramid with the concept at its centre. Intake turns anything a student sends into a request, matches it to existing concepts first, and only then generates a new or bigger plan. Every learner record (rings, attempts, marked answers, repairs, receipts) keys to the concept id, so a concept made from a question keeps its progress when it later joins a chapter.

## What changed from the diode-only version

| Diode-only assumption | Now |
| --- | --- |
| Branch is one of Electronics, Electrical, Chemical | `discipline` is free text, and `subjectProfileId` picks the rules. A new subject is a new profile, not new code |
| Odia is the only student language | A language policy: one source language, any number of support languages, each reviewed per concept |
| Every plan is a full chapter with a syllabus | Three scopes. A plan with no syllabus names the request that sets its boundary |
| The lab is a circuit simulator | A practical has a kind (simulation, physical lab, software, drawing, coding, field, calculation) with steps, observations, fault cards and viva prompts. Subjects with no practical work hide the green ring |
| Diagrams are electronics kinds; the explorable is diode-only | Open visual kinds with per-subject suggestions; six generic interactive kinds (parameter sweep, step through, label parts, sort steps, compare toggle, simulation) |
| Exam weight is typed by hand | The exam signal is computed from past questions mapped to concepts; its basis says real, estimated or none |
| Terms and prerequisites stay inside one chapter | Terms are unique across the course (borrowed terms are listed); prerequisites cross plans; school topics are bridge nodes |
| Source only at chapter level; no review state | A source on every explanation, visual, example, worked question and check; a review status (draft, auto-checked as "Kiki-made", teacher-checked, flagged) |
| No learner, practice or repair data | Learner, goals, route, concept state, attempts with diagnosis, practice sets, marked answers, repair plans, receipts, word stickers, practical runs, classes |

## Three worked ledgers

| Ledger | Subject | Scope | Came from | What it proves |
| --- | --- | --- | --- | --- |
| Diodes and rectifiers | Electronics | Chapter, 12 concepts | Curated (migrated from v1) | A simulation practical with three fault cards, two parameter sweeps, a bridge to a Class 12 topic |
| Material balances on steady, non-reacting processes | Chemical Engineering | Topic, 2 concepts | A professor's notes, with page-level sources | A physical lab, a sort-steps interactive, exam signal computed from two sample past papers |
| Eigenvalues and eigenvectors of a 2 × 2 matrix | Engineering Mathematics | Concept, 1 concept | One typed question in a self course | No practical (three rings), no syllabus (bounded by the request), a step-through interactive |

## How anything a student brings becomes lessons

1. **Request.** Any input (a question, notes, a syllabus, a past paper, an experiment sheet, a homework photo) becomes a `StudyRequest` with its pages.
2. **Match first.** Existing concepts are found by canonical key and meaning, so a question about ripple opens the existing concept instead of making a duplicate.
3. **Resolve.** Kiki picks one action: open existing, answer only, attach the material to existing concepts, extend a plan, or make a new plan at the right scope.
4. **Propose.** For anything new, the student sees an outline and confirms or edits it.
5. **Generate.** Outline, validate, draft, validate, localize. The first concept is ready in about a minute, while the rest finish.
6. **Label.** The content shows a "Kiki-made" label until a teacher checks it. A student's report flags it.
7. **Absorb.** Later uploads enrich or merge plans; learner state follows the concept ids.

## What every concept contains

Each concept is one node on the student's map and one lesson of 10 to 15 minutes. The course's source language (usually English) is the source of truth. Support-language text (Odia first) and the five dial levels are generated from it and reviewed before they ship. Which parts appear in a lesson depends only on what the concept has.

| Part | What it is | Shown as |
| --- | --- | --- |
| Explanation | A one-sentence key idea and a 60 to 140 word explanation | **Text + image** (always, with a visual brief of any kind: circuit, process flow, graph, equation, annotated notes), **voice** (a Kiki walkthrough of 3 to 8 steps, each tied to a word in the text), and optionally **video** (narrated slides, or a 20-second generated clip where motion matters), and optionally an interactive (parameter sweep, step through, label parts, sort steps, compare toggle or simulation) |
| Example | A concrete scenario and what it proves | A card after the explanation; real circuits and numbers where possible |
| Worked question | An exam-style question answered in full, line by line, with a rubric that adds up to its marks | The model answer the student learns to write; also the marking scheme for Snap your answer and practice sets |
| Check questions | At least 3 questions that test whether the concept is clear | Always a concept check (MCQ, numerical or diagram), a words check (term match) and an English check (short answer, spoken or written), plus a practical check when the concept has a practical. The mix comes from the subject profile |

Each concept also records its objectives, prerequisites, the terms it introduces, common misconceptions (these feed diagnosis and the lab fault cards), its exam signal (computed from past papers when there are any), its estimated minutes, where each part came from, and its review status.

## How MECE is enforced

Mutual exclusivity and exhaustiveness are checked by a script (`data-model/validate.js`), not by eye. Every edit to a ledger is validated before it ships.

| Rule | What it checks |
| --- | --- |
| Subject and course | The subject profile is embedded and matches the course; the language policy and dial labels are complete |
| Pyramid shape | The shape for the plan's scope (chapter, topic or concept); exactly one parent per concept; every split states its dimension and rationale |
| Mutually exclusive | Each objective is owned once; each term is introduced once across the whole course; no duplicate objectives, titles, canonical keys, terms or ids |
| Collectively exhaustive | The objective tree mirrors the pyramid; every syllabus line is covered, or the plan names the request that bounds it; out-of-scope topics are named |
| Complete concepts | A visual; a walkthrough whose targets are in the text; a valid interactive (its formulas are evaluated); an example; a worked question with a known type and a rubric that adds up; the subject's check mix; sources and a review status |
| Practicals | Linked both ways; steps, an expected result, fault cards and viva prompts; none in subjects without practical work |
| Learning order | Prerequisites exist and form no cycles; no term is used before the concept that introduces it is a prerequisite |
| Exam signal | Matches the past papers when there are any |
| Across ledgers | In one course: no term introduced twice, no dangling prerequisites or term uses, no duplicate concepts |

A test seeds 13 known errors, one per rule family, into copies of the three ledgers. The validator catches all 13 (`tools/test-validator.js`).

## Worked example: Diodes and rectifiers

![lesson pyramid · 1 lesson plan, 4 broad concepts, 12 concepts](../diagrams/lesson-pyramid.png)

Each split uses one stated dimension, so siblings never overlap. The chapter follows the AC-to-DC power supply: the diode, then rectify, filter, regulate. A linear supply is exactly these four stages, so nothing in the chapter is left out. Out of scope, named in the ledger: transistors, clippers and clampers, switched-mode supplies, and special diodes other than the Zener.

### The ledger at a glance

All 12 concepts of "Diodes and rectifiers". The full content (explanations, walkthrough scripts, worked answers, rubrics, every check question with its answer) is in `data-model/ledgers/electronics/diodes-and-rectifiers.json`. Past-paper weights are sample values to replace with real counts.

| ID | Concept | Explanation | Example | Worked question (marks) | Checks | Min | Past papers |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C-1.1 | PN junction and the depletion region | Voice (default), text + image, 18 s clip | Two crowded rooms with an open door | Explain the formation of the depletion region (5) | MCQ, term, MCQ, English | 12 | 2/5 |
| C-1.2 | Forward and reverse bias | Voice (default), text + image, 60 s slides | Reverse-polarity protection in a toy | Compare forward and reverse bias (5) | MCQ, term, English, spoken | 12 | 4/5 |
| C-1.3 | V-I characteristic and cut-in voltage | Voice (default), text + image, 70 s slides | Sweeping a 1N4007 in the lab | Draw and explain the V-I characteristic (5) | MCQ, term, diagram, English | 12 | 4/5 |
| C-1.4 | Diode models | Text + image (default), voice | 5 V and 1 kΩ: 5 mA, 4.3 mA or 4.22 mA by model | 12 V and 2.2 kΩ: ideal against constant drop (5) | Numerical, MCQ, term, English | 12 | 2/5 |
| C-2.1 | Half-wave rectifier | Voice (default), text + image, 20 s clip | The rectifier lab: Vm ≈ 17 V, Vdc ≈ 5.2 V | Explain the half-wave rectifier with waveforms (5) | MCQ, numerical, term, English, lab | 15 | 5/5 |
| C-2.2 | Centre-tap full-wave rectifier | Voice (default), text + image | Vm = 15 V gives 9.55 V at 100 Hz | Explain it and state the PIV (5) | MCQ, numerical, term, English | 15 | 5/5 |
| C-2.3 | Bridge rectifier | Voice (default), text + image | The input stage of a mains adapter | Compare centre-tap and bridge (5) | MCQ, numerical, term, English | 12 | 5/5 |
| C-2.4 | Rectifier figures of merit | Text + image (default), voice | Choosing a rectifier for a charger | Derive the ripple factor of a half-wave rectifier (5) | MCQ, numerical, term, written | 15 | 4/5 |
| C-3.1 | How a capacitor filter smooths | Voice (default), text + image, 20 s clip | A tank under a tap that runs in bursts | Why a capacitor filter, and how it smooths (5) | MCQ, term, English, lab | 12 | 3/5 |
| C-3.2 | Ripple voltage and choosing the capacitor | Text + image (default), voice | 100 mA through 1000 µF gives 1 V ripple | Size C for 200 mA and at most 1 V ripple (5) | Numerical, MCQ, term, English | 15 | 4/5 |
| C-4.1 | The Zener diode and breakdown | Voice (default), text + image | A 5.1 V reference | Zener against avalanche breakdown (5) | MCQ, MCQ, term, English | 12 | 3/5 |
| C-4.2 | The Zener voltage regulator | Text + image (default), voice | 12 V down to 5.1 V for a microcontroller | Design a 5.1 V, 20 mA regulator (5) | Numerical, MCQ, term, English | 15 | 2/5 |

The demo route's 9 stops map onto these concepts. The route's "Full-wave rectifier" stop covers C-2.2 and C-2.3, and its "Ripple factor" stop covers C-2.4 and C-3.2.

The new validator found four content issues in this ledger, now fixed in the migration:

- "Peak inverse voltage" was used by C-2.2 and C-2.3 before C-2.4 introduced it. It now belongs to C-2.2.
- "Reverse saturation current" was explained in C-1.2 but owned by C-1.3. It now belongs to C-1.2.
- C-2.3's worked answer needed "centre-tap transformer" without linking it.
- One 2-mark written check had no rubric.

## Files, storage and adding content

All files are in `data-model/` in the project folder:

- `types/content.ts`, `types/intake.ts`, `types/learner.ts`: the types for content (course to check question, practicals, exam profiles, past papers), intake (requests, source documents, outline proposals, generation jobs, smart links) and learners (state, attempts, practice, marking, repair, receipts, classes).
- `subject-profiles.json`: the subject rules (Electronics, Electrical, Chemical Engineering, Mathematics, and a generic profile).
- `ledgers/`: the three worked ledgers.
- `validate.js`: run `node validate.js ledgers` for every ledger plus the cross-ledger checks.
- `tools/test-validator.js` (the 13 seeded errors) and `tools/migrate-v1-to-v2.js`.
- `archive-v1/`: the original diode-only types, ledger and validator, unchanged.
- `README.md`: the same rules, for engineers.

**Storage:** Firestore.

- Content uses one collection per entity, keyed by id. A concept's explanation, example, worked question and checks sit inside the concept document.
- Generated text variants live in `variants/{entityId}:{field}:{lang}:{level}`.
- Intake uses `requests`, `sourceDocs`, `jobs` and `smartLinks`.
- Learner data sits under `learners/{id}/` (concept states, attempts, routes, practice sets, submissions, repair plans, receipts, stickers, practical runs).
- Classes keep only aggregates in `classPulse`.

**Adding a subject:** add one profile to `subject-profiles.json`, with the practical label and kinds, visual kinds, check mix, and whether units matter. No code changes.

**Adding a curated chapter or topic** (student uploads follow the pipeline above):

1. Write the governing question, choose the scope, pick one split dimension and name what is out of scope.
2. Split into broad concepts and concepts, with one objective per node and a canonical key per concept.
3. Map every syllabus line to concepts, or name the request that bounds the plan.
4. Have Gemini draft each concept in the ledger shape, from the student's notes first and curated sources second, with a source on every part.
5. Add past papers so exam signals are computed, not estimated.
6. Run the validator and fix every error. Have a teacher check the worked answers (review status: teacher-checked).
7. Generate the support-language text at each dial level, then get a native-speaker review.
