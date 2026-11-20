# 0018 — Pedagogy packets: researched English source for translation, audio and canvas

Status: skill and checker implemented (`.claude/skills/kiki-pedagogy-packets/`, Codex wrapper in
`.agents/skills/`). Runner not built. 20 November 2026.

## Context

The ten saved C-AM packets never passed through the accepted translation pipeline: every
placard has `textMode: authored` and `provenance: authored_case_reused`. Their English and Odia
text was hand-authored in the kiki-web `data-model` case. The mixed-script pipeline itself
works on prepared English (the VCO live run and the held-out v2 run completed both text stages,
evidence `prototypes/mixed_script/evidence/2026-10-13/`). What was missing is the step that
produces that prepared English for an arbitrary chapter, topic or concept, plus the checks,
glossary and canvas specification that go with it.

## Decision

- A skill researches the concept (claim ledger with sources and confidence), models the
  learner (prerequisites, misconceptions), designs backwards from objectives, and writes
  `kiki-chapter-plan/v1` plus one `kiki-pedagogy-packet/v1` per concept.
- English is the source of truth. The packet's `teaching` block uses `lesson-ledger/v2`
  field names. Placards keep the case's four kinds. Each placard projects 1:1 to a
  `mixed-script-input/v1` that the backend's own `validate_input` accepts. Odia glosses and
  pronunciations are pending drafts that the pipeline glossary requires.
- Canvas widgets are declarative specs (≤3 controls, formulas in the ledger grammar,
  behaviour cases, `ideal_teaching_model`). The factory implements them as reviewed code.
  Packets never ship executable code.
- `scripts/check_packet.py` (standard library only) enforces structure and pedagogy lints,
  evaluates canvas behaviour cases, runs the real `validate_input`, and lints three
  post-translation failure modes of `validate_stage`: literals hidden inside ordinary words,
  digits in spoken forms, and spoken-term overlap.

## Consequences and open items

- A runner must still chain research → packet → checker → mixed-language job → TTS → canvas
  factory → ledger/case assembly → publication. Out of scope here.
- Notes-only packets have no HTTPS reference, which `mixed-script-input/v1` requires. The runner
  needs a document-reference form, or the contract needs a change.
- New canvas topics need the factory's scene contract to accept non-CAM concepts and units
  beyond `""/normalized/Hz/degree`.
- The authored C-AM-03 ledger cites a MathWorks page for the modulation index and
  overmodulation. That page (read 2026-11-20) covers DSB AM with an offset `k` and does not
  mention either. The worked example packet cites two university lecture decks instead.
