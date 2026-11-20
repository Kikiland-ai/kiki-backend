# Quality gates

Run the checker first. Then do this review pass yourself, reading the packet as a student
with the prerequisites but nothing more.

## Gate 1: Truth

- [ ] Every placard sentence, answer key and canvas case traces to a high- or moderate-confidence claim.
- [ ] Every number was recomputed, and the arithmetic is recorded in the claim's `check`.
- [ ] Every idealisation and condition is stated where it is used.
- [ ] Notation matches the student's material (or the stated convention).
- [ ] No invented sources, locators, syllabus lines, exam weights or reviews.

## Gate 2: Learning design

- [ ] Each objective has a measurable verb, a Bloom level, and at least one check that evidences it.
- [ ] The definition placard names and symbols *before* the concept placard uses them.
- [ ] The concept placard grounds the idea concretely before the general relation and contains a refutation.
- [ ] The application placard makes the student *use* the idea (a calculation path, decision or diagnosis).
- [ ] The recap placard is retrievable rules and conditions, not narration about the lesson.
- [ ] Prerequisites are correct and minimal. No term is used before its owner concept.
- [ ] The worked question models the reasoning that the checks then ask for with less scaffolding.

## Gate 3: Assessment quality

- [ ] 5 concept MCQs, difficulty spread, every owned objective covered, correct option position varied.
- [ ] Every distractor is plausible to a real student and has a rationale. A strong student could
      not eliminate options by form alone.
- [ ] Explanations teach: why right, and why the tempting wrong answer is wrong.
- [ ] The lab predict answer is a prediction with a reason. The English check is answerable in 1–2 sentences.

## Gate 4: Pipeline readiness

- [ ] The checker passes with zero errors, including the backend `validate_input` projection.
- [ ] Sentences read correctly in isolation (cover the neighbours and reread each one).
- [ ] Every symbol, formula and unit is a literal with a spoken form that TTS can say unambiguously.
- [ ] The canvas (if any) has ≤3 controls, its behaviour cases pass, and it shows the misconception failing.

## Anti-patterns seen in earlier Kiki content (do not repeat)

Found in the authored C-AM-03 ledger/case content (kiki-web `data-model`, October 2026):

| Anti-pattern | Example | Fix |
|---|---|---|
| Joke or impossible distractors | "It creates a quiz", "It changes the model filename" | distractors from misconceptions or named slips |
| Walkthrough narration unrelated to its target | target "modulation index" narrated with the application sentence | `say` explains the target phrase |
| One-line application placard | "Use an envelope comparison to distinguish…" | a reasoning path with numbers or a decision |
| Predict-check answer copied from the definition | predict answer = AM formula | prediction + reason ("the envelope crosses zero, so…") |
| Generic English check | "In one or two sentences, explain: <title>" | a targeted *why* prompt tied to the misconception |
| Interactive that is just text steps | `step_through` repeating the placards | a real parameter widget, or `canvas: null` with a reason |

## Report back

State: checker output (actual), counts (concepts, placards, checks, terms, canvases), claims at
moderate confidence, inferred misconceptions, open questions, and required human reviews
(scientific, native Odia, pronunciation). Never describe a draft as reviewed or verified.
