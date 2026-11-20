# Trader and streamer content layer

Two complete **draft source-content modules**, built with the pedagogy packet skill from
PR #13 at `940065c`. The design baseline is Design-Thinking `45180af`; the 12 relevant source
files are preserved with hashes in [sources/manifest.json](sources/manifest.json).

Start with [the lesson review](REVIEW.md). For integration, use the two `pack.json` files and
their neighbouring assessments, cue seeds, graphs and review records.

| Persona | Module | Concepts in route order | Target support |
|---|---|---|---|
| Ravi, placeholder trainee trader | Event days | Direction and IV; controlled time comparison; entry risk and sizing; decision journal | Hindi glossary drafts; imported Hindi tutor lines |
| Meera, placeholder creator | Launch-week streams | Hooks and structure; chat warnings; segment ratios; one-change experiments | Hinglish glossary drafts; imported Hinglish tutor lines |

## What is included

- Eight `kiki-pedagogy-packet/v1` files: 32 placards, 80 source sentences, 40 concept MCQs,
  eight words checks, eight expression checks and eight practice predictions. Every MCQ
  distractor has its own rationale. Each lesson includes a worked question and rubric.
- Two `kiki-chapter-plan/v1` module plans, with objectives, prerequisite routes and term ownership.
- Two assembled `kiki-pack/v0` drafts: [trader](packs/trading-fno/pack.json) and
  [streamer](packs/streaming-gta/pack.json). Each has four concepts, inline term chips,
  deterministic scene descriptions, provenance and review state.
- Two adapted eight-node tutor graphs from the pinned design source. Canonical `nextSteps`
  resolve to the new content ids, `caseData.review` records the draft state, and the source
  prototype scorecards are removed from the assembled graphs. No fixed scorecard is learner evidence.
  Unconditional learner-performance claims and causal overclaims are corrected in the exports.
  Changed lines are English-only until translated; unchanged Hindi/Hinglish lines remain inherited drafts.
- Practice-task definitions for paper-case review, saved analytics inspection and a run-of-show
  plan. These are content specifications; no real tool interaction was performed.
- Sentence-level cue **seeds**. There are no timestamps, narration assets or playable cue tracks.

## Boundaries and review status

English is the lesson source. Hindi and Hinglish **lesson renditions have not been generated**.
The packs deliberately advertise only English as available. Target-language term glosses,
pronunciations and the inherited tutor dialogue remain machine drafts pending native review.
The source language is also marked draft pending domain review.

All people, organisations, rules and case data are illustrative. The streamer content refers
to GTA 6 by name only. These cases do not describe an actual launch or use third-party art.
The trader content reviews a historical paper case; it gives no live action recommendation.
Case lot sizes and model assumptions are not represented as current exchange specifications.

The desk's straddle comparison is taught as an organisation heuristic, not a universal profit
boundary. Theta comparisons state which inputs are fixed. The stream ratio compares aggregate
counts, not tracked individuals; charts support a diagnosis to investigate, not proof of causation.
External model definitions were checked against the Options Industry Council's
[Theta](https://www.optionseducation.org/advancedconcepts/theta) and
[Volatility & the Greeks](https://www.optionseducation.org/advancedconcepts/volatility-the-greeks)
pages on 20 November 2026.

The four dimension keys remain `concept`, `words`, `english`, `lab`; displayed labels are
Concept, Words, Expression and Practice. A language gap does not erase concept credit.
Authored practice predictions explicitly earn **no observed-practice credit**.

## Layout

```text
sources/manifest.json             upstream revision and SHA-256 hashes
sources/design/                  unmodified source snapshot
plans/<packId>.plan.json          module route and objective hierarchy
packets/<packId>/*.packet.json    authoritative authored lesson content
packs/<packId>/pack.json          assembled DomainPack draft
packs/<packId>/assessments.json   authored checks and worked-question rubrics
packs/<packId>/cue-seeds.json     sentence cues awaiting TTS timing
packs/<packId>/review.json        review and integration limits
packs/<packId>/graphs/*.json      adapted prototype tutor graph
packs/<packId>/sources/           copied persona, playbook and scenario
```

`assessments.json`, `cue-seeds.json` and `review.json` are authoring sidecars, not additions to
the proposed DomainPack runtime contract. No UI or API consumer for these sidecars is claimed.
Source hashes are checked before assembly, and pack generation is deterministic.

## Build and verify

Run from the repository root, using Python 3:

```sh
python3 -B scripts/build-persona-content.py
python3 -B scripts/build-persona-content.py --check
python3 -B -m unittest discover -s tests -p test_persona_content.py -v
python3 -B .claude/skills/kiki-pedagogy-packets/scripts/check_packet.py \
  content/knowledge-workers/packets/*/*.packet.json \
  content/knowledge-workers/plans/*.json
```

The assembler reuses the PR's checker and adds cross-file checks for objective hierarchy,
term ownership, duplicate placard ids, graph paths, scene references and arithmetic. It checks
source hashes and recomputes the case option prices, budget, P&L and stream endpoint ratios.
It also refuses empty widget expectations. These checks protect this bundle without changing
the shared skill's checker. The graphs are checked against the proposed v0 shape and topology;
no full application schema mirror or runtime integration test is claimed.

## Editing and integration

Edit authoritative packet/plan files, then regenerate and run `--check`. Never edit a pack
export to fix a lesson. A source refresh is an explicit revision-and-hash update; the existing
`context/design-thinking/` snapshot remains untouched.

Next, have a trader and creator review the case reasoning and assessment keys, and have native
reviewers review Hindi/Hinglish. Then connect the pack reader, translate lesson renditions,
generate audio and derive cue timing from actual speech. Only a real observed learner action
may create practice evidence. Publishing, application integration and provider calls are separate work.
