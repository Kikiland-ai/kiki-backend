# Packet contract

Two documents. Both are UTF-8 JSON. Ids use `[A-Za-z0-9][A-Za-z0-9_.-]{0,79}` (the
mixed-script pipeline's id rule). Concept ids follow the ledger style (`C-AM-03`); placard ids
`CARD-<concept-suffix>-<kind>`; sentence ids `<placard-id>.s<n>`.

## `kiki-concept-packet` → downstream map

| Packet field | Consumed by | As |
|---|---|---|
| `placards[].sentences` + `terms`/`usesTerms` + `research.sources` | mixed-script pipeline | one `mixed-script-input/v1` per placard (projection below) |
| `placards[].title.en/body` (joined sentences) | kiki-web `learning-case/v1` | `Placard.title.en`, `Placard.body.en` (Odia filled by the pipeline) |
| `teaching.*`, `objectives`, `terms`, `learner.*` | kiki-web `lesson-ledger/v2` | `Concept`, `Objective[]`, `Term[]` (same field names) |
| `visual` | ledger `explanation.modalities.textImage.visual`; canvas `visualBrief` | static image/SVG brief |
| `canvas` | canvas factory | widget spec → scene + trusted model + behaviour tests |
| `teaching.checks` + `chapter-plan.chapterTest` | `AssessmentDefinition` | concept (5, 60%) / chapter (10, 80%) |

## `kiki-pedagogy-packet/v1` (one per concept)

```jsonc
{
  "schema": "kiki-pedagogy-packet/v1",
  "packetId": "PKT-C-AM-03-1",
  "createdAt": "2026-11-20T00:00:00Z",
  "scope": {
    "lessonPlanId": "LP-ANALOG-MODULATION", "broadConceptId": "BC-AM-2",
    "conceptId": "C-AM-03", "order": 3, "canonicalKey": "conventional-am-envelope",
    "title": "Conventional AM, envelope and modulation index",
    "subjectProfileId": "electronics", "hasPractical": true
  },
  "status": {"review": "draft", "scientific": "pending", "nativeOdia": "pending", "pronunciation": "pending"},

  "research": {
    "governingQuestion": "…",
    "sources": [{"id": "S-1", "origin": "textbook|student_notes|syllabus|past_paper|experiment_sheet|teacher|curated",
                 "tier": 1, "label": "…", "url": "https://…", "locator": "§4.2"}],
    "claims": [{"id": "CL-…", "kind": "…", "text": "…", "sourceIds": ["S-1"], "confidence": "high|moderate|low", "check": "…"}],
    "outOfScope": ["…"],
    "openQuestions": ["…"]
  },

  "learner": {
    "prerequisiteIds": ["C-AM-02"],
    "externalPrerequisites": [{"title": "…", "level": "school|earlier_course", "canonicalKey": "…"}],
    "troublesome": "why this concept is hard (element interactivity, counter-intuitive part)",
    "misconceptions": [{"id": "M-AM-03-1", "statement": "…", "correction": "…",
                        "basis": "documented|inferred", "sourceIds": [], "reasoning": "…", "faultType": "Wrong assumption"}]
  },

  "objectives": [{"id": "O-AM-03", "statement": "Interpret … and calculate …", "bloom": "apply",
                  "parentId": "O-AM-G2", "ownerId": "C-AM-03"}],

  "terms": [{"id": "T-AM-03-2", "term": "envelope", "definition": "…", "aliases": [], "symbol": null, "unit": null,
             "ownerConceptId": "C-AM-03", "spoken_en": "envelope",
             "glosses": {"or": "draft"}, "pronunciations": {"or": "draft"}, "review_status": "pending"}],
  "usesTerms": [ /* same shape, copied from the owning packet; ownerConceptId ≠ this concept */ ],

  "teaching": {
    "canDo": "…", "keyIdea": "one sentence",
    "explanation": {"text": "60–140 words", "defaultModality": "textImage",
                    "walkthrough": [{"target": "phrase in text", "mark": "sweep|marker|lens|connect|circle",
                                     "dim": "concept|words|english|lab", "say": "narration about the target"}]},
    "example": {"title": "…", "scenario": "…", "takeaway": "…", "sourceIds": ["S-1"]},
    "workedQuestion": {"id": "W-AM-03", "type": "numerical", "marks": 2, "prompt": "…",
                       "modelAnswer": ["line", "line"], "rubric": [{"criterion": "…", "marks": 1, "objectiveId": "O-AM-03"}],
                       "examVocabulary": ["T-AM-03-3"]},
    "selfExplainPrompt": "Why …?",
    "checks": [{"id": "Q-AM-03-1", "type": "mcq", "dimension": "concept", "prompt": "…",
                "options": ["…"], "answer": "…", "distractorRationale": {"<option>": "M-…|error: sign slip"},
                "explanation": "why right + why the tempting wrong option is wrong",
                "objectiveIds": ["O-AM-03"], "difficulty": 1, "claimIds": ["CL-…"]}],
    "examSignal": {"basis": "none", "askedIn": 0, "outOf": 0, "note": "No past papers supplied."},
    "estMinutes": 12
  },

  "placards": [{
    "id": "CARD-AM-03-definition", "kind": "definition",
    "title": {"en": "Definition"},
    "sentences": [{"id": "CARD-AM-03-definition.s1", "english": "…",
                   "term_ids": ["T-AM-03-1"], "literals": [{"text": "mu", "spoken": "mu"}],
                   "claimIds": ["CL-…"], "refutesMisconceptionIds": []}],
    "visualRef": "explanation", "canvasState": {"mu": 0.5}
  }],

  "visual": {"kind": "waveform", "description": "what to draw", "alt": "…", "sourceIds": ["S-1"]},
  "canvas": { /* widget spec below, or null */ },
  "canvasNullReason": "required when canvas is null",
  "handoff": {"audioUnit": "placard", "speechNotes": ["say 'mu' as 'mu', not 'micro'"]}
}
```

Rules the checker enforces: exactly four placards in the order definition, concept, application,
recap; 1–10 sentences each; sentence `term_ids` equal **exactly** the glossary terms that occur
in the sentence (case-sensitive, whole-word, same rule as `pipeline.py`); each literal is a
substring of its sentence; all claim/source/term/misconception/objective references resolve.

## Canvas widget spec (`canvas`)

A canvas is a **small controllable widget**: 1–3 controls, a trusted analytic model, readouts
and views, bound to placards. The packet describes it declaratively. The factory implements it
as reviewed code and pins conformance cases. Existing CAM scenes (`cam-interactive-scene/v1`)
are pinned to their concept and model hash, so a new topic is `kind: "new"`.

```jsonc
{
  "artifactId": "CANVAS-C-AM-03",
  "status": "proposed",
  "reusesPinnedScene": "C-AM-03",          // or null for new topics
  "kind": "am",                              // existing scene kind, or "new"
  "interaction": "parameter_sweep",          // ledger Interactive kinds
  "purpose": {"objectiveIds": ["O-AM-03"], "misconceptionIds": ["M-AM-03-1"],
              "insight": "what the student should notice by moving the control"},
  "controls": [{"name": "mu", "label": "Modulation index", "min": 0, "max": 1.5, "step": 0.1, "default": 0.5, "unit": ""}],
  "model": {
    "assumptions": ["ideal single-tone message", "normalised carrier amplitude Ac = 1"],
    "equations": [{"text": "s(t)=Ac[1+mu*cos(2*pi*fm*t)]cos(2*pi*fc*t)", "spoken": "…"}],
    "outputs": [{"name": "envMin", "label": "Minimum envelope", "unit": "normalized", "formula": "1-mu", "decimals": 2}],
    "views": [{"kind": "trace|spectrum|flow|table|phasor", "description": "…"}]
  },
  "behaviorCases": [{"inputs": {"mu": 0.5}, "expect": {"envMin": 0.5}, "tolerance": 0.001,
                     "observation": "envelope stays above zero"},
                    {"inputs": {"mu": 1.2}, "expect": {"envMin": -0.2}, "tolerance": 0.001,
                     "observation": "envelope crosses zero", "showsMisconception": true}],
  "placardStates": [{"placardId": "CARD-AM-03-concept", "controls": {"mu": 1.2}, "cue": "watch the envelope cross zero"}],
  "mustShow": ["…"], "mustNotImply": ["…"],
  "claim": "ideal_teaching_model",
  "alt": "text alternative for the whole widget"
}
```

- Controls: unique `[a-zA-Z][a-zA-Z0-9]*` names, `min ≤ default ≤ max`, `step > 0`; units from
  `"" | normalized | Hz | degree | V | s | rad` (the current scene contract allows only the first four;
  others require a factory contract change, and the checker warns).
- Formulas use the ledger grammar: numbers, input names, earlier output names,
  `+ - * / ^ ( )`, `exp log sqrt abs min max pi`, plus `sin cos tan` (canvas only; the ledger
  `parameter_sweep` grammar has no trigonometry, so the checker warns).
- 3–7 behaviour cases, including the default and at least one case that makes the
  misconception fail. The checker evaluates every formula against them.

## `kiki-chapter-plan/v1` (one per request)

```jsonc
{
  "schema": "kiki-chapter-plan/v1",
  "lessonPlanId": "LP-…", "scope": "chapter|topic|concept", "title": "…",
  "governingQuestion": "…", "canDo": "…",
  "request": {"kind": "syllabus|chapter_name|question|material", "text": "…", "sourceIds": ["S-1"]},
  "sources": [ /* same shape as packet sources */ ],
  "mece": {"dimension": "…", "rationale": "…", "outOfScope": ["…"]},
  "objectives": [ /* apex (parentId null) + one per broad concept */ ],
  "broadConcepts": [{"id": "BC-…", "order": 1, "title": "…", "governingQuestion": "…", "objectiveId": "O-…",
                     "mece": {"dimension": "…", "rationale": "…", "outOfScope": []}, "conceptIds": ["C-…"]}],
  "concepts": [{"id": "C-…", "title": "…", "canonicalKey": "…", "broadConceptId": "BC-…",
                "prerequisiteIds": [], "requiredForPractical": false, "estMinutes": 12}],
  "route": ["C-…"],
  "practical": {"id": "P-…", "title": "…", "requiredConceptIds": ["C-…"]},   // or null
  "chapterTest": [ /* exactly 10 mcq CheckQuestions, each with conceptIds */ ]
}
```

## Projection to `mixed-script-input/v1` (what a runner submits)

For each placard:

```json
{
  "schema": "mixed-script-input/v1",
  "id": "<placard id>",
  "title": "<scope.title> — <placard title.en>",
  "source": {"kind": "adapted_reference", "review_status": "pending",
             "references": [{"title": "<source label>", "url": "<https url>"}]},
  "mix": {"support_language": "or", "script": "Odia", "level": "odia-led-english-terms"},
  "glossary": [{"id": "<term id>", "english": "<term>", "meaning_or": "<glosses.or>",
                "pronunciation_or": "<pronunciations.or>", "spoken_en": "<spoken_en>", "review_status": "pending"}],
  "sentences": [{"id": "…", "english": "…", "term_ids": ["…"], "literals": [{"text": "…", "spoken": "…"}]}]
}
```

- `references` are the HTTPS sources cited by that placard's claims. If none has a URL (for
  example only student notes), the projection fails and the checker reports it. Notes-only
  packets need the runner to attach a document reference, which is an open contract gap.
- `glossary` is the union of `terms` and `usesTerms` that occur in the placard. A term whose
  English text contains another term (for example "modulation index" ⊃ "modulation") is
  allowed. Each counts by its own whole-word occurrences, which is why `term_ids` must list
  both.
- The pipeline currently runs one fixed Odia mix level. The student proficiency pair
  is applied by the runner/job, not the packet.
