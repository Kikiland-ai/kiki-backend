# Make BB8 selectable in ChatGPT

`@bb8` is the correct ChatGPT invocation style only when BB8 is installed and
selectable in that client's skill picker. Repository files and GitHub access
alone do not install the plugin in ChatGPT.

## ChatGPT desktop: local marketplace

The repository now contains `.agents/plugins/marketplace.json`, named
`kikiland-bb8` and displayed as **Kikiland BB8**. It contains exactly one plugin:
BB8, sourced from `./bb8` relative to the repository root. No unrelated plugin
or MCP connection is included. The skills-only package needs no service login.

On the computer where the desktop app runs, register the marketplace through
the supported CLI, using the machine's existing GitHub access for this private repo:

```sh
codex plugin marketplace add Kikiland-ai/Design-Thinking --ref main
```

Alternatively, open an up-to-date, trusted local checkout of this repository
as the desktop project so it can discover the repo marketplace directly.
Do not manually edit an internal plugin cache or copy another account's settings.

Restart the ChatGPT desktop app. Open the Plugins Directory, select **Kikiland
BB8**, and install **BB8**. Start a fresh Work chat, type `@`, and select BB8
from the picker. Merely typing the string `@bb8` cannot select an absent skill.

Verify the plugin identifies as BB8 0.2.2, exposes its 22 skills, and can frame
a generic decision using the packaged harness without prior context. This
task prepares the installation source; it does not modify the desktop user's
profile, install a plugin into that account, or prove UI registration succeeded.

## ChatGPT browser or a hosted session

A local desktop marketplace is not automatically a browser/workspace plugin
installation. BB8 must be installed through that workspace's supported plugin
management path before it can appear in `@` selection. Workspace publishing
is separate from GitHub organization repo provisioning and requires the
appropriate workspace role and product support.

For an Agents API hosted sandbox, follow the original runbook: create a fresh
session with the validated BB8 ZIP in `environment.plugins`. Uploading the ZIP
as a regular attachment does not register it. Do not translate that API field
into an invented browser menu option.

## Codex CLI or IDE

Open the updated repository checkout. Use `/skills` or `$bb8`; Codex's repo
skill discovery reads `.agents/skills/`. The `@` ChatGPT convention is not the
CLI convention. Restart Codex if new files have not appeared.

## Claude Code

Open the updated repository checkout and invoke `/bb8`. The project skill
wrapper is under `.claude/skills/`. This is separate from ChatGPT installation.

## Reference mode in a chat without BB8 installed

If the uploaded package is available to the assistant, request:

> Use BB8 from the uploaded package for this task. Read its canonical skill
> and harness, and state that this is reference mode rather than native activation.

The assistant can follow those instructions without an `@` picker entry. It
must not claim the plugin was installed, and cannot add a picker entry using
ordinary file edits in a running hosted session.

## Official references

- [ChatGPT versus Codex invocation](https://learn.chatgpt.com/docs/build-skills)
- [Local marketplaces and desktop installation](https://developers.openai.com/plugins/build/plugins)
