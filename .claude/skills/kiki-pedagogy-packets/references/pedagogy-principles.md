# Pedagogy principles → packet rules

Each principle is stated with its evidence, a confidence label for Kiki's use, and the
concrete rule it imposes on packets. Confidence describes how well the evidence transfers to
*Kiki's setting* (self-paced, mobile, bilingual Odia–English, engineering undergraduates), not
the strength of the original lab finding. Sources were checked on 2026-11-20; numbers below
are as reported by the cited source.

## 1. Design backwards from evidence of learning

- **Evidence.** Constructive alignment (Biggs, 1996, *Higher Education* 32(3)) and backward
  design (Wiggins & McTighe, *Understanding by Design*, 1998/2005): outcomes first, then the
  assessment that would evidence them, then the activities.
  Summary: <https://itali.uq.edu.au/teaching-guidance/principles-learning/guiding-theories-and-frameworks/teaching-frameworks-and-models>
- **Confidence:** moderate (design framework; strong consensus, limited causal trials).
- **Rules.** Objectives before placards. One measurable verb per objective with a Bloom level.
  Every check's `objectiveIds` ⊆ the concept's own objectives (ledger rule C5). If an
  objective has no check, delete it or add the check.

## 2. Small steps, managed cognitive load

- **Evidence.** Rosenshine, "Principles of Instruction", *American Educator* 36(1), 2012:
  present new material in small steps, check understanding, high success rate, scaffold
  hard tasks (note its thin citation base, critiqued by Bokhove 2024 in TES). Mayer's segmenting and pre-training principles: learner-paced
  segments and naming key components first help (Mayer 2021 / *Cambridge Handbook of Multimedia
  Learning*; summary <https://www.unh.edu/teaching-learning-resource-hub/sites/default/files/media/2023-06/itow-research-based-principles-for-designing-multimedia-instruction-mayer.pdf>).
- **Confidence:** high for the direction; per-principle effect sizes vary.
- **Rules.**
  - Four placards, learner-paced: **definition** acts as pre-training (names and symbols), then
    **concept** (mechanism), **application** (use it), **recap** (retrieve-ready summary).
  - Prerequisite terms are introduced in their owning concept, never first used cold (D3).
  - Split a concept when the concept placard needs more than ~6 sentences or more than about
    four new interacting elements (symbols, conditions, relationships) at once.

## 3. Words + pictures, spoken narration, no clutter

- **Evidence.** Mayer's principles (via the summary above): coherence (cut extraneous material;
  reported 18/19 tests, median d≈0.86), signalling (cue essentials; 26/28, d≈0.70), modality
  (narrated graphics over on-screen text; 53/61, d≈0.76); redundancy is weak (d≈0.10) and has
  exceptions for short on-screen text. Replication outside the lab is uneven.
- **Confidence:** moderate–high (strong lab base; transfer to phone lessons plausible).
- **Rules.**
  - Every concept has a static `visual` brief. Narration (placard audio) describes the visual
    rather than reading a different text.
  - No decorative facts, history or trivia unless an objective needs them (coherence).
  - Walkthrough steps signal one phrase each; `say` explains *that* phrase (signalling). Do not
    reuse unrelated sentences as narration.
  - Visible formulas stay short; the spoken form is a separate literal expansion.

## 4. Worked examples first, fading with expertise

- **Evidence.** Worked-example effect and the expertise reversal effect (Kalyuga, Ayres,
  Chandler & Sweller 2003, *Educational Psychologist* 38:23–31): worked examples help novices
  and can hurt more experienced learners.
- **Confidence:** high.
- **Rules.** Every concept has a fully worked question with line-by-line model answer and a
  concept-only rubric that sums to `marks` (C3). The application placard shows the reasoning
  path, not just the answer. Checks progress difficulty 1 → 3 so later items are less
  scaffolded than the worked example.

## 5. Concrete first, then abstract

- **Evidence.** Concreteness fading (Fyfe, McNeil, Son & Goldstone 2014, *Educational
  Psychology Review* 26:9–25): concrete → bridging → abstract sequences beat either alone for
  transfer; later work asks for clearer definitions.
- **Confidence:** moderate.
- **Rules.** The concept placard grounds each symbol in a physical or observable meaning before
  the general formula ("the envelope is the outline traced by the peaks"). Canvas widgets let
  the student vary a concrete quantity and watch the abstract readout change.

## 6. Confront misconceptions explicitly

- **Evidence.** Refutation texts (state the misconception, refute it, explain the correct idea)
  beat plain exposition: Tippett 2010 review (*Int. J. Sci. Math. Educ.*); Schroeder & Kucera
  2022 meta-analysis, g = 0.41 over 44 comparisons
  (<https://link.springer.com/article/10.1007/s10648-021-09656-z>); Danielson et al. 2024
  (*Educational Psychologist*), consistent advantage. Threshold concepts are troublesome,
  counter-intuitive and integrative (Meyer & Land 2003). Engineering concept inventories (for
  example the Signals and Systems Concept Inventory) are the best place to find documented ones.
- **Confidence:** high for refutation; moderate for which misconceptions apply to Kiki students.
- **Rules.**
  - At least one misconception per concept, each tagged `basis: documented` (with a source) or
    `basis: inferred` (explained). Do not present inferred misconceptions as documented.
  - The concept placard contains at least one refutation sentence linked by
    `refutesMisconceptionIds` ("This rule applies to conventional AM; it does not apply to
    DSB-SC because…").
  - Distractors come from misconceptions (see §8). A canvas should make the misconception
    visibly fail when one exists.

## 7. Retrieval practice with explanatory feedback, spaced

- **Evidence.** Dunlosky et al. 2013 (*Psychological Science in the Public Interest*
  14(1):4–58; <https://scholars.duke.edu/publication/954654>) rated practice testing and
  distributed practice high utility; rereading and highlighting low. Explanation feedback beats
  correct-answer feedback for transfer (Butler, Godbole & Marsh 2013). Prompted
  self-explanation helps (Bisra et al. 2018 meta-analysis, 64 studies, *Educ. Psychol. Rev.*
  30:703–725). Active learning raises STEM exam and concept-inventory scores by about 0.47 SD
  (Freeman et al. 2014, *PNAS* 111:8410; <https://pmc.ncbi.nlm.nih.gov/articles/PMC4060654/>).
- **Confidence:** high.
- **Rules.**
  - Each concept: 5 concept-dimension MCQs (journey: 3/5 = 60% to pass), equivalent enough that
    a retry can draw unseen ones. Plus words, English and (if practical) lab checks.
  - Every `explanation` says *why* the answer is right **and** why the most tempting distractor
    is wrong. Never just restate the answer.
  - The recap placard is written as retrievable statements (rules, conditions, one formula),
    not as "in this lesson we learned".
  - Include one self-explanation prompt per concept (`teaching.selfExplainPrompt`), usually a
    "why does…" question answered in the English check.
  - Chapter test items must be new items, not copies of concept MCQs.

## 8. Write MCQs that measure, not trick

- **Evidence.** Haladyna, Downing & Rodriguez 2002 (31 item-writing guidelines, *Applied
  Measurement in Education*); Rodriguez 2005 meta-analysis: three options are usually
  optimal, because plausible distractors are scarce.
- **Confidence:** high for guidelines; the Kiki UI and ledger currently use 4 options.
- **Rules.** 3 or 4 options, default 4 to match the existing ledger; drop to 3 rather than
  pad with an implausible option. Every distractor has a `distractorRationale` pointing to a
  misconception id or a named error (sign error, wrong formula, unit slip). No joke options, no
  "all/none of the above", no longest-is-correct, no negative stems unless the negation is
  bolded in the stem itself. Vary the position of the correct answer.

## 9. Learn in the familiar language, keep exam English

- **Evidence.** For Indian engineering education the evidence is thin. Policy (NEP 2020, AICTE
  regional-language courses) pushes mother-tongue instruction. Small studies found no
  comprehension loss from Tamil–English code-switching in CS teaching, and commentators favour
  "mother tongue plus English". AICTE translations keep English technical names
  (<https://drishtiias.com/pdf/1630068445.pdf>). No strong causal trial was found for this
  population.
- **Confidence:** low–moderate. Treat it as a product decision (already confirmed in the
  journey), not settled science.
- **Rules.** English technical terms stay in Latin script at every proficiency level (protected
  glossary terms). Each term has an English definition, a draft Odia meaning and a draft Odia-script
  pronunciation, all `pending` review. The source English is plain and short so the Odia-led
  translation stays faithful. English academic writing is assessed separately and never
  costs concept marks.

## 10. Multiple representations, one model

- **Rule.** The placard text, the visual brief, the canvas behaviour and the checks must
  describe **the same model with the same symbols, units and assumptions**. If the canvas uses
  a normalised amplitude, the text says so. If the text says "ideal", the canvas assumptions
  say "ideal".

## What not to do (evidence-informed)

- Do not use learning-styles matching; modality choice follows content, not student "style"
  (Pashler et al. 2008, *Psychological Science in the Public Interest*, found no adequate
  evidence for the meshing hypothesis; not re-verified in this session).
- Do not pad lessons with motivational filler or rereading summaries.
- Do not treat MCQ correctness as evidence of English or practical skill (journey rule).
