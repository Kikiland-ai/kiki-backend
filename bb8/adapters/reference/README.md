# Portable reference adapter

Requires Python 3.10 or newer and its standard library. No account, credential,
network, dependency installation, or model API is required.

Run from the BB8 repository root:

```sh
python adapters/reference/bb8.py list
python adapters/reference/bb8.py validate
python adapters/reference/bb8.py prepare \
  --task 'Review the specified change for correctness' \
  --skill engineering-review \
  --scope src/example.py \
  --mode read-only \
  --tool read \
  --reference harness/references/engineering-principles.md
```

`src/example.py` is an illustrative future task scope. The adapter does not
read it or require it to exist. It reads only BB8's packaged instruction files.
`list` reports packaged skills; it does not report native host discovery.
`validate` checks plugin identities, exact skill inventory, registry paths,
frontmatter, and all relative Markdown links in the packaged skills.

`prepare` prints a scoped task packet containing BB8 and the selected specialist
instructions. Give that packet to an existing IDE/CLI/chat agent using its
supported input mechanism. The host must already have the intended checkout,
appropriate tools, and authorization. No second plugin is installed.

For local edits, declare `--mode local-edit --tool edit`. Add `--tool exec` only
when the host provides command execution and the task authorizes relevant checks.
Tool declarations are caller statements, not permission grants or guarantees.
The adapter rejects traversal scopes, escaped or symlinked packaged resources,
unknown skills, and knowledge operations under the current restriction.

Only the coordinator and chosen specialist are reference-loaded. Add individual
references explicitly with repeatable `--reference`; do not load every skill.
Scope restrictions in the packet are instructions. Enforcement belongs to the
host sandbox and tool policy, so this adapter is not a security boundary.

This adapter prepares prompts, not model responses. It does not execute the
task, edit the application repo, create a session, or activate a native plugin.
Native BB8 remains available through the runbook's supported registration routes.
