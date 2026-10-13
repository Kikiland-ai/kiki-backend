# Receiving-session runbook: install and verify BB8

## Mission

Set up the uploaded `bb8` directory as a skills-only plugin in the current
cloud environment. Do not reconstruct, request, import, or infer any prior
project context, user knowledge, chat history, account memory, or credentials.

The package is self-contained. Its `harness/` directory is runtime support for
the skills, not project context.

## Non-negotiable boundaries

- Do not search the surrounding workspace for old BB8 projects or knowledge.
- Do not create or populate a knowledge base during plugin setup.
- Do not copy authentication files, API keys, tokens, browser state, account
  configuration, logs, caches, or chat databases.
- Do not install unrelated skills found elsewhere in the workspace.
- Do not edit the packaged skill content except to repair a demonstrated
  packaging or path error, and report any such repair.
- Treat only the uploaded `bb8` plugin directory as setup scope.

## Now: locate and preflight the package

1. Locate the single directory named `bb8` that contains both:
   - `plugin.json`
   - `.codex-plugin/plugin.json`
2. Confirm both manifests have:
   - name: `bb8`
   - version: `0.2.2`
   - description: `Local-first executive thinking partner, planner, and capability router.`
3. Confirm `skills/` contains exactly these 22 directories:
   - `bb8`
   - `data-analysis`
   - `deep-research`
   - `design-critique`
   - `engineering`
   - `engineering-architecture`
   - `engineering-debugging`
   - `engineering-implementation`
   - `engineering-review`
   - `engineering-security`
   - `engineering-testing`
   - `experience-design`
   - `experiment-design`
   - `minto-communication`
   - `organise`
   - `problem-solving`
   - `product-design`
   - `product-discovery`
   - `product-strategy`
   - `prompt-design-engineering`
   - `strategic-storytelling`
   - `transcript-insights-tofu`
4. Confirm every listed directory contains `SKILL.md` with `name` and
   `description` YAML fields.
5. Resolve every relative Markdown link in each `SKILL.md`. Confirm its target
   exists inside the plugin package. Do not follow links outside the package.
6. Confirm there are no `.pyc`, `__pycache__`, credential, environment, vault,
   chat-history, or project directories in the package.
7. Confirm there are no absolute user-machine paths in the package.

Stop and report the exact mismatch if any preflight check fails. Do not silently
drop a skill or substitute a host-provided skill with the same name.

## Next: register the plugin

Choose the route matching the environment.

### Route A — OpenAI-hosted sandbox

The outer ZIP must contain exactly one top-level `bb8/` directory, and that
directory must contain `.codex-plugin/plugin.json`. Register the ZIP as one
entry in the new session's `environment.plugins` collection. Use the manifest's
exact name and description in the upload request. The host extracts and
registers the plugin automatically.

If this runbook is executing inside a session that has only received the ZIP as
a normal workspace file, explain that plugin capabilities are fixed when the
session is created. Prepare or identify the valid ZIP, then instruct the caller
to create a fresh session with it in `environment.plugins`; do not claim that
copying files into the current workspace activated the plugin.

### Route B — Self-hosted cloud sandbox

Place the complete plugin directory at an accessible stable path such as:

`/workspace/plugins/bb8`

Create a fresh agent session whose self-hosted environment includes the exact
plugin root in `capability_directories`, for example:

`/workspace/plugins/bb8`

Select the plugin root itself, not its parent and not `skills/`. The root must
contain `.codex-plugin/plugin.json`.

### Route C — Codex desktop under the separate account

If the target is the desktop app rather than an Agents API sandbox, expose the
plugin through a personal or repository marketplace, install it from the
Plugins Directory, restart the app when required, and test in a new chat. Do
not copy files directly into an internal cache version directory as the primary
installation method.

## Later: acceptance test in a fresh session

1. List the active plugin and confirm the identity is `bb8` version `0.2.2`.
2. List its discovered skills and compare them exactly with the 22-item list
   above.
3. Invoke BB8 with: `Use BB8 to frame a consequential decision in Now, Next,
   Later form and tell me which specialist skill you would route to.`
4. Verify that BB8:
   - acts as the coordinator;
   - uses the packaged harness;
   - names an appropriate packaged specialist;
   - does not claim access to prior projects, personal knowledge, or account
     memory;
   - does not invent a knowledge-root location.
5. Invoke one specialist directly, for example:
   `Use the problem-solving skill to structure a generic ambiguous problem.`
6. Report pass/fail for manifest discovery, 22-skill discovery, BB8 routing,
   direct specialist invocation, and context isolation.

## Completion report

Return a concise setup report with:

- installation route used;
- registered plugin root or hosted-upload status;
- plugin version;
- discovered skill count and any missing or extra skills;
- acceptance-test results;
- whether a fresh session is required;
- any blocker requiring user or administrator action.

Do not include or solicit project context in this report.
