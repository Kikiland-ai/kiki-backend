# Packet contract

There are two documents, both UTF-8 JSON. Ids match `[A-Za-z0-9][A-Za-z0-9_.-]{0,79}` (the
pipeline id rule), are stable and ASCII. Sentence ids are `<placard-id>.s<n>`.

## Downstream map

| Packet field | Consumer | As |
|---|---|---|
| `placards`, `terms`/`usesTerms`, `canvas` (scene form) | **kiki-pack/v0** (`05-contracts-v0.md` §1) | `Concept{id,title,goal,placards}`, `Term{id,term,meaning,say}`, `Scene` |
| `placards[].sentences[].cue` | Cue track (§2) | seeds for `Cue{sentence, scene{state, highlight}}`; the runner adds `t` from TTS timing |
| `canvas` (widget form) | concept-canvas factory | a trusted analytic widget plus behaviour tests |
| `canvas` (scene form) | scene templates (§3) | a `candles` / `payoff` / `line` / `flow` / `ece` scene with `states` |
| `reflect` | tutor graph authoring (§4) | a link to an existing graph, or a seed (problem, insights, misconceptions, hint ladder) |
| `teaching.*`, `objectives`, `terms`, `learner.*` | kiki-web `lesson-ledger/v2` | `Concept`, `Objective[]`, `Term[]` (same field names) |
| placards (exactly four kinds) | kiki-web `learning-case/v1` | `Placard` (source text; target text added by the pipeline) |
| placards + terms | backend `mixed-script-input/v1` (Odia only today) | one input per placard |
| `teaching.checks` | assessments / evidence (§6) | lesson-check evidence on the four dimensions |

## `kiki-pedagogy-packet/v1` (one per concept)

```jsonc
{
  "schema": "kiki-pedagogy-packet/v1",
  "packetId": "PKT-TR-IV-EVENT-1",
  "createdAt": "2026-11-20T00:00:00Z",
  "domain": { /* see domain-corners.md */ },
  "scope": {"planId": "LP-…", "groupId": "MOD-…", "conceptId": "TR-IV-EVENT", "order": 1,
            "canonicalKey": "iv-before-events", "title": "…", "practiceTaskId": "pre-event-checklist"},
  "status": {"review": "draft", "domainReview": "pending", "pronunciation": "pending",
             "languages": {"hi": "machine_draft"}},

  "research": {
    "governingQuestion": "…",
    "sources": [{"id": "S-1", "origin": "org_playbook", "tier": 1, "label": "…", "url": "https://… (optional)",
                 "locator": "§2, EV-2.1", "illustrative": false}],
    "claims": [{"id": "CL-1", "kind": "org_rule", "text": "…", "sourceIds": ["S-1"], "confidence": "high", "check": "…"}],
    "outOfScope": [], "openQuestions": []
  },
  "learner": {"prerequisiteIds": [], "externalPrerequisites": [], "troublesome": "…",
              "misconceptions": [{"id": "M-…", "statement": "…", "correction": "…", "basis": "documented|inferred",
                                  "sourceIds": [], "reasoning": "…"}]},
  "objectives": [{"id": "O-…", "statement": "…", "bloom": "apply", "parentId": "O-…", "ownerId": "<conceptId>"}],

  "terms": [{"id": "T-…", "term": "implied volatility", "definition": "…", "aliases": ["IV"], "symbol": null, "unit": null,
             "ownerConceptId": "<conceptId>", "spoken": "implied volatility",
             "glosses": {"hi": "draft meaning"}, "pronunciations": {"hi": "draft, in the target script"},
             "review_status": "pending"}],
  "usesTerms": [ /* same shape, owned by another concept */ ],

  "teaching": {
    "canDo": "…", "keyIdea": "…", "selfExplainPrompt": "Why …?",
    "explanation": {"text": "60–140 words", "defaultModality": "textImage",
                    "walkthrough": [{"target": "phrase in text", "mark": "sweep|marker|lens|connect|circle",
                                     "dim": "concept|words|english|lab", "say": "…"}]},
    "example": {"title": "…", "scenario": "…", "takeaway": "…", "sourceIds": ["S-2"]},
    "workedQuestion": {"id": "W-…", "type": "numerical", "marks": 2, "prompt": "…", "modelAnswer": ["…"],
                       "rubric": [{"criterion": "…", "marks": 1, "objectiveId": "O-…"}], "examVocabulary": ["T-…"]},
    "checks": [{"id": "Q-…", "type": "mcq", "dimension": "concept",
                "evaluates": "fact|calculation|procedure|process|diagnosis|judgement|recall",
                "prompt": "…", "options": ["…"], "answer": "…",
                "distractorRationale": {"<option>": "M-…|error: …"}, "explanation": "…",
                "objectiveIds": ["O-…"], "difficulty": 1, "claimIds": ["CL-…"]}],
    "examSignal": {"basis": "none", "askedIn": 0, "outOf": 0, "note": "…"},
    "estMinutes": 12
  },

  "placards": [{"id": "CARD-…-definition", "kind": "definition|concept|example|application|recap",
                "title": {"en": "…"},
                "sentences": [{"id": "CARD-…-definition.s1", "english": "source-language sentence",
                               "term_ids": ["T-…"], "literals": [{"text": "…", "spoken": "…"}],
                               "claimIds": ["CL-…"], "refutesMisconceptionIds": [],
                               "cue": {"state": "after", "highlight": ["leg-24200ce"]}}],
                "visualRef": "explanation"}],

  "visual": {"kind": "…", "description": "what to draw", "alt": "…", "sourceIds": ["S-1"]},
  "canvas": { /* widget or scene form, or null */ },
  "canvasNullReason": "required when canvas is null",
  "reflect": null,      // or {"graphRef": "trading-fno/bad-call-iv-crush"} or {"seed": {…}}
  "handoff": {"speechNotes": ["…"]}
}
```

- The field is named `english` for compatibility, but it holds the sentence in
  `domain.languages.source`. The sentence lints assume a Latin-script source.
- **Placards.**
  - 1–6 per concept; at least one `concept` placard.
  - At most one `definition` (first, if present) and one `recap` (last, if present).
  - When `consumers` includes `learning-case/v1`, exactly `definition, concept, application, recap`.
  - Sentences per placard: 1–10.
- `term_ids` equal **exactly** the glossary terms whose text occurs in the sentence
  (case-sensitive, whole-word: the same rule as `pipeline.py`).
- Each term has a draft gloss for **every** target language. Pronunciations are required for
  `or` (the pipeline needs them) and recommended for the other targets.

## Canvas, widget form (a controllable concept widget)

```jsonc
{"form": "widget", "artifactId": "CANVAS-…", "status": "proposed", "reusesPinnedScene": "C-AM-03" /* or null */,
 "kind": "am" /* pinned scene kind or "new" */, "interaction": "parameter_sweep|compare_toggle|step_through|label_parts|sort_steps",
 "purpose": {"objectiveIds": [], "misconceptionIds": [], "insight": "what the learner should notice"},
 "controls": [{"name": "mu", "label": "…", "min": 0, "max": 1.5, "step": 0.1, "default": 0.5, "unit": ""}],
 "model": {"assumptions": [], "equations": [{"text": "…", "spoken": "…"}],
           "outputs": [{"name": "envMin", "label": "…", "unit": "normalized", "formula": "1-mu", "decimals": 2}],
           "views": [{"kind": "trace|table|spectrum|flow|phasor", "description": "…"}]},
 "behaviorCases": [{"inputs": {"mu": 1.2}, "expect": {"envMin": -0.2}, "tolerance": 1e-6, "observation": "…", "showsMisconception": true}],
 "placardStates": [{"placardId": "…", "controls": {"mu": 1.2}, "cue": "…"}],
 "mustShow": [], "mustNotImply": [], "claim": "ideal_teaching_model", "alt": "…"}
```

- 1–3 controls. Units are `"" | normalized | Hz | degree` for the current scene contract; other
  units raise a warning.
- Formulas use the ledger grammar plus `sin`, `cos` and `tan`. 3–7 behaviour cases, which the
  checker evaluates; at least one has `showsMisconception: true`.
- Sentence cues set control values: `"cue": {"state": {"mu": 1.2}}`.

## Canvas, scene form (a deterministic template from contracts v0 §3)

```jsonc
{"form": "scene", "purpose": {…}, "illustrative": true,
 "scene": {"id": "tr-payoff", "template": "payoff",
           "params": {"legs": [{"id": "leg-24200ce", "type": "call", "side": "long", "strike": 24200, "premium": 90.25, "lots": 4}],
                      "lotSize": 75, "spot": 24040, "range": [23600, 24600],
                      "iv": {"before": 0.175, "after": 0.11}, "daysToExpiry": {"before": 3, "after": 2}},
           "states": {"before": {"values": {"ivPhase": 0}}, "after": {"values": {"ivPhase": 1}}}},
 "mustShow": [], "mustNotImply": [], "claim": "illustrative_case|ideal_teaching_model", "alt": "…"}
```

- Templates: `candles`, `payoff`, `line`, `flow` and `ece`. The checker validates their parameters
  against contracts v0. A sentence `cue.state` must name one of `scene.states`, and `highlight`
  ids must exist in the scene.
- `illustrative: true` is required when the numbers are invented for teaching. The UI must label
  it ("Illustrative · not advice").

## `reflect` (optional tutor-mode handoff)

Either `{"graphRef": "<packId>/<graphId>"}` for an existing `kiki-tutor-graph/v0`, or a seed:

```jsonc
{"seed": {"problem": "Why was this a bad call?", "caseRef": "S-2",
          "metrics": [{"id": "sentiment", "label": "Market sentiment", "dim": "concept"}],
          "insights": [{"id": "vol-aware", "desc": "…", "metric": "sentiment"}],
          "misconceptionIds": ["M-…"],
          "hintLadder": [{"rung": "question", "say": "…"}, {"rung": "nudge", "say": "…"},
                         {"rung": "worked_step", "say": "…"}, {"rung": "answer", "say": "…"}]}}
```

A graph author turns the seed into 8–12 nodes. The seed keeps the graph on the same model,
misconceptions and rules as the lesson.

## `kiki-chapter-plan/v1` (one per request)

```jsonc
{"schema": "kiki-chapter-plan/v1", "planId": "LP-…", "domain": {…}, "scope": "chapter|module|topic|concept",
 "title": "…", "governingQuestion": "…", "canDo": "…",
 "request": {"kind": "syllabus|chapter_name|question|material|playbook", "text": "…", "sourceIds": []},
 "sources": [], "mece": {"dimension": "…", "rationale": "…", "outOfScope": []},
 "objectives": [], "groups": [{"id": "MOD-…", "order": 1, "title": "…", "governingQuestion": "…", "objectiveId": "O-…",
                               "mece": {…}, "conceptIds": []}],
 "concepts": [{"id": "…", "title": "…", "canonicalKey": "…", "groupId": "MOD-…", "prerequisiteIds": [],
               "requiredForPractical": false, "estMinutes": 12}],
 "route": [], "practical": null, "chapterTest": []}
```

Shapes:

- chapter: 2–5 groups;
- module or topic: 1 group;
- concept: 1 group with 1 concept.

Each group has 2–5 concepts (exactly 1 at concept scope). `chapterTest` is required only at
chapter scope when the policy defines one (10 MCQs in the student journey).

## Projections the checker emits (`--emit DIR`)

- `<conceptId>.pack-concept.json`: `{concept, terms, scenes}` in `kiki-pack/v0` shape. Placard
  text is the source-language sentences joined, with each term occurrence replaced by
  `[[term-id]]` (longest match first). Term `meaning` holds the source definition plus the
  target glosses, and `say` holds the target pronunciations.
- `<placard-id>.mixed-input.json` (only when `mixed-script-input/v1` is a consumer and `or` is
  a target): the backend pipeline input. The checker runs the real `validate_input` on it.
  The pipeline requires an HTTPS reference, so notes-only packets fail here until the contract
  grows a document-reference form.
