# Research protocol: going deep on a concept

The goal is not a long survey. It is a **claim ledger** complete enough that every placard
sentence, check answer and canvas behaviour traces to a verified claim.

## 1. Decompose the topic into research branches

For each concept, answer these questions (skip any that do not apply, and say which):

| Branch | Question | Feeds |
|---|---|---|
| Definition | What exactly is it? In what notation and units does *this course* write it? | definition placard, terms |
| Purpose | Why does it exist and what problem does it solve? | hook (`canDo`), concept placard opening |
| Mechanism | How does it work, step by step? What causes what? | concept placard, walkthrough |
| Mathematics | Governing relations, derivation sketch, valid ranges, limiting cases | literals, canvas model, worked question |
| Conditions | Assumptions, idealisations, where it stops holding | refutation sentences, canvas `assumptions` |
| Contrasts | Nearest neighbouring concepts that students confuse it with | misconceptions, distractors |
| Misconceptions | Documented student errors (concept inventories, education research, instructor notes) | misconceptions, distractors, canvas purpose |
| Application | Where it is used: a lab, a device, a design decision, an exam question type | application placard, example, practical link |
| Assessment | How exams and vivas ask it (past papers if supplied) | worked question, checks, `examSignal` |

## 2. Source order (claim-specific authority)

1. **The student's own material** (syllabus, slides, notes, experiment sheet, past papers). It
   sets scope, notation and emphasis. Cite with `origin` + `locator` ("slide 14").
2. **Standard references**: university textbooks, course notes from established engineering
   departments (open courseware), standards bodies.
3. **Official tool and vendor documentation** (MathWorks, device datasheets, application notes),
   authoritative for tool behaviour, block parameters and device specifications.
4. **Education research** (concept inventories, misconception studies), authoritative for
   what students get wrong.
5. **Encyclopaedias, tutorials, forums**: leads only, never the sole source of a claim.

Search-result snippets are not reviewed sources. Open the page you cite. If a source cannot be
opened, it cannot be cited. Record it in `research.openQuestions` instead.

## 3. Claim ledger

Every material statement becomes a claim:

```json
{"id": "CL-03-4", "kind": "condition", "text": "For 0 <= mu <= 1 the conventional AM envelope never crosses zero.",
 "sourceIds": ["S-2"], "confidence": "high", "check": "derived: envelope = Ac(1+mu cos) >= Ac(1-mu) >= 0"}
```

- `kind`: `definition` | `fact` | `relation` | `condition` | `idealisation` | `procedure` |
  `convention` | `misconception_evidence`.
- `confidence`: `high` (two independent sources or a source plus derivation), `moderate` (one
  authoritative source), `low` (indirect). **Low-confidence claims may not appear in placards
  or answer keys.** Resolve them or move them to `openQuestions`.
- `check`: how you verified it (derivation, recomputation, second source). Recompute every
  numeric example and worked answer. Write the arithmetic in `check`.
- Notation conflicts (for example `m` vs `mu`, `Ka` vs `ka`) are a `convention` claim. Use the
  student's material's notation, else the dominant textbook convention, and say so.

## 4. Contradictions

Before calling two sources contradictory, check definitions (peak vs RMS, one-sided vs
two-sided spectrum), normalisation, units, and idealised vs practical models. Most conflicts are
apparent. Record real conflicts in `openQuestions` and teach only what both sources agree on,
or state the condition that separates them.

## 5. Misconception mining

1. Search for a concept inventory or misconception study for the topic (search terms:
   "<topic> misconceptions", "<topic> concept inventory", "students' difficulties with <topic>").
2. List near-neighbour confusions from the Contrasts branch.
3. Add predictable formula slips (sign, factor of 2, rad vs Hz, peak vs peak-to-peak).
4. Tag each one `documented` (with a source) or `inferred` (with your reasoning). Two or three
   strong misconceptions beat a long weak list.

## 6. Stopping rule

Stop when every branch that applies has high/moderate claims for what the placards, checks
and canvas need, and more searching would not change the content. Do not research beyond the
concept boundary. Name exclusions in `research.outOfScope`.

## 7. Chapter mapping (chapter and topic scope)

- Split the chapter on **one stated dimension** per level (ledger P4 `mece`) with a rationale
  and named exclusions. Chapter: 2–5 broad concepts; topic: 1 broad concept; each broad concept
  2–5 concepts.
- Each concept is one teachable idea (about 8–15 minutes) with its own objective(s).
- Prerequisites form a DAG. A concept never uses a term before its owning concept is a
  prerequisite (ledger D3). School-level needs become `externalPrerequisites`.
- When a practical exists, list its required concepts and confirm the route includes all of
  their prerequisites.
- Chapter test blueprint: 10 MCQs; with ≤10 concepts, at least one per concept, the rest on
  key applications and relationships; >10 concepts, prioritise core ideas and use
  cross-concept items.
