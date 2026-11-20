# Authoring rules

## Placards: what each one does

| Kind | Job | Sentences | Must contain |
|---|---|---|---|
| definition | Pre-training: name the thing, its symbol or the trade's word, in one precise statement | 1–3 | the owned term(s); the defining relation or rule, if any |
| concept | The mechanism or rule and its reason: concrete grounding, then the general idea, conditions and a refutation | 3–6 | at least one `refutesMisconceptionIds`; every idealisation or heuristic labelled as such |
| example | One concrete case, ideally the organisation's own, or a contrasting pair | 2–5 | real numbers or observations from the cited case; `illustrative` flagged |
| application | Use it: a reasoning path, a decision or diagnosis, or the job action the learner takes | 2–5 | steps with their reasons; ends in an action the learner takes in the job |
| recap | Retrieval-ready rules: what to remember and when it applies | 2–4 | the key idea, the main condition, the org rule id if there is one; no "we learned" filler |

Use 1–6 placards (the four-kind arc for the ECE web route). The total narration per concept is
roughly 90–250 words in the source language.

## Sentences: translation- and audio-ready

The pipeline translates sentence by sentence and checks that terms, literals and numbers
survive. Write for that in any domain:

1. **One idea per sentence**, 8–28 words. The checker warns above 32 words and errors above 45.
2. **Self-contained.** Do not use "this" or "it" for something in the previous sentence. Repeat
   the noun.
3. **Plain syntax.** Active voice. No idioms, slang or desk or stream shorthand unless it is a
   glossary term. No rhetorical questions.
4. **Qualifiers explicit and adjacent**: "In an ideal linear model…", "The desk's quick guide…",
   "The agency's rule of thumb…". Short, unmistakable negations.
5. **Terms verbatim.** Use the glossary term exactly, in the same case, every time, with no
   synonyms. The checker computes `term_ids`. Matching is case-sensitive, so a lowercase term
   at the start of a sentence ("Implied volatility is…") is **not** detected. Rephrase so the
   term is not the first word ("The implied volatility of an option is…").
6. **Every placard contains at least one glossary term.**
7. **Protected literals.** Every formula, symbol, number with its unit, price, rule id
   (`EV-2.1`, `LW-3.1`), tool label or acronym that is not a glossary term goes in
   `literals`, with a spoken form:
   - `{"text": "₹90.25", "spoken": "ninety rupees twenty-five paise"}`
   - `{"text": "EV-2.1", "spoken": "E V two point one"}`
   - `{"text": "s(t)=Ac[1+mu*cos(2*pi*fm*t)]cos(2*pi*fc*t)", "spoken": "s of t equals A c times one plus mu cos two pi f m t, times cos two pi f c t"}`
8. **Numbers** are written as digits in the sentence, and only the numbers you want preserved.
9. **Survive the post-translation counts.** The validation stage counts by raw substring:
   - A literal must never also occur inside an ordinary word of the same sentence (`mu` inside
     "maximum"; `IV` inside a word). Rephrase the sentence or lengthen the literal.
   - Spoken forms use number **words**, never digits that are not in the sentence.
   - A literal's spoken form must not contain a glossary term's `spoken`, and one term's
     `spoken` must not sit inside another's unless the source terms nest in the same way.
10. Use ASCII math (`mu`, `pi`, `<=`) and ASCII hyphens (`-`, not `−`). Currency symbols are
    allowed inside literals.

## Glossary terms

- A term is introduced by exactly one concept (its `ownerConceptId`). Other concepts list it in `usesTerms`.
- `definition`: one source-language sentence a learner could say to a colleague.
- `spoken`: how TTS should say the term in the source language (spell acronyms out: "I V", "O B S").
- `glosses.<lang>` and `pronunciations.<lang>` for every target: short, everyday words, with the
  canonical term kept in Latin script where speakers keep it. They are drafts, with
  `review_status: pending`. Reuse existing glosses from the domain's ledger or pack.
- Avoid one- or two-letter terms (they over-match). Use the full term ("implied volatility",
  with the alias "IV") and put the bare acronym in a literal where needed.

## Explanation and walkthrough

- `text`: 60–140 words, the canonical explanation.
- `walkthrough`: 3–8 steps. Each `target` appears verbatim in `text`, and each `say` explains that
  target. `dim` follows the four colours.

## Example and worked question

- The `example` is a concrete case, preferably from the organisation's own work, and ends in a
  transferable takeaway.
- The `workedQuestion` is a prompt in the style of the domain's assessment (an exam question, a
  desk review question, an agency plan review), with a line-by-line model answer and a rubric
  for concept marks only.

## Checks

| Dimension (key) | Count | Types | Notes |
|---|---|---|---|
| concept | `assessmentPolicy.conceptChecks` MCQs (default 5) | `mcq`; extras may be `numerical`, `predict`, `order_steps` | difficulty spread; every owned objective covered; set `evaluates` |
| words | ≥1 | `term_match`, `fill_blank` | distractors are definitions of *related* terms |
| english (Expression) | ≥1 | `short_english`, `spoken`, `long_written` | in the `workingLanguage`; answers `selfExplainPrompt` or produces a job artefact (rationale, plan) |
| lab (Practice) | ≥1 when `practical.applies` and `practiceTaskId` is set | `predict`, `order_steps`, `label_diagram` | in the real tool; the answer states what to read or do **and why** |

Corner guidance for concept MCQs (`evaluates`):

- **laws**: `fact`, `calculation`, `procedure`. Numeric distractors are the results of named slips.
- **odds**: at least 3 of `process` ("Which rule did the note skip?"), `diagnosis` ("What
  mainly caused the loss?") and `judgement` ("How should the desk review it?"). Never ask
  "was it a good trade?" when the answer depends on the outcome.
- **audiences**: at least 3 of `diagnosis` ("Where does the curve show the hook failing?"),
  `judgement` and `process`. For judgement items, every option is plausible, and the key
  follows from a cited org rule or heuristic, which the explanation names.

Item writing in every corner:

- The stem is answerable without the options.
- 3–4 parallel options; no jokes; no all/none of the above.
- Each distractor has a rationale (a misconception id, or `error: …`).
- The explanation says why the key is right and why the tempting option is wrong.
- Vary the position of the key.

## Canvas

Make one only when it teaches:

- **Widget**: moving a control reveals the relationship or breaks the misconception (modulation
  index → envelope zero-crossing). It has at most 3 controls, readouts that the checks use, a
  textbook default, and the failure state bound to the concept placard.
- **Scene template**: the learner must read a case or signal. Use `candles` with event markers,
  `payoff` before and after an IV change, `line` (retention with segment bands, IV over time),
  `flow` (a run-of-show, a procedure) or `ece` (the existing ECE renderers). Fill `params` with
  the case's own numbers and define named `states` that the narration moves between.
- If none fits, use `canvas: null` with a reason. Do not invent a new template; propose one to
  the canvas factory.
- Every canvas uses the same model and numbers as the text. Label illustrative data.
  `mustNotImply` names any over-generalisation, or any advice the picture might suggest.

## Cues (narration drives the canvas)

Add `cue` to a sentence when the canvas should change as it is spoken:

- `{"state": "after"}`: a scene state;
- `{"state": {"mu": 1.2}}`: widget control values;
- `{"highlight": ["leg-24200ce"]}`: ids inside the scene.

The runner turns cues into the cue track, with timing from TTS. Do not invent timestamps.

## Reflect (tutor mode)

Where the domain has a tutor graph, link it (`graphRef`). Otherwise, seed one:

- one realistic problem;
- 2–3 insights (each tied to a metric);
- the concept's misconceptions;
- a 4-rung hint ladder (question, nudge, worked step, answer).

The hint ladder uses the concept's own numbers and rules.
