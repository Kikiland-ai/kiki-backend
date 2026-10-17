# Floating Kiki windows — fast-iteration test plan

17 October 2026, Asia/Kolkata. Working test plan for the first floating-window slice described in the [handoff](../handoffs/floating-guidance-windows.md). The user asked for a plan that lets us **iterate quickly now and formalise later**. It favours short local loops with zero model calls and zero deployments; the full acceptance matrix, CI wiring and published contract come at formalisation. No window code exists yet; nothing here claims a check has passed.

## 1. Decisions this plan tests

Recorded in [ADR 0008](../decisions/0008-floating-guidance-windows-first-slice.md):

1. **Layout:** one combined Kiki dock that the student can split into two windows (Guide and Screen context) and re-dock.
2. **Controls in the first slice:** move, minimize/restore, reset position, split/dock, expand details (help), open tracker, and **pause/resume**. Pause/resume is an authoritative lab mutation routed through the reader's existing revision-checked lab action; every other control is local display state.
3. **Permissions:** add a `https://matlab.mathworks.com/*` host permission so windows come back after a MATLAB reload without another popup click. Still no `<all_urls>`.
4. **Testing:** this plan.

Confirmed by the user: "help" in the first slice means the expandable Where / How / Settings / Expected result / Why panel plus the authored `already_done_help`, and **Open tracker** for responses. Free-text or voice help inside the window is deferred.

## 2. Base and build

- Runtime branch: `experiment/floating-guidance-bubbles` from `baseline/screen-reader-v1` at `7c986df` (same tree as donor `ae234dc`; PR #1 merged). Port two small fixes first and test them alone: `runtime.capture_active` in `committedProjection`, and browser accepted-observation retention ("Earlier accepted view").
- Reader: `prototypes/json_stream_site`. Rebuild the Worker bundle after any worker change: `node scripts/build.mjs`. `worker/index.js` and `dist/` are generated.
- Extension: new window adapter, proposed under `prototypes/floating_guidance/`. Reuse from `prototypes/screen_writing/shared_tab/` only: popup start/tab binding, Capture Handle, sender classification, closed-shadow host with re-attach, sequence high-water, double-rAF paint confirmation, `restore()`. Leave the SVG op compiler, 8-second TTL, full-viewport invalidation listeners, signed frame binding and probe-marker mask behind.
- **Dev manifest variant:** the shipped bridge only matches the two hosted reader origins. A dev build adds `http://localhost:8870/*` as reader origin and as a controlled target, so the whole loop runs locally. Never ship the dev variant.

## 3. Iteration loops

Run the fastest loop that can fail for the change you made. Move up only when the lower loop is green.

| Loop | What runs | Target turnaround | Model calls | Who |
| --- | --- | --- | --- | --- |
| L0 Unit | `node --test` on pure modules | < 5 s | 0 | automated |
| L1 Window harness | Static page that mounts the window module directly, plus a snapshot stepper | < 30 s, reload to see | 0 | automated + eye |
| L2 Local lab | Dev reader on `localhost:8870` with fixture provider, unpacked dev extension, controlled target tab, Playwright | 1–3 min | 0 | automated |
| L3a Real Simulink, fixture provider | Real MATLAB Online tab, local reader with fixture provider, unpacked dev extension | ~10 min | 0 | user, guided checklist |
| L3b Real Simulink, real provider | Same, with a real model read | ~15 min | real | user; needs explicit authorization |

### L0 Unit (pure functions)

Modules to keep pure so they are testable without a browser:

- **Projector** `labState → floating-guidance/v0.1 snapshot`. Fixtures come from real `data/guided-policy.json` and the replayed lab states, never the handoff's illustrative strings. Cases:
  - CP-DSB-06 `gain-settings` gives Now "Set Recovery gain to 2.", where "Double-click Recovery gain.", settings `Gain = 2`, Next "Connect Receiver product → Lowpass → Recovery gain."
  - Last action of a checkpoint: Next comes from `next_instruction` with its own checkpoint/action identity.
  - Completion: `next` is null.
  - `verification_only` is only ever `true` (absent means authored action).
  - Text, list and message size limits are enforced, and unknown versions are rejected.
- **Lifetime reducer** `(windowState, snapshot | event) → windowState`, one test per row of handoff §7: waiting-first, new frame without analysis, accepted analysis, view change, freshness expiry (20 s), provider 400/503/429, checkpoint change, pause, disconnect, reconnect, local minimize.
- **Ordering guard:** stale stream/attachment generation, out-of-order sequence, duplicate (idempotent, no repaint), late auxiliary completion.
- **Protocol validator:** message type allowlist, sender shape, version negotiation.

Run: `node --test scripts/test-floating-*.mjs` (new files, beside the existing `test-*.mjs`).

### L1 Window harness

A local HTML page that mounts the content-script window module into a Simulink-shaped page (reuse `scripts/fixtures/gain-dialog.html` as the underlay). It has a stepper that feeds recorded snapshots for every §7 state. No extension and no server are needed, so it is the loop for visual and interaction work.

Checks (Playwright screenshot + assertions, and a quick look):

- Combined dock renders Now, Next, connection/read status and screen context, readable at 100% and 150% zoom and at 1024×700.
- Split into two windows and re-dock; positions persist across a reload; reset-position works.
- Drag clamps to the viewport after a resize; nothing jumps when a new snapshot arrives.
- Minimize to the Kiki launcher and restore with no content loss.
- **No event leakage:** the underlay counts its own pointer/key/wheel events. Clicking, dragging, typing and scrolling inside Kiki leaves the counter unchanged. Clicking outside Kiki still reaches the underlay.
- Keyboard: tab order, visible 2px `focus-ring`, Escape minimizes, an arrow-key or reset alternative to drag, focus returns sensibly after minimize.
- `prefers-reduced-motion` turns off transitions.
- Breadboard tokens: `paper`/`paper-raised` surfaces, `ink`/`pencil`/`line`, `blue-ink` for practical labels. Status always carries a word, never only colour.
- Long content (several settings, long `how`) scrolls inside the window.

### L2 Local lab (automated end to end, no model)

Start: `npm run build && node scripts/dev-server.mjs --analysis-fixture` (add `--quota-fixture` for 429). Playwright launches Chromium with the unpacked dev extension (`--load-extension`, persistent context) and `--auto-select-tab-capture-source-by-title`, as the existing `check-*-browser.py` scripts do. Proposed script: `scripts/check-floating-guidance-browser.py`.

Scenarios:

1. **Cold connect:** start a lab, bind the target tab via the popup. Saved Now/Next appear **before** the first analysis completes; Screen context says waiting for a first read.
2. **Coherence:** after each committed update, the reader's current-action text, the window's Now text and both lab revisions match. This is the core lab-coherence assertion and should run after every transition below.
3. **Advance:** drive the receiver fixture scene (`work/receiver-scene.txt`) to make an action advance; the window replaces Now/Next atomically, with no adjacent-revision mix.
4. **Pause/resume from the window:** the window shows "Pausing…" until the authoritative snapshot arrives, then Paused. The observation is cleared (pause clears `runtime.candidate`). Resume restores the guide. A stale revision gets a 409, which shows "Could not pause, open tracker" and changes nothing.
5. **Provider wait:** 429 via `--quota-fixture`; 503 via the existing fixture failure; add a 400 dev flag for the 15-minute model-wide cooldown path. In every case the instructions stay, the status is honest with the retry time, and no new observation appears.
6. **Freshness:** with no new accepted analysis for over 20 s, Screen context flips to "Earlier view" and its timestamp never refreshes from delivery alone.
7. **Lifecycle:** stop sharing, navigate the target, close the reader tab, reload the target (host permission re-injects; binding must be re-established explicitly, not resurrected), stop the service worker via CDP and send a message. Each case ends in the correct status and an explicit reconnect, with no stale fresh claim.
8. **Self-capture canary:** dev builds render a canary token and a solid canary colour patch inside the window. A test-only hook reads the capture canvas right after the copy and asserts the canary colour is absent in the window rectangle. The fixture provider also asserts that the canary token never appears in anything it is sent.
9. **Mask timing:** log `performance.now()` for hide → copy → restore on every sample. Record p50/p95 in the foreground and with the target tab in the background. Iteration target: restored within one frame in the foreground; the background value is recorded, not gated, until we have data.
10. **Interaction safety:** drag/expand/type inside Kiki during capture produces no view-change invalidation, no lab mutation and no checkpoint change.
11. **Exposure is not progress:** display ACKs (visible/minimized/rendered) never change a checkpoint or learner dimension.

### L3a Real Simulink, no model (user checklist, about 10 minutes)

Same local reader with `--analysis-fixture` and the unpacked dev extension, but the target is the real `matlab.mathworks.com` tab with the DSB-SC model open. The fixture provider reports `unknown`, so nothing advances on its own; this isolates windows, masking and interaction on the real tool.

1. Bind the MATLAB tab from the popup; the dock appears with the saved current/next step.
2. Read Now and Next without switching tabs. Is the default corner and width acceptable over the model?
3. Split into two windows, move them, re-dock.
4. Drag a block, open the Recovery gain dialog and pan the canvas with Kiki open. Simulink behaves normally and Kiki does not reset.
5. Type inside a Kiki field or press keys with Kiki focused. Nothing reaches Simulink.
6. Pause and resume from the window; the reader tab agrees.
7. Reload MATLAB; Kiki returns via the host permission and asks to reconnect rather than showing stale content as live.
8. Note anything flickering during capture (the mask must not look like disappearing windows).
9. Screenshot of the windows over Simulink, plus the evidence JSON from the dev server.

### L3b Real Simulink, real provider (only after authorization)

Same as L3a with a real model read through a local key or an agreed private Site. Check one accepted observation appears with its source time, ages correctly, and Kiki's own text is never read back as screen evidence. Hosting choice and any deployment are separate decisions.

## 4. Fast-iteration aids to build alongside the slice

- **Snapshot recorder:** dev builds append every built snapshot to `work/floating-guidance/snapshots.jsonl`; L1 replays them. Real-tool bugs become L1 fixtures in seconds.
- **Debug footer (dev only):** stream, sequence, lab revision, observation age and mask p95 in a small line inside the dock.
- **Event log:** one JSON line per event from handoff §11: snapshot built, received, validated/rejected with reason, displayed, minimized/restored, observation changed/stale, disconnected, mask started/restored/failed. No raw images, keys or free text.
- **Fixture provider flags:** existing `--analysis-fixture`, `--quota-fixture`, `--receiver-fixture`; add `--provider-400` and `--provider-503-always`.

## 5. Guardrails for every loop

- L0–L3a make zero model calls and touch no hosted Site, secret or saved learner session.
- Use the local SQLite database only (`work/lab-preview.sqlite`); never seed or reset a hosted session.
- The dev extension manifest stays out of any package the user installs for hosted use.
- The frozen annotation suite, baselines and the existing receiver Site stay unchanged.

## 6. Exit to formalisation

Iteration is done when L0–L2 pass together, the user completes L3a without a blocking issue, and one L3b run shows an accepted observation correctly labelled. Then formalise:

- Publish `contracts/floating_guidance.v0_1.schema.json` with examples.
- Add L0 + L2 to CI (extend `screen-reader-evaluation.yml` or add a new workflow).
- Walk the full acceptance matrix from handoff §11 and record evidence.
- Measure analysis→commit and commit→paint latency in the real flow.
- Decide the hosted surface and produce a release extension build.

## 7. Open after this plan

- Default dock corner, width and density: settle in L1/L3a with screenshots rather than up front.
