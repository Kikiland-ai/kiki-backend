---
name: kiki-pedagogy-packets
description: Turn a body of knowledge (a chapter, an organisation's playbook or SOP, lecture notes, a recorded review, or a single concept) into researched, pedagogically designed KiKi learning packets for any domain, any learner (students or knowledge workers) and any target language. The packets feed the multilingual translation and speech pipeline, the canvas factory (widgets and scene templates), domain packs, lesson ledgers and tutor graphs. Use when asked to build lessons, modules, placards, checks, glossaries, canvas specs or tutor-graph seeds for KiKi, or to "research and teach" a topic. Do not use to translate, synthesize audio, render canvases, run tutor sessions or publish; those are downstream stages.
---

# KiKi pedagogy packets

KiKi helps people learn a body of knowledge **in the language they think in**, practise it in the
real tool, and reason it through. Learners lose performance to the working language and to
unwritten know-how, not to ability. This skill is the content step of the tribal-knowledge
builder: it turns source material into one `kiki-chapter-plan/v1` per request and one
`kiki-pedagogy-packet/v1` per concept. It works in any sector: engineering, trading, streaming,
clinical procedures, sales, compliance and so on.

Each packet is the source-language truth for one concept. It holds:

- researched claims;
- a learner model;
- objectives;
- 1–6 placards;
- a glossary;
- checks across four dimensions;
- a worked question;
- a visual;
- optionally a canvas (widget or scene template), narration cues and a tutor-graph seed.

## The domain decides the pedagogy

Every packet declares a **domain** (`references/domain-corners.md`): the pack, the learner's role,
the languages, the dimension labels, the assessment policy, any practical tool and the guardrails.
It also declares the domain's **corner**. The corner changes what is true, what is checkable and
what is safe to say:

| Corner | Knowledge is | Example domains | Checks mostly evaluate |
|---|---|---|---|
| **laws** | formal, verifiable, one right answer | engineering, field service, clinical procedure, compliance | facts, calculations, procedures |
| **odds** | probabilistic; good decisions can lose | trading, insurance, sales forecasting, operations risk | process quality, diagnosis, judgement against the organisation's rules |
| **audiences** | social and creative; feedback comes from people and live metrics | streaming, marketing, sales calls, customer success, design | diagnosis from signals, judgement with rationale |

## Read before working

1. [Pedagogy principles](references/pedagogy-principles.md): the evidence and the rules it implies. Always.
2. [Domain corners](references/domain-corners.md): the domain block, per-corner rules, guardrails. Always.
3. [Research protocol](references/research-protocol.md): source order (the organisation first), claim ledger. Always.
4. [Packet contract](references/packet-contract.md): exact output shape and the downstream projections. Always.
5. [Authoring rules](references/authoring-rules.md): sentences, glossary, literals, checks, canvas, cues.
6. [Quality gates](references/quality-gates.md): the review pass and known anti-patterns.
7. Worked examples, one per corner:
   - [laws: C-AM-03](templates/laws-C-AM-03.packet.json), with a controllable widget;
   - [odds: event-day IV](templates/odds-TR-IV-EVENT.packet.json), with a payoff scene and a tutor-graph link.

## Workflow

Do the phases in order. Do not write placards before the learner model and objectives exist.

1. **Intake and domain.** Establish:
   - the domain block: pack, corner, learner role and transition, source and target languages,
     practical tool, guardrails;
   - the scope;
   - the source material the organisation or learner supplied;
   - existing concept ids and terms to reuse rather than duplicate.

   Ask only about what changes the output: the corner when unclear, missing scope, conflicting
   sources, or the target language. Default everything else and say what you defaulted.
2. **Research deep.** Mine the supplied material first and cite it by its own section ids
   (`EV-2.1`, "slide 14"). Verify facts and fill gaps from authoritative sources. Record org
   rules and heuristics as such, not as universal facts. Recompute every number.
3. **Map the scope.** For a chapter, module or topic, make a MECE split into groups and then
   concepts, with a prerequisite DAG, route order and test blueprint, and write the plan. Then
   generate the concepts in route order.
4. **Model the learner** per concept:
   - prerequisites;
   - misconceptions, documented or inferred;
   - what is troublesome;
   - element interactivity.

   Split the concept if one concept placard cannot carry the core idea without overload.
5. **Design backwards.** Objectives first, then the evidence that would prove them, then the
   instruction. Every check maps to an owned objective. Every distractor maps to a misconception
   or a named error. In odds and audiences domains, most concept checks judge process, diagnosis
   or judgement, not outcomes.
6. **Write the placards.** Short, self-contained source-language sentences with stable ids,
   glossary term ids, protected literals with spoken forms, and optional cues that drive the canvas.
7. **Specify the canvas** only when it earns its place. Use a **widget** when moving a control
   reveals the relationship. Use a **scene template** (`candles`, `payoff`, `line`, `flow`, `ece`)
   when the learner must read a real signal or case. Otherwise set `canvas: null` with a reason.
8. **Assess** using the domain's assessment policy:
   - concept checks;
   - words;
   - expression (explaining it to peers in the working language);
   - practice in the real tool, when it applies;
   - a worked question.

   Optionally add a `reflect` seed or a link to a tutor graph.
9. **Check.** Run the checker, fix every error, review warnings against the quality gates, then report.

```sh
<python> -X utf8 -B .claude/skills/kiki-pedagogy-packets/scripts/check_packet.py <packet-or-plan.json>... [--emit <dir>]
```

The checker verifies:

- structure, domain and corner rules, and pedagogy lints;
- scene template parameters, and widget behaviour cases (by evaluating their formulas);
- cue targets;
- the `kiki-pack/v0` concept projection;
- for Odia targets, the backend's real mixed-script `validate_input`.

`--emit` writes every projection that a runner would submit.

## Output and report

Write packets to the location the user names, else `work/pedagogy-packets/<packId>/`
(`plan.json`, `<conceptId>.packet.json`). Report:

- the domain and corner;
- the sources actually used;
- the concepts produced;
- the checker output, as actually printed;
- unresolved claims;
- inferred misconceptions;
- the human reviews still needed: domain expert, native speaker per language, pronunciation.

## Boundaries

- The source language, usually English, is the truth. Target-language glosses and pronunciations
  are machine drafts until a native speaker reviews them. Never mark a review complete.
- Never invent sources, section ids, locators, statistics, exam weights or reviews. Case data
  that is invented for teaching is flagged `illustrative` and labelled on screen.
- Honour the domain's guardrails. In high-stakes domains teach **process, not picks**: never
  recommend a live action such as a trade, a dose or a legal step, and never present an outcome
  as proof of a decision's quality.
- Do not use third-party logos, artwork or footage. Refer to brands and products by name only.
- Canvas specs are declarative. Never emit drawing or model code.
- Do not translate, call TTS, render, run tutor sessions or publish. The runner owns those steps.
