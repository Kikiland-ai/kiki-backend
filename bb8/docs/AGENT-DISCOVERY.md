# Claude Code and Codex discovery

For ChatGPT `@bb8`, follow [the plugin installation guide](CHATGPT-INSTALL.md).
The repository marketplace at `.agents/plugins/marketplace.json` exposes only
BB8 for supported local clients to install; it does not install itself into
a running hosted chat. ChatGPT uses `@` selection, Codex CLI/IDE uses `/skills`
or `$bb8`, and Claude Code uses `/bb8`.

The original BB8 skills and harness remain unchanged. Small generated project
skills expose their names and descriptions in each host's discovery location.

| Surface | Files | Behavior |
|---|---|---|
| Codex instructions | Root `AGENTS.md` | Repository guidance under Codex's instruction rules. |
| Codex skills | `.agents/skills/<name>/SKILL.md` | Metadata discovery; body loads when selected. |
| Claude instructions | Root `CLAUDE.md` with `@AGENTS.md` | Imports the shared instructions. |
| Claude skills | `.claude/skills/<name>/SKILL.md` | Automatic relevance selection or `/name`. |
| Canonical resources | `bb8/skills/`, `bb8/harness/` | Wrapper points to original skill and its references. |

Wrappers are ordinary files, so Windows clones need no symlink support. They
are generated from canonical metadata and do not install another plugin.
All 21 names remain the same. Knowledge operations remain excluded; `organise`
is not implicitly enabled by the generated host metadata.

## Indexing and integrity

`bb8/adapters/discovery/index.json` lists 21 skills, their host entrypoints, and
hashes for all 71 original package files. It is a deterministic catalogue,
not an embedding index or evidence that an agent read every file. Repository
files cannot force a proprietary host index or full-context loading.

Instruction loading, skill discovery, relevant file reads, search indexing,
and native hosted plugin registration are separate states. Read the selected
skill and task-relevant files; avoid loading every skill into every session.

```sh
python bb8/adapters/discovery/sync.py --write
python bb8/adapters/discovery/sync.py --check
python bb8/adapters/reference/bb8.py validate
python -B -m unittest discover -s bb8/tests -p 'test_*.py' -v
```

The generator refuses unmanaged same-name conflicts and symlinked destinations.
CI checks missing or stale wrappers and resource hashes. These are file checks,
not runtime client acceptance.

## Client acceptance

Open a fresh session in the trusted checkout. For Claude Code, use `/memory`
to confirm root CLAUDE.md and its imported AGENTS.md, inspect the skill menu,
and invoke `/bb8`. For Codex, inspect the skill selector and invoke `$bb8` or
request BB8 explicitly. Confirm the selected skill's repository path; personal
or managed same-name skills may take precedence or appear alongside it.

Ask BB8 to frame a generic consequential decision in Now, Next, Later form and
name its canonical skill file and packaged specialist. Supply no prior context.
Then invoke engineering-review on one explicitly supplied file and confirm
the host reads that file and the canonical review instructions. Also verify
discovery when starting in a nested directory. If unavailable, check workspace
trust, client version, disabled skills, and excluded project settings.

Claude Code is not installed in this execution environment. A Codex binary is
present, but no model session or account configuration was opened. Actual
client loading remains an acceptance step.

## Official references

- [Codex skills](https://learn.chatgpt.com/docs/build-skills)
- [Codex instructions](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Claude instruction imports](https://code.claude.com/docs/en/memory)
