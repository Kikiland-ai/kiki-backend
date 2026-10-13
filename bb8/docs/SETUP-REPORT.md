> Historical 0.2.1 setup/port notes. The user-authorized 0.2.2 extension adds prompt-design-engineering; the current package has 22 skills. Use the current manifests, registry, and runbook for acceptance.

# BB8 setup report

- Route: A, hosted session registration handoff prepared.
- Hosted-upload status: normal workspace attachment; not registered or activated.
- Plugin version: 0.2.1 in both plugin manifests.
- Packaged skills: 21; missing 0; extra 0.
- Relative skill links: all 33 resolve within the plugin.
- Package files: 71; extracted bytes match the uploaded ZIP.
- Archive SHA-256: `bf5ceac9dbbadbc638961c9e70213985b1353d88914d7d38d6ab309715ff1180`.
- Context isolation during setup: pass; package-only inspection.
- Package repairs: none. Packaged content unchanged.
- Advisory: harness metadata version is 0.2.0; this differs from the plugin
  release version but is not a runbook identity mismatch. No change made.

| Fresh-session acceptance check | Result |
|---|---|
| Active plugin identity and version | Blocked: fresh registered session required |
| Exact 21 discovered skills | Blocked: no BB8 skills in current active catalogs |
| BB8 coordinator and packaged specialist routing | Blocked: plugin inactive |
| Direct problem-solving invocation | Blocked: plugin inactive |
| Runtime context isolation | Blocked: plugin inactive; setup isolation passed |

Fresh session required: yes. The runbook explicitly states that plugin
capabilities are fixed when a hosted session is created. No available tool in
this session accepts a local plugin archive for session registration.

Caller/administrator action: upload the validated original ZIP through the
session-creation interface as exactly one `environment.plugins` entry, using:

- Name: `bb8`
- Description: `Local-first executive thinking partner, planner, and capability router.`

The archive already has the required sole top-level `bb8/` directory and
`.codex-plugin/plugin.json`. Do not substitute a plugin-directory search result.

Then run:

> Use BB8 to frame a consequential decision in Now, Next, Later form and tell
> me which specialist skill you would route to.

> Use the problem-solving skill to structure a generic ambiguous problem.

Confirm coordinator behavior, packaged harness use, an appropriate packaged
specialist, no prior-project or memory claims, and no invented knowledge-root.
Record pass/fail for all five checks only after actual execution.

## Portable starter implementation

AGENTS.md, the usage guide, the adapter contract, and the reference loader are
in place in this separate repository copy. All 71 original files are unchanged.
The loader passes package validation and 11 local adapter/isolation tests.
It prepares instructions only; model execution, application-repo edits, native
activation, and cross-host behavioral acceptance have not been performed.
