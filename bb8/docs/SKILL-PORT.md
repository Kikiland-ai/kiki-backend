# Portable skill port

Use the existing `skills/bb8/SKILL.md` as the coordinator entrypoint and retain
all 21 specialist/family skills with their exact names. The recommended first
port is a host adapter around the existing suite, with no content rewrites.

## Current layout

```text
bb8/
  AGENTS.md                  # repository entrypoint
  plugin.json                # original portable manifest
  .codex-plugin/plugin.json  # original Codex manifest
  skills/                    # original 21 skills and references
  harness/                   # original shared runtime guidance
  adapters/                  # contract and working reference loader
  docs/                      # usage and rollout documentation
```

This separate repository copy adds instructions, documentation, and a reference
adapter. All original package files remain byte-identical. The uploaded archive
remains the validated native installation artifact for the current setup.

## Portable contract

Inputs: current request, explicitly allowed current-task files, constraints,
actual discovered capabilities, tool permissions, and an optional current-task
plan. Prior chats, account memory, vaults, credentials, and unrelated repository
context are excluded under the current scope.

Outputs: objective, success criteria, Now / Next / Later plan, selected specialist,
execution result, evidence, blockers, and a plain-file continuation handoff.

The host adapter must:

1. Resolve the plugin root explicitly and discover `skills/*/SKILL.md` without
   traversing other directories for context. Read name/description frontmatter.
2. Preserve exact skill IDs and report unavailable skills. Never replace them
   with host skills merely because their names match.
3. Load only the coordinator and relevant specialist references.
4. Bridge available file, search, plan, and tool functions to host APIs.
   Missing tools restrict execution; they need not prevent planning.
5. Gate routing on both packaged registry status and host exposure. Separately
   report tool limitations and policy restrictions.
6. Apply instruction precedence and approved scope before every tool action.
7. Store optional current-task handoffs as ordinary files, without a knowledge
   store, proprietary memory requirement, or account lookup.

## Host strategies

| Host | Integration approach |
|---|---|
| OpenAI hosted | Register the unchanged ZIP in a fresh session's `environment.plugins`. |
| Self-hosted Agents environment | Register the plugin root itself in `capability_directories`; create a fresh session. |
| Codex desktop | Expose through a personal/repository marketplace, install through Plugins Directory, and test in a new chat. |
| Other IDE or CLI | Add a thin host instruction pointer to `AGENTS.md` and implement supported skill/tool discovery. |
| Chat with document loading | Explicitly load the coordinator and selected references; report reference mode, not native plugin activation. |

If a host requires standalone skill bundles, generate derived bundles in a
separate build directory, include every required harness/reference resource,
rewrite links only in that derived output, and validate them. Keep the source
package unchanged. Document that transformation before releasing a new version.

## Port acceptance

Verify exact 21-skill inventory, valid resource paths, unavailable-capability
fallback, direct specialist use, scoped file access, and BB8 routing. Run the same
generic prompts on at least two selected hosts. Require comparable mission
structure, specialist selection, and isolation; prose need not be identical.
The reference adapter is implemented and locally tested. It prepares scoped
instruction packets without model or tool execution. Native host adapters and
cross-host behavioral equivalence remain pending target-host availability.
