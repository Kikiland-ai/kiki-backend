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
