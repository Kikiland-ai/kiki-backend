<!-- BB8:BEGIN -->
## BB8

For consequential or multi-step work, read `bb8/AGENTS.md`, then use the
coordinator at `bb8/skills/bb8/SKILL.md` and `bb8/harness/system-prompt.md`.
Use the relevant engineering specialist for repo implementation, debugging,
review, or testing. Follow applicable repository instructions and the user's
explicit task scope. Execute authorized local work and report actual checks.

Codex discovery wrappers live in `.agents/skills/`; Claude Code wrappers live
in `.claude/skills/`, with `CLAUDE.md` importing these instructions. Load the
selected canonical skill and only the references it needs. Host tools perform
the work. Do not retrieve prior projects, chats, memory, vaults, or credentials.

Identify and read task-relevant files explicitly. Do not claim all files were
indexed or loaded. Discovery metadata is not an embedding index or native
hosted-plugin registration.

Check setup from the repository root:

```sh
python bb8/adapters/reference/bb8.py validate
python bb8/adapters/discovery/sync.py --check
python -B bb8/tests/test_reference_adapter.py
```
<!-- BB8:END -->

## Kiki backend context and implementation

Before substantive work, read `SETUP.md`, `context/README.md`, the source prototype directions and handoff, then the relevant v2 contracts. Use the source precedence rules; old mock UI and build-plan defaults do not supersede the latest confirmed journey or the user's current instructions.

Treat `context/design-thinking/` as a pinned source snapshot. Do not casually rewrite its documents or types as implementation progresses. Record new decisions in `docs/decisions/`, current work in `docs/plans/active.md`, and implement reconciled runtime schemas in `contracts/`. An explicit source refresh must update the source revision and file hashes together.

Implement small vertical slices with actual runtime validation. Maintain separate concept, terminology, English, and practical evidence. The student controls language and performs lab actions. GIF export retains an editable semantic scene. Mixed-language speech returns real timing cues. Image annotation and live screen annotation have separate targets/lifecycles. No mock implies a live provider/tool works.

Use `python scripts/verify-context.py`, BB8 checks, and the backend's actual test commands. Do not commit credentials or credit an AI in commit/PR messages. Update the active plan with what ran, what failed, and the exact next action at session end. Carry continuity through these files rather than assuming chat memory transfers.
