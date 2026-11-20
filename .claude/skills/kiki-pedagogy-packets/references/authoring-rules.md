# Authoring rules

## Placards: what each one does

| Kind | Job (pedagogical role) | Sentences | Must contain |
|---|---|---|---|
| definition | Pre-training: name the thing, its symbol and unit, in one precise statement | 1–3 | the owned term(s); the defining relation if there is one |
| concept | Mechanism: concrete grounding → general relation → conditions → refutation | 3–6 | ≥1 sentence with `refutesMisconceptionIds`; every idealisation stated |
| application | Use it: a short worked reasoning path, a design or lab decision, or a diagnosis | 2–5 | real numbers computed in steps, or a decision with its reason |
| recap | Retrieval-ready rules: what to remember and when it applies | 2–4 | the key idea, the main condition, the one formula, no "we learned" filler |

Total narration per concept: roughly 90–220 English words. Placards are learner-paced
segments. Long concepts split into two concepts, never into tiny type.

## Sentences: translation- and audio-ready English

The mixed-script pipeline translates sentence by sentence and checks that terms, literals and
numbers survive. Write for that:

1. **One idea per sentence**, 8–28 words (the checker warns above 32 and errors above 45).
2. **Self-contained.** No "this", "it" or "the former" pointing to a previous sentence when the
   referent is ambiguous. Repeat the noun. Translation treats each sentence alone.
3. **Plain syntax.** Active voice, subject–verb–object, no stacked subordinate clauses, no
   idioms ("rule of thumb", "kicks in"), no rhetorical questions in placards.
4. **Keep qualifiers explicit and near what they qualify**: "In an ideal linear model, …",
   "for a single-tone message", "only when the envelope stays non-negative". Negations are
   short and unmistakable ("does not cross zero").
5. **Terms verbatim.** Use the glossary term exactly as spelled, with the same case, every time.
   No synonyms for a term inside a concept. If a sentence uses a term's text, it must list
   that term id (the checker computes this).
6. **Every placard contains at least one glossary term.** The pipeline rejects an empty
   glossary.
7. **Protected literals.** Every formula, symbol, variable, numeric value with unit and
   acronym that is not a glossary term goes in `literals` with a spoken form:
   - `{"text": "s(t)=Ac[1+mu*cos(2*pi*fm*t)]cos(2*pi*fc*t)", "spoken": "s of t equals A c times one plus mu cosine two pi f m t, times cosine two pi f c t"}`
   - `{"text": "6 V", "spoken": "six volts"}`, `{"text": "Hz/V", "spoken": "hertz per volt"}`
   - Spoken forms are English words for TTS, unambiguous and short. The visible formula stays compact.
8. **Numbers.** The pipeline rejects changed or added numbers. Use only numbers that you want
   preserved, and write them as digits. Avoid number words in the English (write "two
   sidebands" only if "two" is not a quantity you compute with).
9. **Survive the post-translation counts** (`validate_stage` counts by raw substring):
   - A literal must never also occur inside an ordinary word of the same sentence: `mu` inside
     "maximum", "minimum" or "must" is lost when those words become Odia. Rephrase the sentence
     ("largest value"), or make the literal longer (`mu=0.5`).
   - Spoken forms use number **words** ("six volts"), never digits that are not in the sentence.
   - A literal's spoken form must not contain a glossary term's `spoken_en`, and one term's
     `spoken_en` must not sit inside another's unless the English terms nest the same way.
     The checker enforces all three rules.
10. **Formulas** in plain ASCII as the existing packets do (`mu`, `pi`, `*`, `^`, `<=`). Avoid
   Unicode math (μ, ≤) in sentences. Put the pretty form in the visual brief if needed.

## Glossary terms

- A term is introduced by exactly one concept (`ownerConceptId`). Others list it in `usesTerms`.
- `definition`: a single English sentence a student could write in an exam.
- `spoken_en`: how TTS should say the English term (acronyms spaced: "D S B S C").
- `glosses.or` (meaning) and `pronunciations.or` (English term written in Odia script) are
  **drafts**, `review_status: "pending"`. Keep them short, use common Odia words, keep the
  English term in Latin script inside the gloss when there is no common Odia word. When an
  existing ledger already has a gloss for the term, copy it rather than inventing a new one.
- Avoid one-letter or very common English words as glossary terms (they match too often).
  Prefer the full phrase ("modulation index" rather than "index").

## Explanation and walkthrough (ledger `explanation`)

- `text`: 60–140 words, the canonical explanation. It may be the concept placard's sentences
  joined, lightly condensed.
- `walkthrough`: 3–8 steps. Each `target` is a phrase that appears verbatim in `text`. Each `say`
  explains that phrase in one or two sentences ("The envelope is the outline traced through
  the carrier peaks."). Do not reuse an unrelated placard sentence. `dim` follows the colour
  meaning: concept (green), words (red), english (yellow), lab (blue).

## Example and worked question

- `example`: a concrete scenario (a lab waveform, a device, a measured reading) and a one-line
  takeaway that is the transferable rule.
- `workedQuestion`: exam-style prompt, `modelAnswer` written line by line *as the student should
  write it*, rubric marks only for concept steps, summing to `marks`. `examVocabulary` lists the
  term ids the answer must use.

## Checks

| Dimension | Count | Types | Notes |
|---|---|---|---|
| concept | exactly 5 | `mcq` (or `numerical`/`predict` as extras beyond the 5 MCQs) | difficulty spread: ≥1 at 1, ≥1 at 3; cover every owned objective |
| words | ≥1 | `term_match` or `fill_blank` | definition ↔ term. Distractors are definitions of *related* terms in the course |
| english | ≥1 | `short_english` (or `spoken`) | answers `selfExplainPrompt`; `answer` is a model answer, rubric optional |
| lab | ≥1 if `hasPractical` | `predict` | `answer` states the predicted observation **and the reason**, not a copy of the definition |

MCQ writing:

- The stem is a complete question that can be answered without reading the options.
- 4 options by default (3 when no fourth plausible distractor exists). Options are parallel in
  form and similar in length. No joke options, no "all/none of the above".
- `distractorRationale` has one entry per wrong option: a misconception id, or `error: <named slip>`.
- `explanation` explains the correct reasoning and why the most tempting distractor fails.
- Numeric items: distractors are the results of the predicted slips (inverted ratio, forgot
  the factor of 2, used peak-to-peak). Verify each by computation and record it in the claim
  `check`.
- Vary the correct option's position across the five items.

## Canvas widgets: when and how

Make a canvas only when **moving a control reveals the concept's key relationship or makes a
misconception visibly fail**. Good: modulation index → envelope zero-crossing; phase error →
recovered amplitude shrinking as cos(phi). Not worth it: a definition with no variable, a pure
taxonomy, anything where a static comparison table teaches the same thing (`canvas: null`,
`canvasNullReason`).

Design rules:

1. **≤3 controls**, each a quantity named in the placards, with physically sensible ranges.
   The range should straddle the interesting boundary (for example mu from 0 to 1.5 crosses mu=1).
2. **Readouts** are the quantities the checks ask about. A readout that no placard or check
   mentions is clutter.
3. **Default = the textbook-normal case.** Put the failure case in a `placardStates` entry for
   the concept or application placard, so narration and widget agree.
4. **Same model as the text**: same symbols, normalisation and assumptions. List the
   assumptions, and use `claim: ideal_teaching_model`. `mustNotImply` names over-generalisations
   ("does not imply every demodulator fails at mu>1").
5. **Behaviour cases** (3–7): the default, each boundary, and the misconception case, with
   expected readout values you computed by hand. The checker re-evaluates them from the formulas.
6. Describe views ("two stacked traces: carrier with envelope, and envelope alone"). The
   factory owns rendering, colours and code.
