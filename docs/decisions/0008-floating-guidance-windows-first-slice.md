# Floating Kiki windows: first-slice choices

17 October 2026. User decisions on the open choices in the [floating guidance window handoff](../handoffs/floating-guidance-windows.md) §13. They shape the first build slice; they do not authorize implementation or deployment by themselves.

## Decisions

| Question | User's choice | Consequence |
| --- | --- | --- |
| Layout | One combined dock that can split into two windows | One window manager. The default is a single Kiki dock with Guide and Screen context sections; the student can split them into two movable windows and re-dock. |
| Controls without opening the tracker | Pause is necessary; display controls, help and open tracker also make sense | First slice includes move, minimize/restore, reset, split/dock, expandable details, open tracker and pause/resume. Pause/resume goes through the reader's existing revision-checked lab action (`worker/lab.js` pause/resume); the window shows the paused state only after the authoritative snapshot arrives. |
| Re-injection after MATLAB reload | Add a host permission | Add `https://matlab.mathworks.com/*` to the extension's host permissions. Keep the trusted reader allowlist; no `<all_urls>`. A reload re-injects windows, but the live binding is re-established explicitly, never resurrected from cache. |
| Hosted test surface | Make a test plan to iterate quickly now and formalise later | See the [fast-iteration test plan](../plans/floating-guidance-test-plan.md): local loops with zero model calls first; hosted surface and release build are chosen at formalisation. |

## Help (confirmed)

"Help" in the first slice is the expandable Where / How / Settings / Expected result / Why panel plus the authored already-done help, with responses still on the tracker. Free-text or voice help inside the window is deferred. The user confirmed this reading.

## Base

Runtime work starts from `baseline/screen-reader-v1` at `7c986df`. PR #1 merged on 15 October, and that commit has the same tree as the handoff's pre-drawing donor `ae234dc`. The stopped drawing integration is not merged into the new branch.
