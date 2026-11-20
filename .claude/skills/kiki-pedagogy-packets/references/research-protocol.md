# Research protocol: going deep on a concept

The goal is a **claim ledger**, not a long survey. It must be complete enough that every placard
sentence, check answer, canvas value and tutor branch traces to a verified claim.

## 1. Decompose into research branches

For each concept, answer the branches that apply and say which ones you skipped:

| Branch | Question | Feeds |
|---|---|---|
| Definition | What exactly is it, in the notation and vocabulary *this organisation or course* uses? | definition placard, terms |
| Purpose | What job problem or decision does it serve? | `canDo`, concept placard opening |
| Mechanism or rule | How does it work, or what does the organisation's rule say, and why? | concept placard, walkthrough |
| Quantities | Governing relations, ranges, thresholds, budgets, limiting cases | literals, canvas, worked question |
| Conditions | Assumptions, idealisations, when the rule stops applying | refutation sentences, `assumptions` |
| Contrasts | Neighbouring ideas that people confuse with it; two close cases | misconceptions, distractors, contrast scenes |
| Misconceptions | Documented errors (research, inventories, the org's own review notes) | misconceptions, distractors, tutor seed |
| Application | Where it shows up in the job or the tool | application placard, example, practice check |
| Assessment | How exams, desk reviews, agency reviews or vivas test it | worked question, checks, `examSignal` |

## 2. Source order (authority depends on the claim)

1. **The organisation's or learner's own material.** Playbooks, SOPs, case files, recorded
   reviews, lecture notes, syllabus, experiment sheets, past papers. It sets scope, vocabulary,
   rules and emphasis. Cite it by its own ids and locators (`EV-2.1`, "slide 14", "p. 3").
   Origins: `org_playbook`, `org_sop`, `org_case`, `org_recording`, `lecture_notes`, `syllabus`,
   `student_notes`, `experiment_sheet`, `past_paper`, `teacher`.
2. **Standard references**: textbooks, university course notes, standards, regulator
   guidance (`textbook`, `standard`, `regulator`).
3. **Official tool and vendor documentation**: tool behaviour, parameters and specifications (`vendor_doc`).
4. **Research**: learning-science and domain studies, concept inventories, misconception
   studies (`research`).
5. **Encyclopaedias, tutorials and forums**: leads only, never the sole source of a claim (`curated` at most).

Open every page you cite. Snippets are not sources. A source you cannot open goes to
`research.openQuestions`.

**When organisation material conflicts with external evidence:**
- An org *rule* (a budget, a template, a review practice) is authoritative for that
  organisation. Teach it as their rule.
- An org *factual* claim that external evidence contradicts (a wrong formula, a misread
  regulation) must not be taught as fact. Record it in `openQuestions` for the domain owner.
  Teach only what is right, or what both sources agree on.
- Never override safety, legal or regulatory constraints with an org heuristic.

## 3. Claim ledger

```json
{"id": "CL-4", "kind": "org_rule", "text": "EV-2.1: if you cannot say why your expected move beats the implied move, do not buy premium into the event.",
 "sourceIds": ["S-1"], "confidence": "high", "check": "Quoted rule from the desk playbook, section 2."}
```

- `kind`:
  - `definition`, `fact`, `relation`, `condition`, `idealisation`, `procedure`, `convention`;
  - `org_rule`: the organisation's binding rule;
  - `heuristic`: the organisation's rule of thumb;
  - `illustrative_data`: numbers in a teaching case;
  - `misconception_evidence`.
- `confidence`:
  - `high`: two independent sources, or a source plus a derivation, or a verbatim org rule;
  - `moderate`: one authoritative source;
  - `low`: indirect. **Low-confidence claims may not appear in placards, answer keys, canvas
    expectations or tutor branches.**
- `check`: how you verified the claim. Recompute every number and write the arithmetic down.
  For illustrative cases, cite the case file's own consistency check if it has one (for
  example, a Black–Scholes check script), or recompute.
- Notation and vocabulary: use the organisation's terms. Record the mapping to standard notation
  as a `convention` claim.

## 4. Contradictions

Before calling sources contradictory, check:

- definitions (peak vs RMS, gross vs net, concurrent vs average viewers);
- normalisation, units, time windows and populations;
- an idealised model vs practice;
- a rule vs a fact.

Most conflicts turn out to be apparent. Record real ones in `openQuestions`.

## 5. Misconception mining

1. Look for misconception research for the topic: "<topic> misconceptions", "<topic> concept
   inventory", "common mistakes <role>", "<bias> decision making".
2. Mine the organisation's own material. Rules that say "never" or "don't" usually exist because
   people made that mistake. Recorded reviews and post-mortems are the best evidence.
3. Add contrasts and predictable slips: sign errors, factors of two, units; for odds, sizing
   from conviction; for audiences, reading one metric alone.
4. In odds domains, consider **outcome bias** every time (pedagogy principles §11).
5. Tag each misconception `documented` (with a source) or `inferred` (with reasoning). Two or three
   strong misconceptions beat a long weak list.

## 6. Stopping rule

Stop when every applicable branch has high- or moderate-confidence claims for what the placards,
checks, canvas and tutor seed need, and further searching would not change the content. Name
exclusions in `research.outOfScope`.

## 7. Scope mapping (chapter, module and topic scope)

- Split on **one stated dimension** per level, with a rationale and named exclusions:
  - chapter: 2–5 groups;
  - module or topic: 1 group;
  - each group: 2–5 concepts.

  Groups map to `kiki-pack/v0` modules and to ledger broad concepts.
- Each concept is one teachable idea, about 8–15 minutes, with its own objective(s).
- Prerequisites form a DAG. School-level or earlier-role needs become `externalPrerequisites`.
- When a practical or Do-mode task exists, list its required concepts and include all their prerequisites.
- Tests: a chapter gets the policy's chapter test (10 MCQs in the student journey). Modules and
  topics need none unless the policy says so.
