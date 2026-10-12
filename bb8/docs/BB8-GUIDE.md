# How to use BB8

For native plugin use, register BB8 with the target host, create a fresh session
where required, and verify discovery. For reference mode, use the included
`adapters/reference/bb8.py` loader and follow its README. Loading instructions
does not activate a native plugin.

## Begin a mission

Use plain language across hosts:

> Use BB8 to frame this decision in Now, Next, Later form. State assumptions,
> success criteria, and the packaged specialist you would route to. Use only
> this request; do not use prior chats, memory, vaults, or credentials.

Supply the decision or task and desired output. BB8 should clarify only what
would materially change the result, present a proportional plan, and continue
within your authorization. For a simple task, request the specialist directly.

## Choose a specialist

| Outcome | Skill |
|---|---|
| Frame, prioritize, coordinate | `bb8` |
| Diagnose an ambiguous problem | `problem-solving` |
| Investigate current external evidence | `deep-research` |
| Analyze supplied numbers or structured data | `data-analysis` |
| Build a clear executive narrative | `minto-communication` |
| Connect purpose, benefits, experience, and features | `strategic-storytelling` |
| Choose an engineering route | `engineering` |
| Architecture, implementation, debugging, review, testing, security | Corresponding `engineering-*` specialist |
| Choose a product route | `product-design` |
| Discover needs or choose product strategy | `product-discovery`, `product-strategy` |
| Design journeys, critique an artifact, test uncertainty | `experience-design`, `design-critique`, `experiment-design` |
| Extract evidence-backed transcript findings | `transcript-insights-tofu` |
| Knowledge ingestion and curation | `organise` is packaged; excluded under the current scope |

Examples:

> Use the problem-solving skill to structure a generic ambiguous problem.

> Use BB8 to compare a minimal host adapter with a standalone bundle port.
> Route the architecture tradeoffs to engineering-architecture and state
> which capabilities are actually available.

> Use engineering-review to evaluate only the change I explicitly provide.

Hosts supporting `$skill-name` may offer that shortcut. Plain-language invocation
is the portable convention; namespace and command syntax depend on the host.

## Continue work

For a multi-step task, ask BB8 to update a current-task mission plan using
`harness/plan-template.md`. To resume, explicitly supply that task plan and the
files in scope. Do not assume BB8 remembers earlier sessions. A mission plan is
a task handoff, not authorization to import personal history or create a vault.

## Check a result

Look for the objective, chosen route, visible evidence and uncertainty, concrete
Now / Next / Later actions, blockers, and an exact continuation point. Ask BB8 to
distinguish packaged capability from host discovery and successful invocation.
External research and execution require appropriate host tools and task scope.

## Use BB8 for actions inside a repository

BB8 supplies the workflow and routing. The host agent supplies access to the
checkout, file editing, command execution, and tests. A skills-only installation
does not itself supply a checkout, a shell, permissions, or repository access.

For future repo use, open the intended checkout in a capable host and register
BB8 separately. If this is the BB8 repository itself, put the drafted `AGENTS.md`
beside `skills/` and `harness/`. In another repository, merge a short BB8 entry
into that repository's existing `AGENTS.md`; keep its own conventions and nested
instructions. Use the registered skill in a native host. For reference mode,
the entry must point to a plugin root explicitly supplied to that host, rather
than assuming BB8's files are present inside the application repository.

Suggested application-repo instruction:

```markdown
## BB8 workflow
For consequential or multi-step tasks, use the registered BB8 coordinator.
For simple changes, use the relevant specialist directly when helpful.
Follow this repository's applicable instructions. Limit reads and edits to the
task's explicit scope; do not import history, memory, vaults, or credentials.
Present a proportional plan, execute authorized local changes, verify them,
and report the changed files, results, blockers, and exact next action.
If BB8 is not discovered, report that limitation rather than claiming it ran.
```

Example implementation request:

> Use BB8 to implement [desired behavior] within [explicit files or directory].
> Route through engineering-implementation. You may read and edit files within
> that scope and run the relevant local checks. Show the plan, make the smallest
> complete change, and report the diff and check results. Do not commit, push,
> publish, deploy, or access credentials.

Example debugging request:

> Use BB8 with engineering-debugging to investigate [provided failure] in
> [explicit scope]. Reproduce it, test the likely causes, fix the root cause,
> and run the relevant regression check. Report anything you cannot verify.

Example review request:

> Use engineering-review to review [specified diff or files]. Report actionable
> correctness and reliability findings with file locations. This is read-only.

The user supplies the future task's scope; BB8 does not reconstruct a repo from
account data or earlier conversations. Within that scope, BB8 reads applicable
instructions and relevant code, identifies the affected behavior, and reuses
the project's declared check commands. It does not invent commands or claim
tests passed when they were not run. If necessary files lie outside the allowed
scope, it identifies the precise missing dependency before expanding access.

Ordinary authorized local edits do not need repeated approval. Commits, pushes,
PR creation, and deployment depend on the user's request and host policy;
the examples above authorize local work only. If the host is read-only or lacks
a shell, BB8 should produce a plan or patch and report unperformed checks.

A useful action result states: what changed, why, the affected files, the actual
verification performed, unresolved risks, and the next action. For larger work,
update the explicitly authorized task plan so another session can continue.
These examples are documentation, not actions performed on an application repo.
