# Floating Kiki windows — first slice

Kiki mini windows inside the shared MATLAB/Simulink Online tab. They show the reader's current and next step, the accepted screen observation and the connection state, so the student does not need to switch tabs. Design: [handoff](../../docs/handoffs/floating-guidance-windows.md), [ADR 0008](../../docs/decisions/0008-floating-guidance-windows-first-slice.md), [ADR 0009](../../docs/decisions/0009-floating-window-capture-redaction.md), [test plan](../../docs/plans/floating-guidance-test-plan.md).

The tracker stays authoritative. The windows copy its text, never choose a step, and never count as a lab action. Pause/resume from a window calls the reader's existing revision-checked lab action.

## Pieces

| Path | Role |
| --- | --- |
| `../json_stream_site/assets/floating-guidance.js` | Deterministic `floating-guidance/v0.1` projection of the accepted lab state |
| `../json_stream_site/assets/floating-bridge.js` | Reader-page publisher, window command routing and capture redaction |
| `extension/core.js` | Receiver validation, ordering high-water and window view model (pure) |
| `extension/ui.js` | Breadboard dock/split windows; consumes every event that starts inside Kiki |
| `extension/content.js` | MATLAB-tab content script |
| `extension/background.js` | MV3 worker: tab binding, sender checks, routing; state in `storage.session` |
| `extension/bridge.js` | Reader-page bridge, allowlisted message types only |
| `harness/` | L1 harness, recorded snapshots and the controlled target page |
| `scripts/` | Extension build, fixture recorder and the L2 local lab server |
| `tests/` | L0 core tests, L1 harness check and L2 local lab check |

## Run the loops

From the repository root unless noted. L0–L2 make zero model calls and touch no hosted Site.

```sh
# Build the reader bundle (needed after any reader change) and both extension variants
(cd prototypes/json_stream_site && node scripts/build.mjs)
node prototypes/floating_guidance/scripts/build-extension.mjs        # work/floating-guidance/{release,dev}/

# L0 unit (under a second each)
(cd prototypes/json_stream_site && node --test scripts/test-floating-guidance.mjs ../floating_guidance/tests/test-core.mjs)

# L1 window harness (~5 s), screenshots in work/floating-guidance/harness/
python prototypes/floating_guidance/tests/check-harness.py
# or open prototypes/floating_guidance/harness/index.html?canary and use the scenario picker

# L2 local lab (~1 min): real reader + dev extension + controlled target, fixture provider
python prototypes/floating_guidance/tests/check-local-lab.py

# Refresh harness snapshots from replayed tracker states after policy/projection changes
(cd prototypes/json_stream_site && node ../floating_guidance/scripts/make-fixtures.mjs)
```

On Windows, set `PYTHONUTF8=1` for the repository's Python suites (the baseline reads UTF-8 files with the platform default).

## L3a: real Simulink, no model (you, about 10 minutes)

1. `cd prototypes/json_stream_site && node scripts/build.mjs && node ../floating_guidance/scripts/serve-local-lab.mjs`. This runs the local reader on http://localhost:8870 with the fixture provider. Screen reads return "not established", so nothing advances by itself.
2. Build the extension (above). In Chrome open `chrome://extensions`, turn on Developer mode, choose **Load unpacked** and select `work/floating-guidance/dev`.
3. Open MATLAB Online with the DSB-SC model. Click the Kiki extension icon and choose **Show Kiki on this tab**.
4. In another tab open http://localhost:8870, start the guided lab, then **Share screen** and pick the MATLAB tab.
5. Then check:
   - you can read Now and Next without switching tabs;
   - the default corner and width are acceptable;
   - split, move, re-dock and minimize all work;
   - with Kiki open you can still drag a block, open the Recovery gain dialog and pan;
   - pressing keys while Kiki has focus does nothing to Simulink;
   - Pause and Resume in the window match the tracker tab;
   - after reloading MATLAB, Kiki comes back and reconnects.
6. In the tracker tab, the returned frame should show a grey box where Kiki is. The magenta canary in the dev window must never appear in that image.

The dev build shows a magenta canary and uses an open shadow root for tests. Use `work/floating-guidance/release` for anything other than local testing. L3b, a real model read, needs your go-ahead and a key or private Site.
