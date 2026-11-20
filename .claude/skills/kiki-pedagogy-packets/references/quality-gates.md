# Quality gates

Run the checker first. Then do this pass yourself, reading the packet as the learner described
in `domain.learner`: someone with the prerequisites and nothing more.

## Gate 1: Truth

- [ ] Every placard sentence, answer key, canvas value, cue and tutor branch traces to a high- or
      moderate-confidence claim.
- [ ] Every number was recomputed, or taken from a case file that carries its own consistency check.
- [ ] Every idealisation, org rule and heuristic is labelled as such where it is used.
- [ ] The vocabulary matches the organisation's material, or the stated convention.
- [ ] Nothing is invented: no sources, section ids, statistics, exam weights or reviews.
      Illustrative data is flagged.

## Gate 2: Learning design

- [ ] Each objective is measurable, has a Bloom level and is evidenced by at least one check.
      Workplace objectives read as job performance.
- [ ] Names and symbols come before use. Concrete grounding comes before the general rule. The
      concept placard refutes a misconception.
- [ ] The application ends in a job action. The recap is retrievable rules.
- [ ] The worked question models the reasoning that the checks then ask for with less scaffolding.
- [ ] Where context decides the right move, a contrasting case is shown.

## Gate 3: Assessment quality

- [ ] The concept checks follow the policy, cover every objective, spread difficulty and vary the
      key position.
- [ ] Every distractor is plausible to a real learner in this role.
- [ ] Odds and audiences: most items judge process, diagnosis or judgement, and none grades a
      decision by its outcome.
- [ ] Explanations teach. The expression check produces something a colleague would accept. The
      practice check happens in the real tool.

## Gate 4: Language and pipeline readiness

- [ ] The checker passes with zero errors.
- [ ] Sentences read correctly in isolation.
- [ ] Every literal has a spoken form that TTS can say.
- [ ] Every target language has draft glosses, marked machine draft.
- [ ] Cues name real states and ids.
- [ ] The canvas uses the same numbers as the text.

## Gate 5: Safety and guardrails

- [ ] The domain's guardrails are honoured. Nothing reads as a live recommendation (a trade, a
      dose, a legal step).
- [ ] No third-party logos, artwork or footage. Brands are named only.
- [ ] Nothing about a real person or organisation is invented. Case data is illustrative or cited.

## Anti-patterns seen in earlier KiKi content (do not repeat)

From the authored C-AM-03 ledger and case content (kiki-web `data-model`, October 2026):

| Anti-pattern | Example | Fix |
|---|---|---|
| Joke or impossible distractors | "It creates a quiz", "It changes the model filename" | distractors from misconceptions or named slips |
| Walkthrough narration unrelated to its target | target "modulation index" narrated with the application sentence | `say` explains the target |
| One-line application placard | "Use an envelope comparison to distinguish…" | a reasoning path that ends in an action |
| Predict answer copied from the definition | predict answer = the AM formula | a prediction plus its reason |
| Generic expression check | "In one or two sentences, explain: <title>" | a targeted *why*, or a job artefact |
| Citation drift | the MathWorks page cited for modulation index and overmodulation; it covers neither | cite only what you opened and checked |

Risks in the new corners:

| Anti-pattern | Example | Fix |
|---|---|---|
| Grading by outcome | "The trade made money, so the thesis was good" as the key | judge the process against the rules |
| Heuristic stated as law | "Viewers leave after 60 seconds of silence" | "The agency's rule LW-3.1: no more than 60 seconds of silence" |
| Advice disguised as a lesson | "Buy calls when PCR is high" | teach the process; PCR is context, never a signal |
| Invented platform statistics | "Streams with polls get 40% more chat" | cite it, or drop it |

## Report back

State:

- the domain, corner and consumers;
- the checker output (actual);
- counts: concepts, placards, checks, terms, canvases;
- moderate-confidence claims;
- inferred misconceptions;
- open questions;
- the reviews still required: domain expert, a native speaker for each target language,
  pronunciation.

Never describe a draft as reviewed or verified.
