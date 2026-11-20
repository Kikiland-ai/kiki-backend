---
name: kiki-pedagogy-packets
description: Research a chapter, topic or single concept in depth and author evidence-backed, pedagogically designed Kiki learning packets (English source of truth) that the backend can feed straight into the mixed-language translation, speech and concept-canvas pipelines. Use when asked to "make packets", "research and teach" a chapter/topic/concept, build placards, concept checks, chapter tests, glossaries or canvas widget specs for Kiki. Do not use to translate, synthesize audio, render canvases or publish media; those are downstream pipeline stages.
---

# Kiki pedagogy packets

Turn a chapter, topic or concept into **digestible, validated packets**: one `kiki-chapter-plan/v1`
per request and one `kiki-pedagogy-packet/v1` per concept. Each packet is the English source
of truth for a concept: researched claims, learner model, objectives, four placards, glossary,
checks, worked question, a static visual brief and (when it earns its place) a canvas widget spec.

The packet is the step that used to be hand-authored. Downstream it must survive, without
editing:

- `prototypes/mixed_script/pipeline.py` `validate_input` (each placard projects to one
  `mixed-script-input/v1`), then Odia translation → mixed refinement → speech text → Gemini TTS.
- The concept-canvas factory (trusted analytic models with ≤3 controls, behaviour cases,
  `claim: ideal_teaching_model`).
- kiki-web `lesson-ledger/v2` assembly and `data-model/validate.js` (the `teaching` block
  uses ledger field names on purpose).

## Read before working

1. [Pedagogy principles](references/pedagogy-principles.md): the evidence and the rules it implies. Always.
2. [Research protocol](references/research-protocol.md): how to go deep and keep a claim ledger. Always.
3. [Packet contract](references/packet-contract.md): exact output shape and downstream mapping. Always.
4. [Authoring rules](references/authoring-rules.md): placard sentences, glossary, literals, MCQs, canvas widgets.
5. [Quality gates](references/quality-gates.md): the review pass and known anti-patterns.
6. [Worked example](templates/C-AM-03.packet.json): a complete packet that passes the checker.

## Workflow

Do the phases in order. Do not write placards before the learner model and objectives exist.

1. **Intake and boundary.** Establish scope (`chapter` | `topic` | `concept`), the subject,
   what the student supplied (syllabus, slides, notes, past papers, experiment sheet) and
   any existing concept ids / `canonicalKey`s to reuse instead of duplicating. Ask only
   for what changes the output: missing scope boundary, conflicting materials, or whether a
   lab/practical is in play. Default otherwise and say what you defaulted.
2. **Research deep** (research protocol). Build the source list and claim ledger first.
   Student material sets the boundary and notation; authoritative sources verify and fill gaps.
   Recompute every number. Record out-of-scope items and open questions.
3. **Map the chapter** (chapter/topic scope). MECE split into broad concepts → concepts,
   prerequisite DAG, route order, external prerequisites, chapter-test blueprint. Write
   `kiki-chapter-plan/v1`. Generate concepts in route order.
4. **Model the learner** per concept: prerequisites, documented or inferred misconceptions,
   what is troublesome or threshold-like, and element interactivity (how many ideas must be held
   at once). If the concept cannot be taught in four placards without overload, split it.
5. **Design backwards**: objectives (one measurable verb, Bloom level) → evidence (checks that
   would prove each objective) → instruction (placards, example, worked question, visual,
   canvas). Every check maps to an owned objective. Every distractor maps to a misconception
   or a named plausible error.
6. **Write the four placards** (definition → concept → application → recap) as short,
   self-contained, translation-ready English sentences with stable ids, glossary term ids and
   protected literals with spoken forms.
7. **Specify the canvas** only when manipulating a variable reveals the key relationship or
   breaks a misconception. Otherwise set `canvas: null` with a reason and rely on the visual.
8. **Assess**: 5 concept MCQs (pass is 3/5 = 60%), plus a words check, an English check and
   (when a practical exists) a lab/predict check; worked question with a rubric that sums.
9. **Check**: run the checker, fix every error, review warnings with the quality gates, then
   report.

```sh
python -X utf8 -B .claude/skills/kiki-pedagogy-packets/scripts/check_packet.py <packet-or-plan.json>... [--emit-mixed-inputs <dir>]
```

The checker verifies structure, pedagogy lints, canvas behaviour cases (by evaluating the
declared formulas) and runs the backend's real `validate_input` on every placard projection.
`--emit-mixed-inputs` writes the `mixed-script-input/v1` files a runner would submit.

## Output and report

Write packets to the location the user names, else `work/pedagogy-packets/<lessonPlanId>/`
(`chapter-plan.json`, `<conceptId>.packet.json`). Report: scope and sources actually used,
concepts produced, checker result (actual output), unresolved claims, inferred (not documented)
misconceptions, and what still needs instructor / native-Odia / pronunciation review.

## Boundaries

- English is the source of truth. Odia glosses and pronunciations are **drafts** required by
  the pipeline glossary; always `review_status: pending`. Never mark review complete.
- Never invent sources, page locators, syllabus lines, past-paper weights (`examSignal.basis:
  none` unless real papers exist), measurements, or teacher review.
- Canvas specs describe ideal teaching models in declarative math; never emit executable code.
- Do not translate, call TTS, render, publish or write to Firestore. The runner owns that.
- Mark idealisations and conditions in the text itself ("in an ideal linear model…").
