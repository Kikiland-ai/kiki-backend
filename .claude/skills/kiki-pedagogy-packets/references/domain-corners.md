# Domains and corners

KiKi is one engine for many kinds of knowledge work. **Domains are data**: a new sector is a
new domain block plus source material, never a new skill. This file says what the domain
block holds, and how each knowledge corner changes the pedagogy.

Source: Design-Thinking `docs/knowledge-workers/01-kiki-for-knowledge-workers.md` (v0.2,
20 Nov 2026) and `05-contracts-v0.md` (kiki-pack/v0). Both are **Proposed**; re-read them if
they change.

## The domain block (every packet and plan)

```jsonc
"domain": {
  "packId": "trading-fno",                 // kiki-pack/v0 id; ECE: "ece-analog-modulation"
  "corner": "laws | odds | audiences",
  "profileId": "trading",                  // subject/domain profile, when one exists
  "learner": {"role": "Trainee index-options trader", "transition": "retail habits → desk process",
              "priorKnowledge": "what they already know and use"},
  "languages": {"source": "en", "targets": ["hi"], "workingLanguage": "en"},
  "dimensionLabels": {"concept": "Concept", "words": "Words", "english": "Expression", "lab": "Practice"},
  "assessmentPolicy": {"conceptChecks": 5, "passPercent": 60, "options": 4},
  "practical": {"applies": true, "label": "Practice", "tool": "Trading terminal (paper mode, historical replay)"},
  "guardrails": ["Process, not picks: past or paper trades only; never recommend a live trade"],
  "consumers": ["kiki-pack/v0"]            // which projections this packet must satisfy
}
```

- **Dimension keys never change.** `concept` (green), `words` (red), `english` (yellow, shown
  as *Expression*: explaining it clearly to peers in the team's working language) and `lab`
  (blue, shown as *Practice*: doing it in the real tool). Labels come from the domain.
- **`workingLanguage`** is the language the learner must eventually *express* the work in.
  For an Indian engineering student it is English; for a Hindi-speaking desk it may be Hinglish
  (`hi-Latn`). Canonical terms keep their form in every language.
- **`assessmentPolicy`** comes from the product or the buyer: the confirmed student journey
  uses 5 concept MCQs at a 60% pass. Org packs may set their own.
- **`consumers`** decides which projections the checker enforces:
  - `kiki-pack/v0`: always valid; the concept, terms and scenes for a domain pack.
  - `learning-case/v1` and `lesson-ledger/v2`: the existing ECE web route. It needs exactly
    the four placard kinds in order.
  - `mixed-script-input/v1`: the current backend translation pipeline. It supports Odia only,
    so it applies only when `or` is a target.

## How the corner changes the pedagogy

| | **laws** | **odds** | **audiences** |
|---|---|---|---|
| What "correct" means | Derivable, verifiable | A good *process* given what was knowable; outcomes are noisy | A good *read* of people and signals, plus a plan with a rationale; several answers may be acceptable |
| Typical sources | Textbooks, standards, datasheets, lecture notes, SOPs | The org's playbook and risk rules, past case files, regulator guidance | The org's playbook, recorded reviews, analytics exports, a creator's own past streams or calls |
| Claim kinds that dominate | `definition`, `relation`, `condition`, `procedure` | `org_rule`, `heuristic`, `illustrative_data`, `fact` (market mechanics) | `heuristic`, `org_rule`, `illustrative_data` |
| Misconceptions to mine | Formula slips, over-generalised rules, confused neighbours | **Outcome bias** (judging a decision by its result), direction-only thinking, sizing from conviction | Vanity metrics, "more content = more engagement", reading one signal alone |
| Concept checks evaluate | `fact`, `calculation`, `procedure` | Mostly `process`, `diagnosis`, `judgement` (≥3 of the concept checks) | Mostly `diagnosis`, `judgement`, `process` (≥3 of the concept checks) |
| Good item stems | "Calculate…", "Which condition…" | "Which rule did this note break?", "What mainly caused this P&L?", "How should the desk review this?" | "Where does the retention curve show the hook failing?", "Which change best fits LW-3.1?" |
| Canvas | Widget on the governing relation; `ece` scenes | `candles`, `payoff` (before and after), `line` (IV, P&L) | `line` with segment bands and markers, `flow` (run-of-show) |
| Practice (Do mode) | Build or measure in the simulator or instrument | Read the chain or chart and set risk on a paper or replayed book | Read the analytics dashboard, restructure the plan |
| Guardrails | Lab safety; "ideal teaching model, not a measurement" | **Process, not picks.** Past or paper trades only; disclaimer; no live advice | Platform and brand names only, no logos or footage; no invented platform statistics; respect for audiences |

### Corner rules the checker enforces

- `odds` and `audiences` need a non-empty `guardrails` list.
- In `odds` and `audiences`, at least 3 concept checks must evaluate `process`, `diagnosis` or
  `judgement`. Each of those checks cites an `org_rule`, `heuristic` or research claim.
- `org_rule` and `heuristic` claims cite an organisation source: `org_playbook`, `org_sop`,
  `org_case`, `org_recording`, `lecture_notes`, `syllabus`, `student_notes`,
  `experiment_sheet`, `past_paper` or `teacher`. A heuristic is the organisation's rule of
  thumb. Say so in the sentence ("The desk's quick guide…", "The agency's rule…") and never
  present it as a law of nature.
- `illustrative_data` claims cite a source marked `"illustrative": true`.
- `odds`: a sentence that sounds like a live recommendation ("you should buy", "go long now")
  raises a warning. An organisation's *process rule*, stated as a rule with its id, is fine.

## Adding a new domain

1. Write the domain block. Pick the corner by asking: is there one verifiable answer (laws), a
   probabilistic outcome (odds), or a judgement about people (audiences)?
2. Collect the organisation's material and give every section a citable id.
3. Write the guardrails with the domain owner, particularly for regulated or high-stakes work.
4. Choose the canvas forms the domain needs from the existing templates. If none fits, propose a
   new scene template to the canvas factory as a contract change. Do not improvise drawing code.
5. Make one worked packet. Run the checker. Have a domain expert and a native speaker review it.
