# Start BB8 in a repository

This is a portable starter based on BB8 0.2.1, with the original 21 skills and
harness preserved. The added reference adapter is version 0.1.0.

1. Read [AGENTS.md](AGENTS.md) for coordinator and repository-action instructions.
2. Read [the usage guide](docs/BB8-GUIDE.md) for implementation, debugging,
   review, and task-continuation requests.
3. Choose native registration through [the original runbook](SESSION-SETUP-RUNBOOK.md)
   or document loading through [the reference adapter](adapters/reference/README.md).
4. Read [the adapter contract](adapters/CONTRACT.md) before adding a host bridge.

From this directory:

```sh
python adapters/reference/bb8.py validate
python adapters/reference/bb8.py prepare \
  --task 'Review the reference adapter for correctness' \
  --skill engineering-review \
  --scope adapters/reference/bb8.py \
  --mode read-only \
  --tool read \
  --reference harness/references/engineering-principles.md
```

The second command prints a task packet. Pass that output to an existing host
agent using its supported input mechanism. It does not execute a model or read
the scoped repository file. The host performs the authorized review.

For an implementation task, supply the desired behavior and explicit scope,
choose `engineering-implementation`, and use `--mode local-edit --tool edit`.
Declare `--tool exec` only if relevant checks are authorized and available.
The host must enforce scope and permissions; this loader is not a sandbox.

Hosted native activation still requires a fresh session. The original uploaded
ZIP is the validated registration artifact. This expanded starter adds local
integration material and has not passed native fresh-session behavioral tests.

No account, credential, knowledge vault, prior-chat, or memory setup is needed.
