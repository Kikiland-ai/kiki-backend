# Session handoff: pedagogy packets skill

20 November 2026 · branch `feat/pedagogy-packets-skill` (from `main` at `c51b654`) ·
decision [0018](../decisions/0018-pedagogy-packets-skill.md)

## Why this exists

Kiki needs to take any chapter, topic or concept, research it in depth, and produce
digestible packets that the backend's existing translation → speech pipeline and the
concept-canvas factory can run on. Until now that input was hand-authored. All ten saved C-AM
packets carry `textMode: authored` / `provenance: authored_case_reused`. Their Odia came from
the kiki-web `data-model` case, not from `prototypes/mixed_script`. The pipeline itself does
work on prepared English: the VCO live run and the held-out v2 run completed both text stages
(evidence `prototypes/mixed_script/evidence/2026-10-13/`). This session built the skill that
produces that prepared English. The user scoped the runner out for now.

## What was built

| Path | Purpose |
|---|---|
| `.claude/skills/kiki-pedagogy-packets/SKILL.md` | Canonical skill: workflow, outputs, boundaries |
| `.claude/skills/kiki-pedagogy-packets/references/pedagogy-principles.md` | Learning-science evidence (verified 2026-11-20) → packet rules, with confidence labels |
| `.../references/research-protocol.md` | Research branches, source order, claim ledger, misconception mining, chapter mapping |
| `.../references/packet-contract.md` | `kiki-pedagogy-packet/v1`, `kiki-chapter-plan/v1`, canvas widget spec, projection to `mixed-script-input/v1` |
| `.../references/authoring-rules.md` | Placard roles, translation- and audio-safe sentences, glossary, MCQs, canvas design |
| `.../references/quality-gates.md` | Review checklist and anti-patterns found in earlier content |
| `.../scripts/check_packet.py` | Standard-library checker; imports the real `validate_input` |
| `.../templates/C-AM-03.packet.json` | Complete worked example that passes the checker |
| `.agents/skills/kiki-pedagogy-packets/SKILL.md` | Codex discovery wrapper pointing to the canonical skill |

## How it connects downstream

- **Translation and audio.** Each placard projects 1:1 to `mixed-script-input/v1` (1–10
  sentences, glossary, protected literals with spoken forms). The checker runs the backend's
  `validate_input` on every projection. It also lints three failures that `validate_stage`
  would raise after translation: a literal hidden inside an ordinary word (`mu` in "maximum"),
  digits in spoken forms, and spoken-term overlap. Odia glosses and pronunciations are pending
  drafts because the pipeline glossary requires them.
- **Ledger and case.** The packet's `teaching` block uses `lesson-ledger/v2` field names
  (kiki-web `data-model/types/content.ts`). Placards keep the `learning-case/v1` kinds:
  definition, concept, application, recap. Assembly into a ledger has not been built.
- **Canvas factory.** A declarative widget spec: ≤3 controls, outputs as formulas in the ledger
  grammar, 3–7 behaviour cases that the checker evaluates, placard states, `mustNotImply`,
  `claim: ideal_teaching_model`. Never executable code. Existing CAM scenes stay pinned to
  their model hash.

## Verification performed

Run with the backend venv (`python` on the authoring machine was a Microsoft Store stub):

```sh
.venv/Scripts/python.exe -X utf8 -B .claude/skills/kiki-pedagogy-packets/scripts/check_packet.py \
  .claude/skills/kiki-pedagogy-packets/templates/C-AM-03.packet.json --emit-mixed-inputs <dir>
```

- Worked example: PASS, 0 errors, 0 warnings. 4 placards, 16 sentences, 8 checks, 5+4 terms,
  canvas. Four `mixed-script-input/v1` files emitted, each accepted by `validate_input`.
- Eleven seeded defects were each caught: wrong term ids (also rejected by the backend),
  literal inside a word, digit in a spoken form, term speech inside a literal's spoken form,
  missing distractor rationale, four MCQs, no refutation sentence, low-confidence claim,
  wrong canvas expectation, prerequisite cycle, route order.
- `scripts/verify-context.py`: PASS (130 source files).
- `bb8/adapters/discovery/sync.py --check`: FAIL on `bb8/adapters/discovery/index.json`. It
  fails identically with the new skill removed, so the failure predates this session.
- Not run: translation, TTS, canvas rendering, ledger `validate.js`, any live provider call.

## Findings to act on

- The authored C-AM-03 ledger cites MathWorks "Analog Passband Modulation" for the modulation
  index and overmodulation. That page covers DSB AM with an offset `k` and mentions neither.
  The example packet cites uOttawa ELG3175 (Conventional AM) and UMD Tretter Ch. 5 instead.
- Anti-patterns in the authored C-AM content: joke distractors, walkthrough narration
  unrelated to its target, one-line application placards, predict answers copied from
  definitions. These are now encoded in `quality-gates.md`.

## Open contract gaps

1. Notes-only packets have no HTTPS reference, which `mixed-script-input/v1` requires. The
   runner needs a document-reference form, or the input contract needs a change.
2. New-topic canvases need the factory to accept non-CAM concepts and units beyond
   `""/normalized/Hz/degree`.
3. The pipeline still runs one fixed mix level. The student proficiency pair belongs to the job.

## Exact next action

Design and build the runner: chapter request → skill (research + packets) → checker → one
mixed-language job per placard → TTS → canvas factory → ledger/case assembly with
`validate.js` → media publication through the existing adapter. Trial it on one concept that
is not in the C-AM set, end to end, with real provider calls.
