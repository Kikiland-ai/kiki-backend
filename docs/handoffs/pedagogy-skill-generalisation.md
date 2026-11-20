# Charter: generalise the pedagogy skill for knowledge workers

20 November 2026 · branch `feat/pedagogy-packets-skill` (PR #13) · owner: **the next teammate
(to confirm)** · builds on the [session handoff](pedagogy-packets-skill.md) and
[decision 0018](../decisions/0018-pedagogy-packets-skill.md)

## Why

Design-Thinking `main` at `45180af` ("Widen KiKi to knowledge workers…") changes who KiKi is for.
KiKi is now an **active multilingual learning companion for knowledge workers, sold to
organisations**. It spans three kinds of knowledge:

- **laws:** the ECE student;
- **odds:** an F&O trader;
- **audiences:** a GTA 6 streamer.

It works in any language, and the organisation's own material is the source of truth. The
first version of this skill was ECE- and Odia-shaped, so it needed a generalisation pass.

Read first:

- Design-Thinking `docs/knowledge-workers/01-kiki-for-knowledge-workers.md`: philosophy, principles, personas.
- Design-Thinking `docs/knowledge-workers/05-contracts-v0.md`: `kiki-pack/v0`, cue track,
  scene templates, tutor graph, evidence.
- Design-Thinking `docs/knowledge-workers/sessions/S4-builder.md` and `S5-content.md`: the
  builder and content sessions this skill serves.
- Design-Thinking `docs/knowledge-workers/personas/trader/` and `personas/streamer/`: the
  illustrative playbooks, case files and tutor flows.

All of these are **Proposed** (D4 is agreed). Re-read them before changing the contract.

## What this PR now delivers (the generalisation pass is done)

| Old assumption | Now in the skill |
|---|---|
| ECE student, Odia only | A `domain` block on every packet and plan: pack, **corner**, learner role and transition, source/target/working languages, dimension labels, assessment policy, practical tool, guardrails, consumers |
| Textbooks and web first | The organisation's material first, cited by its own ids (`EV-2.1`). New origins (`org_playbook`, `org_case`, …) and claim kinds (`org_rule`, `heuristic`, `illustrative_data`) |
| One kind of knowledge | Per-corner rules in `references/domain-corners.md`, enforced by the checker: guardrails required for odds and audiences; at least 3 concept items judging process, diagnosis or judgement, citing the rule they are judged against |
| Exactly 4 placards, 5 MCQs | 1–6 placards with an `example` kind. Exactly four only when the consumer is the ECE `learning-case/v1`. The MCQ count and options come from `assessmentPolicy` |
| Odia pipeline + ledger only | Projections chosen by `consumers`: `kiki-pack/v0` concept emitted always; Odia `mixed-script-input/v1` only when `or` is a target |
| Widget canvas only | Canvas `form: widget` (as before) or `form: scene`, using the contract templates `candles`, `payoff`, `line`, `flow`, `ece` with named states. Sentence `cue`s drive the canvas. Optional `reflect`: a link to a tutor graph, or a seed with a 4-rung hint ladder |
| Pedagogy for students | Four new evidence sections (verified 2026-11-20): transfer of training, outcome bias (process vs outcome), contrasting cases, contingent hints and feedback. Language principles generalised to any language, with expression in a `workingLanguage` |

Worked examples, both passing (0 errors, 0 warnings):

- `templates/laws-C-AM-03.packet.json`: ECE, `en`→`or`, all four consumers, widget canvas.
  The backend `validate_input` accepts all four placard projections.
- `templates/odds-TR-IV-EVENT.packet.json`: an F&O trainee, `en`→`hi`, `kiki-pack/v0`, a payoff
  scene with before/after states, cues, and a `graphRef` to `trading-fno/bad-call-iv-crush`.
  Numbers come from the case file's own Black–Scholes check.

Checker verification (run with the backend venv Python):

- Both examples pass.
- 11 new seeded defects were each caught: odds without guardrails, too few reasoning items, a
  heuristic citing a non-org source, a bad cue state, a payoff range that excludes spot, a short
  hint ladder, a missing target gloss, live-advice phrasing (warning), illustrative data
  unflagged, five placards for `learning-case/v1`, and the Odia pipeline declared for a Hindi target.
- The 11 defects from the first pass still apply to the same rules.

## Not done: the charter for the next owner

Ordered by value. Each item names its acceptance test.

1. **Audiences worked example.** Build a streamer packet from
   `personas/streamer/playbook-excerpt.md` and `scenario.json` (for example "hooks and the
   retention curve", LW-3.1/LW-4.1), with a `line` scene that has segment bands, and a
   Hindi or Hinglish target (`hi-Latn`).
   *Accept:* it passes the checker; at least 3 concept items are diagnosis or judgement; the
   heuristics are attributed to the agency in the sentences.
2. **Chapter/module plan example** for a non-ECE pack (for example the trader "Event days" module: four
   concepts from playbook §2, §3, §4 and §6).
   *Accept:* `kiki-chapter-plan/v1` passes; route and DAG are valid; there is no chapter test,
   because the module policy needs none.
3. **Pack assembly.** Add a small script that merges the emitted `*.pack-concept.json` files and
   the plan into a full `kiki-pack/v0` (`pack.json`: modules, concepts, terms, scenes,
   provenance, `languages.review`).
   *Accept:* it validates against the S2/S4 zod or pydantic mirror once that exists.
4. **Language-generic translation adapter.** The backend pipeline validators are Odia-only
   (S4 calls this out). Specify a `translation-input/v1` with a script-range table (`or`, `hi`,
   `ta`, `te`, `bn`, `mr`, `kn`, plus `-Latn` variants) and the same preservation rules. Then make
   `consumers` accept it.
   *Accept:* the trader example projects to Hindi inputs that a generic validator accepts.
5. **Notes-only sources.** `mixed-script-input/v1` requires an HTTPS reference, but organisation
   material often has none. Propose a document-reference form, with `sourceDocId` and a locator.
6. **Tutor seed → graph.** Turn a `reflect.seed` into a `kiki-tutor-graph/v0` draft (8–12 nodes)
   and check it with Design-Thinking `personas/tools/validate_ece_graph.py`, generalised.
7. **Contract sync.** Contracts v0 is still Proposed. When the hub freezes it (H1), update
   `packet-contract.md` and the checker's template validators to match. Today `payoff` accepts
   the v0.2 `rate` field, and the state `values` are free-form.
8. **Rename the dimension keys** (`english` → expression, `lab` → practice) only when the hub
   does. Until then the keys stay and only the labels change (D2).

## Open decisions (owner: hub or team)

- **Where the skill lives.** It is in kiki-backend today. The builder slice (S4) runs in
  kiki-web `apps/api`. Decide whether the skill or its checker moves, or is vendored, next to
  the builder.
- **Default `workingLanguage` per pack.** For example, English for ECE, and English or
  Hinglish for the desk.
- **Whether Odia stays the brand's anchor** (clarity map, open question 3). This affects which
  examples lead the documentation.

## How to verify on your system

```sh
<python> -X utf8 -B .claude/skills/kiki-pedagogy-packets/scripts/check_packet.py \
  .claude/skills/kiki-pedagogy-packets/templates/*.packet.json --emit <dir>
# expect: both PASS (0 errors, 0 warnings); <dir> gets two *.pack-concept.json and four Odia mixed inputs
```

The checker uses the standard library only. It imports `prototypes/mixed_script/pipeline.py`
when run inside kiki-backend. Elsewhere it skips the Odia validation and reports that it did so.

## Guardrails to keep

- Process, not picks (odds).
- Names only, no third-party art (audiences).
- Machine-draft labels until native review.
- Illustrative data is flagged.
- No invented sources, statistics or reviews.
- Canvas specs stay declarative.
