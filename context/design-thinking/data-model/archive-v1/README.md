# Lesson plan data model

Every chapter is a MECE pyramid: one **lesson plan** splits into 2 to 5 **broad concepts**, each of which splits into 2 to 5 **concepts**. A concept is one node on the student's map and one lesson of 10 to 15 minutes.

```
LP-DR  Diodes and rectifiers            (apex: governing question, can-do, O-0)
├─ BC-1  The PN junction diode           split by: level of description
│   ├─ C-1.1  PN junction and the depletion region
│   ├─ C-1.2  Forward and reverse bias
│   ├─ C-1.3  V-I characteristic and cut-in voltage
│   └─ C-1.4  Diode models
├─ BC-2  Rectification                   split by: circuit topology + shared measures
│   ├─ C-2.1  Half-wave rectifier
│   ├─ C-2.2  Centre-tap full-wave rectifier
│   ├─ C-2.3  Bridge rectifier
│   └─ C-2.4  Rectifier figures of merit
├─ BC-3  Filtering                       split by: how it works vs how much
│   ├─ C-3.1  How a capacitor filter smooths
│   └─ C-3.2  Ripple voltage and choosing the capacitor
└─ BC-4  Regulation                      split by: device vs circuit
    ├─ C-4.1  The Zener diode and breakdown
    └─ C-4.2  The Zener voltage regulator
```

The chapter splits along the AC-to-DC power-supply chain: the device, then rectify, filter, regulate. Each stage changes the signal in exactly one way, so every topic sits in one stage and none is missing.

## What every concept contains

| Part | What it is | Notes |
| --- | --- | --- |
| Explanation | `keyIdea` (one sentence) and `text` (60 to 140 words, English source of truth) | Three modalities from the same text: **text + image** (always, with a diagram brief), **voice** (a KikiWalkthrough script of 3 to 8 steps, each tied to a word in the text), and optionally **video** (narrated slides, or a short generated clip where motion matters) |
| Example | A concrete scenario and its takeaway | Real circuits and numbers where possible |
| Worked question | An exam-style question, answered in full, line by line, with a rubric that adds up to its marks | The model the student learns to write; also the marking scheme for Snap your answer |
| Checks | At least 3 questions that test whether the concept is clear | Must include a concept check (mcq, numerical or diagram), a words check (term_match) and an English check (short_english, spoken or long_written), plus a lab check when the concept has a lab |

Each concept also lists its objectives, prerequisites, the terms it introduces, common misconceptions (which feed diagnosis and the lab fault cards), its past-paper weight and its estimated minutes.

## How MECE is enforced

`validate.js` checks the ledger. Run it after every edit:

```
node validate.js diodes-and-rectifiers.ledger.json
```

| Rule | Checks |
| --- | --- |
| P1 to P4 | Pyramid shape: 2 to 5 children per node, exactly one parent per concept, every split states its dimension and rationale |
| ME1 | Every objective is owned by exactly one node |
| ME2 | Every technical term is introduced by exactly one concept |
| ME3, ME4 | No duplicate objective statements, concept titles or ids |
| CE1 | The objective tree mirrors the pyramid; every parent objective is covered by child objectives |
| CE2 | Every syllabus line maps to at least one concept |
| CE3 | Out-of-scope topics are named, so "exhaustive" has a boundary |
| C1 to C6 | Every concept has an explanation in the required modalities (walkthrough targets must exist in the text), an example, a worked question whose rubric adds up, the check mix, checks that test only its own objectives, and misconceptions |
| D1, D2 | Prerequisites exist and form no cycles |

I tested the validator by breaking a copy of the ledger in seven ways (a doubly owned objective, a doubly introduced term, an uncovered syllabus line, a missing words check, a walkthrough target not in the text, a rubric that doesn't add up, a prerequisite cycle). It reported all seven.

## Files

- `lesson-plan.types.ts`: the TypeScript types for every entity. Read this first.
- `diodes-and-rectifiers.ledger.json`: the complete worked ledger for the demo chapter: 1 lesson plan, 4 broad concepts, 12 concepts, 17 objectives, 35 terms, 12 worked questions, 49 check questions, 159 minutes.
- `validate.js`: the MECE and completeness validator (Node, no dependencies).

## Storing it (Firestore)

One collection per entity, keyed by id: `courses`, `lessonPlans`, `broadConcepts`, `concepts`, `objectives`, `terms`, `labs`. Keep each concept's explanation, example, worked question and checks inside the concept document; it stays well under Firestore's 1 MiB document limit. Learner state references `conceptId` and `objectiveId`, so mastery rings, the route and the repair map all read from the same ids.

## Adding a new chapter

1. Write the governing question and pick ONE split dimension for the chapter. Name what's out of scope.
2. Split into broad concepts, then concepts, writing one objective per node.
3. Map every syllabus line (from the uploaded syllabus, feature 7) to concepts.
4. Have Gemini draft each concept's explanation, example, worked question and checks as JSON in this shape, from the student's notes first (feature 19) and curated sources second.
5. Run `validate.js`, fix every error, then have a teacher check the worked answers.
6. Generate the five dial levels and the Odia text from the English, and have a native speaker review them before they ship (`language.status` goes from `to_generate` to `reviewed`).

The past-paper weights in this ledger are sample values. Replace them with real counts from the class's past papers.
