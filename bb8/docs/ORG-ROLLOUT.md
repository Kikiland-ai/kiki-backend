# BB8 in every new Kikiland-ai repository

Organization App installation and activation have not been performed or
verified by this setup. The code is ready for an administrator's normal rollout.

## Included implementation

- `.github/workflows/bb8-org-bootstrap.yml`: manual runs and roughly half-hourly reconciliation. GitHub schedules can be delayed.
- `bb8/provisioning/bootstrap.py`: guarded, repeatable repository bootstrap.
- `bb8/provisioning/config.json`: organization, creation cutoff, write policy, and controller exclusion.
- `.github/workflows/bb8-check.yml`: package, discovery, and test validation.
- `bb8/adapters/discovery/sync.py`: 22 wrappers per host and resource catalogue.

The scheduled job runs only when `BB8_BOOTSTRAP_ENABLED=true`. It restricts
work to Kikiland-ai repos accessible to the configured installation and created
at or after the cutoff in config.json. It does not backfill older repos. A
manual run can target one explicit repo, with dry run selected by default.

The source is the controller commit checked out by that run. The provisioner
copies only the starter and validation workflow. It reads target tree metadata
and existing AGENTS.md, CLAUDE.md, and the bootstrap marker to preserve instructions
and check conflicts. It does not import application content or historical context.

## Writes and completion

The default is a normal fast-forward commit to the default branch, without
force push. If branch rules block it, one bootstrap PR is opened. Conflicts,
read-only repos, pending PRs, and retries are reported as incomplete and make
the run fail visibly. PRs must merge before BB8 appears on the default branch.
No branch protections or organization rulesets are bypassed.

An empty repo receives an initialization marker commit, then the bundle.
For BB8 to be present in the first commit, use a dedicated template.

Completed installs have `.bb8-bootstrap.json` with plugin version, source
revision, and bundle digest. Repeated scans leave them alone. Existing unmanaged
BB8 files or conflicting wrappers are preserved and flagged. This is first-time
bootstrap; upgrades require a separate reviewed update policy.

## Administrator activation

Install an approved GitHub App on all intended Kikiland-ai repos, including
future repos, with Metadata read, Contents write, Pull requests write, and
Workflows write permissions. A selected-repositories installation cannot
automatically cover future repos.

The controller uses administrator-managed runtime identity configuration through
`BB8_APP_CLIENT_ID` and `BB8_APP_PRIVATE_KEY` in normal GitHub settings.
These are code references; no credential values or account state were requested
or inspected in this task.

1. Arrange the approved App installation and controller runtime identity.
2. Review config.json's creation cutoff and direct-write policy.
3. Set the controller variable `BB8_BOOTSTRAP_ENABLED=true`.
4. Run **BB8 organization bootstrap** against a designated new test repo with dry run enabled; review its result, then apply.
5. Confirm the commit, marker, 22 wrappers per host, and validation workflow. Test empty and protected repos too.
6. Allow scheduled reconciliation and monitor failures or pending PRs.

This session has no tool to install an organization App or configure its identity.
Do not paste keys or tokens into this chat. Activation requires the administrator
workflow above, rather than a claim that pushing files made automation live.

## Dedicated template

Build from a reviewed source checkout. Replace COMMIT_SHA with its full reviewed
40-character commit SHA:

```sh
python bb8/provisioning/bootstrap.py package \
  --source-revision COMMIT_SHA \
  --output bb8-repo-starter.zip
```

This uses local files only. The archive includes shared instructions, BB8,
both hosts' discovery, a complete bootstrap marker, and the validation workflow.
It excludes the organization controller workflow and refuses to overwrite an
existing output archive.

Put those files in a dedicated org repo marked as a GitHub template. Use that
template to create repos. Do not turn the application-bearing Design-Thinking
repo into the generic template. Template changes do not update older repos.
Activated reconciliation catches other creation paths after the cutoff.

## Discovery is separate

Supported Claude Code and Codex clients can discover the repo wrappers after
checkout. This does not install a native hosted-session plugin or force a code
search index. Follow [client discovery acceptance](AGENT-DISCOVERY.md).

## Official references

- [GitHub App token action](https://github.com/actions/create-github-app-token)
- [Template repositories](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-template-repository)
- [Scheduled workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
