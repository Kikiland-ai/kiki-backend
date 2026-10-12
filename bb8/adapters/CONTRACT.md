# BB8 host adapter contract

Adapter version: 0.1.0. Underlying BB8 plugin identity: 0.2.1.

The core source is the unchanged `skills/` and `harness/`. Adapters must separate:

1. Packaged inventory: files exist and pass validation.
2. Reference loading: the host receives selected BB8 instructions as documents.
3. Native discovery: the host actually exposes BB8 and the expected skills.
4. Execution: a host agent actually invokes tools and produces a result.
5. Acceptance: observed behavior passes the fresh-session runbook checks.

Do not promote one state to another without evidence.

Inputs are the current request, explicit file scope, action mode, available host
tools, and selected capability. Previous projects, chats, account memory,
vaults, and credentials are excluded. Additional context must come from the
user's explicit task scope rather than automatic discovery.

Outputs are the task packet or execution result, selected route, evidence,
assumptions, verification outcomes, blockers, and continuation point.

The host is responsible for tool exposure, permission enforcement, current-task
instruction precedence, sandboxing, and command execution. BB8 is responsible
for framing, routing, specialist procedures, and result coherence.

The reference adapter implements inventory validation and scoped prompt
assembly. The discovery adapter generates Codex and Claude Code repository
wrappers and a resource catalogue. The provisioner installs these files in
explicitly configured new organization repos. Model execution, native hosted
plugin registration, organization App activation, and runtime cross-host
behavioral equivalence require the relevant host or administrator.
