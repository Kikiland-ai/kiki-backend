# Pedagogy principles → packet rules

Each principle gives its evidence, a confidence label for KiKi's use, and the rule it imposes
on packets. Confidence describes how well the evidence transfers to *KiKi's setting* (self-paced,
mobile, multilingual, for students and knowledge workers in onboarding or role transitions). It
does not describe the strength of the original finding. Sources were checked on 2026-11-20, and
numbers are as reported by the cited source. Sections 1–8 apply in every corner. Sections 9–12
matter most for workplace learning and for the odds and audiences corners.

## 1. Design backwards from evidence of learning

- **Evidence.** Constructive alignment (Biggs 1996, *Higher Education* 32(3)) and backward design
  (Wiggins & McTighe, *Understanding by Design*, 1998/2005): outcomes first, then the assessment
  that evidences them, then the activities.
  Summary: <https://itali.uq.edu.au/teaching-guidance/principles-learning/guiding-theories-and-frameworks/teaching-frameworks-and-models>
- **Confidence:** moderate (a design framework with strong consensus and limited causal trials).
- **Rules.**
  - Write the objectives before the placards. Each objective has one measurable verb and a Bloom level.
  - Every check's `objectiveIds` ⊆ the concept's own objectives.
  - If an objective has no check, delete the objective or add the check.
  - For workplace domains, phrase objectives as job performance: "Write a pre-trade note that…",
    "Restructure a run-of-show so that…".

## 2. Small steps, managed cognitive load

- **Evidence.** Rosenshine, "Principles of Instruction", *American Educator* 36(1), 2012: small
  steps, check understanding, high success rate, scaffold hard tasks (note its thin citation
  base, critiqued by Bokhove 2024 in TES). Mayer's segmenting and pre-training principles: learner-paced
  segments, and naming key components first, both help (Mayer 2021; summary
  <https://www.unh.edu/teaching-learning-resource-hub/sites/default/files/media/2023-06/itow-research-based-principles-for-designing-multimedia-instruction-mayer.pdf>).
- **Confidence:** high for the direction; effect sizes vary by principle.
- **Rules.**
  - Use 1–6 learner-paced placards. The default arc is **definition** (pre-training: names,
    symbols, the trade's words), then **concept** (the mechanism or the rule and its reason),
    an optional **example** (one concrete case), **application** (use it) and **recap**
    (retrieval-ready rules).
  - Introduce a term in its owning concept before using it elsewhere.
  - Split the concept when the core placard needs more than about 6 sentences or about four new
    interacting elements at once.

## 3. Words + pictures, spoken narration, no clutter

- **Evidence.** Mayer's principles (summary above): coherence (cut extraneous material;
  reported 18/19 tests, median d≈0.86), signalling (26/28, d≈0.70), modality (narrated graphics;
  53/61, d≈0.76). Redundancy is weak (d≈0.10) and has exceptions for short on-screen text.
  Real-world replication is uneven.
- **Confidence:** moderate–high.
- **Rules.**
  - Every concept has a `visual` brief. Narration describes what the canvas shows.
  - Use `cue`s so the canvas moves in step with the sentence being spoken.
  - Cut decorative facts, history and motivational filler.
  - Each walkthrough step signals one phrase, and its `say` explains that phrase.

## 4. Worked examples first, fading with expertise

- **Evidence.** Worked-example effect and the expertise reversal effect (Kalyuga, Ayres, Chandler &
  Sweller 2003, *Educational Psychologist* 38:23–31): worked examples help novices and can hurt
  experienced learners.
- **Confidence:** high.
- **Rules.**
  - Every concept has a fully worked question with a concept-only rubric.
  - The application or example placard shows the reasoning path.
  - Check difficulty rises from 1 to 3. For experienced professionals (`learner.priorKnowledge`),
    shorten the worked example and move sooner to problems.

## 5. Concrete first, then abstract

- **Evidence.** Concreteness fading (Fyfe, McNeil, Son & Goldstone 2014, *Educational Psychology
  Review* 26:9–25).
- **Confidence:** moderate.
- **Rules.**
  - Ground each symbol, rule or metric in something observable before generalising it ("the
    envelope is the outline through the peaks"; "the retention curve is how many viewers are still
    watching at each minute").
  - In workplace domains, the concrete anchor is a real case from the organisation's own work.

## 6. Confront misconceptions explicitly

- **Evidence.**
  - Refutation texts beat plain exposition: Tippett 2010 review; Schroeder & Kucera 2022
    meta-analysis, g = 0.41 over 44 comparisons
    (<https://link.springer.com/article/10.1007/s10648-021-09656-z>); Danielson et al. 2024.
  - Threshold concepts are troublesome and counter-intuitive (Meyer & Land 2003).
- **Confidence:** high for refutation; moderate for which misconceptions a given audience holds.
- **Rules.**
  - At least one misconception per concept, tagged `documented` (with a source) or `inferred`
    (with reasoning).
  - At least one sentence carries `refutesMisconceptionIds`.
  - Distractors and tutor-graph `misconceptions` come from this list.

## 7. Retrieval practice with explanatory feedback

- **Evidence.**
  - Dunlosky et al. 2013 (*Psychological Science in the Public Interest* 14(1):4–58;
    <https://scholars.duke.edu/publication/954654>): practice testing and distributed practice
    have high utility; rereading has low utility.
  - Explanation feedback beats correct-answer feedback for transfer (Butler, Godbole & Marsh 2013).
  - Prompted self-explanation helps (Bisra et al. 2018, 64 studies).
  - Active learning raises STEM exam and concept-inventory scores by about 0.47 SD (Freeman et al.
    2014, *PNAS*; <https://pmc.ncbi.nlm.nih.gov/articles/PMC4060654/>).
- **Confidence:** high.
- **Rules.**
  - Concept checks follow `assessmentPolicy`, so retries can draw unseen equivalents.
  - Every `explanation` says why the answer is right **and** why the tempting option is wrong.
  - Write the recap as retrievable rules.
  - Include one self-explanation prompt per concept.

## 8. Write items that measure, not trick

- **Evidence.** Haladyna, Downing & Rodriguez 2002 (31 guidelines); Rodriguez 2005 meta-analysis:
  three options are usually optimal.
- **Confidence:** high.
- **Rules.**
  - Use `assessmentPolicy.options` (3 or 4). Drop to 3 rather than pad.
  - Every distractor has a rationale.
  - No joke options, and no all/none of the above.
  - Vary the position of the correct answer.

## 9. Learn in the language you think in; express in the working language

- **Evidence.** Thin for any single population.
  - For Indian higher education: NEP 2020 and AICTE regional-language courses; small studies show
    no comprehension loss from code-switching; commentators favour "mother tongue plus English";
    AICTE translations keep English technical names
    (<https://drishtiias.com/pdf/1630068445.pdf>).
  - For knowledge workers, KiKi's premise (performance lost to the working language and jargon,
    not to ability) is a **product hypothesis** (Design-Thinking 01, §1). It has not been tested.
- **Confidence:** low–moderate. Treat it as a product decision.
- **Rules.**
  - Canonical terms, numbers, units and tool labels keep their form in every target language.
  - Every target language has draft glosses and pronunciations, labelled "machine draft" until a
    native speaker reviews them.
  - Assess expression in the `workingLanguage` separately; it never costs concept credit.
  - Write the source sentences plain and short so translation stays faithful.

## 10. Train for transfer to the job

- **Evidence.** Transfer of training meta-analysis (Blume, Ford, Baldwin & Huang 2010, *Journal of
  Management* 36(4):1065–1105; <https://doi.org/10.1177/0149206309352880>): 89 studies relating
  trainee characteristics, the work environment and training design to transfer. Baldwin & Ford
  1988 is the standard model.
- **Confidence:** moderate (this is the field's synthesis; effect sizes not re-checked here).
- **Rules.**
  - Teach with the organisation's own cases, tools and vocabulary.
  - Practice checks use the real tool, in paper mode or as a replay where stakes are high.
  - The application placard ends in a job action ("write this in your note", "send this plan
    by 18:00"), not a quiz-only fact.

## 11. Separate decision quality from outcome (odds corner)

- **Evidence.** Outcome bias: people rate the same decision as better when the outcome was
  good, even when they say outcomes should not matter (Baron & Hershey 1988, *JPSP* 54(4):569–579;
  <https://bear.warrington.ufl.edu/brenner/mar7588/Papers/baron-hershey-jpsp1988.pdf>). A 2023
  preregistered replication found the effect again (Aiyer et al., *International Review of Social Psychology*).
- **Confidence:** high that the bias exists; moderate that teaching against it changes behaviour.
- **Rules.**
  - In odds domains, list outcome bias as a misconception unless the scope truly excludes it.
  - Checks ask about the process (what was knowable, which rule held or broke), never "was it a
    good trade?" judged by its profit or loss.
  - Teach the process × outcome quadrant when the organisation uses one.

## 12. Compare contrasting cases (audiences and odds corners)

- **Evidence.** Analysing contrasting cases prepares learners for explanation, a "time for
  telling" (Schwartz & Bransford 1998, *Cognition and Instruction* 16(4)). Meta-analysis of case
  comparisons: d = .50 (Alfieri, Nokes-Malach & Schunn 2013, *Educational Psychologist* 48(2);
  <https://www.lrdc.pitt.edu/Schunn/papers/ContrastingCasesMeta-AlfieriEtAl2013.pdf>). Learning is
  stronger when the principle comes after the comparison.
- **Confidence:** moderate–high.
- **Rules.**
  - Where the right move depends on context, show two close cases (a segment that held viewers and
    one that lost them; the same view expressed as a naked call and as a spread). Ask what differs,
    then state the principle.
  - A `compare_toggle` widget or two scene states are the natural canvas.

## 13. Feedback and hints: contingent, about the task, fading

- **Evidence.**
  - Scaffolding (Wood, Bruner & Ross 1976) and contingent tutoring: more help after failure, less
    after success (Wood, Wood & Middleton 1978; a 2025 replication found effects on immediate
    performance but not on later independent problem-solving).
  - Feedback interventions improve performance on average (d = .41), but more than a third make it
    worse (Kluger & DeNisi 1996). Effects depend on the information the feedback carries
    (Hattie & Timperley 2007; Wisniewski, Zierer & Hattie 2020).
- **Confidence:** moderate.
- **Rules.**
  - Hint ladders have four rungs: question, nudge, worked step, then answer. Each rung used is evidence.
  - Feedback is about the task and the process, never about the person ("not yet", never "wrong").
  - Never praise without evidence.
  - Support fades as mastery grows: less support language, fewer rungs.

## 14. Multiple representations, one model

- **Rule.** Placard text, visual, canvas, cues, checks and tutor seed must describe **the same
  model**, with the same symbols, units, assumptions and case numbers. If the canvas is normalised
  or illustrative, the text says so.

## What not to do

- Do not match lessons to "learning styles". Modality follows content (Pashler et al. 2008 found
  no adequate evidence for the meshing hypothesis; not re-verified in this session).
- Do not pad lessons with motivational filler or rereading summaries.
- Do not treat a correct MCQ as evidence of expression or practice.
- Do not grade a decision by its outcome in odds domains.
