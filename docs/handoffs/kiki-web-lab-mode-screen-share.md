# Screen sharing from kiki-web Lab mode — handoff

17 October 2026, Asia/Kolkata. Handoff for the kiki-web team. **No kiki-web change has been made.** Decisions still open are marked; nothing here is approved until they are settled.

## 1. Decision and why now

User instruction, after the live floating-window test:

> "the handoff for the screenshare here happens from a demo site, this should be instead done from the lab mode itself, this is a handoff for the kiki-web that should be taken care of."

Today the student shares the MATLAB tab from kiki-backend's **demo reader page**: `http://localhost:8870` locally, or the private reader Site. Kiki's floating windows then appear on the MATLAB tab through the extension.

The goal is for the student to start, see and control sharing from **kiki-web Lab mode** (`/labs/:sessionId`), with the same windows on the MATLAB tab. The demo reader then becomes a backend QA tool, not part of the student journey.

**What already works**, on `experiment/floating-guidance-bubbles` (`e629108`) with real Gemini reads (`gemini-3.5-flash-lite`). The user confirmed it works on their real MATLAB Online tab. The local server log gave:

- 79 screen reads; tracking advanced CP-DSB-01 → CP-DSB-06; 78 committed, 1 provider 503.
- Frame received → decision committed: p50 4.7 s, p90 10.1 s, max 18.7 s.
- Gemini time to first byte: p50 3.6 s, p90 7.4 s; that is about 85% of each read.
- Server work around the call (lab-state reads, provider bookkeeping, commit): under about 60 ms per read at p50.
- Median per read: about 4.3k input tokens, 285 output tokens, 72 KB image.

Commit → window display time was not logged server-side. It is visible in the reader page's `KikiFloating.diagnostics()`.

## 2. The role Lab mode takes over

The extension talks to **whichever page captures the screen**. That page is the "controller", and in this design it must be Lab mode. Its responsibilities, as the demo reader implements them today:

1. **Lab session lifecycle.**
   - Create or resume the session (`screen_guided` progression) and attach the capture session.
   - Send a heartbeat about every 10 s; it needs a capture receipt under 6 s old, and the server marks capture inactive after 20 s without one.
   - Detach on stop, sign-out and `pagehide`.
2. **Capture loop.**
   - Call `getDisplayMedia` only on a user gesture; never reuse an old permission (CONTRACT §8).
   - Sample about every 2 s; scale so the longest side is at most 1600 px.
   - **Redact Kiki's window rectangles on the copied canvas before encoding** ([ADR 0009](../decisions/0009-floating-window-capture-redaction.md)).
   - Encode JPEG at quality 0.8 (0.55 above 1 MB; frames over 1 MB are rejected) and upload.
   - Increase the view revision when the source dimensions change.
3. **Analysis.**
   - Use the streamed check (`lab-analysis-stream/v2`) at the cadence in `lab-cadence.js`.
   - Adopt state **only** from `guidance_committed`. Provisional findings are a labelled preview and never replace accepted facts.
   - Honour `waiting_for_provider` / `retry_after_ms`. A non-auth 4xx starts a 15-minute model-wide cooldown, and saved instructions must stay usable throughout.
4. **Authoritative actions:** pause/resume, student confirmations, responses and revisit, all revision-checked. A 409 means refresh, never overwrite.
5. **Kiki windows publisher.**
   - Build the `floating-guidance/v0.1` projection from every adopted state.
   - Serve the bridge protocol (§4).
   - Route window pause/resume to the same action as the Lab mode button.
6. **Status UI.** Lifecycle per kiki-web CONTRACT §8: connecting, active, paused, disconnected, completed. Each non-active state shows a reason and a recovery action. Also show whether the extension was detected and why a frame was blocked (§6).

## 3. Reference implementation to port (JS → kiki-web TypeScript)

Paths are in kiki-backend on `experiment/floating-guidance-bubbles`. Port the behaviour, not the DOM code.

| Source | What it does | Port note |
| --- | --- | --- |
| `prototypes/json_stream_site/assets/floating-guidance.js` | Pure projector: tracker state → window snapshot; accepted-observation retention; freshness and scope rules | Port as a TS module with a Zod schema for the snapshot; keep `scripts/test-floating-guidance.mjs` cases as Vitest |
| `prototypes/json_stream_site/assets/floating-bridge.js` | Publisher, bridge handshake, heartbeat, command routing, `sampleSafety` / `apply` redaction | Port as a hook or service in `features/labs`; the message names are the contract |
| `prototypes/json_stream_site/assets/capture.js` (`frame()`) | Copy → redact → encode → upload order | Keep the order exactly: redact before `toBlob` |
| `prototypes/json_stream_site/assets/json-stream-client.js` | SSE v2 parsing; committed vs auxiliary | Reuse the rules; Zod-validate events |
| `prototypes/json_stream_site/assets/lab-cadence.js` | When to request the next read | Reuse |
| `prototypes/json_stream_site/assets/lab.js` | State adoption, `render()` mapping, `action()`, pause wiring | Reference for which fields the UI reads |
| `prototypes/floating_guidance/extension/` | MV3 extension | **No code change** needed except origins (§5) |

## 4. Bridge protocol (unchanged, `floating-guidance/v0.1`)

`window.postMessage` on channel `kiki-floating-guidance`, same origin only, top frame only. Each request carries `bridge_id` and gets a `{type:'response', bridge_id, result}` reply.

| Direction | Type | Meaning |
| --- | --- | --- |
| page → extension | `reader_hello {stream_id, lab_session_id}` | Become the controller. The extension returns a new `generation` and the bound tab's capture `handle`, if any |
| page → extension | `reader_snapshot {message}` | `replace_snapshot` with `stream_id`, `generation` and an increasing `sequence`. The result is the window's display ACK |
| page → extension | `reader_command_result {request_id, ok, error}` | Outcome of a window command |
| page → extension | `reader_bye` | Page closing; windows go "not live" |
| extension → page | `extension_present {version}` | Extension installed and bridge loaded |
| extension → page | `fg_target_bound {handle, target_origin}` / `fg_target_closed` | MATLAB tab bound or gone |
| extension → page | `fg_command {command, request_id}` | `pause` or `resume` pressed in a window |
| extension → page | `fg_rects {rects, viewport, moving}` | Window rectangles in CSS px, for redaction |
| extension → page | `fg_snapshot_request` / `fg_superseded` | Resend now / another controller tab took over |

Publish rules:

- Send on every content change and as a heartbeat at least every 5 s. The windows mark the connection lost after 15 s of silence.
- Never resend old pixels as fresh. The observation age is server-measured plus local monotonic time.

## 5. Extension changes

- Add kiki-web origins to `readers` in `prototypes/floating_guidance/scripts/build-extension.mjs`. The same list feeds the content-script matches and the capture handle's `permittedOrigins`.
  - Dev: `http://127.0.0.1:5174` (connected mode) and `http://127.0.0.1:5173` (sample mode).
  - `localhost` and `127.0.0.1` are different origins; add whichever the team actually uses.
  - Production: **open decision**; no kiki-web URL is documented yet.
- Keep binding explicit, through the extension popup's "Show Kiki on this tab". Letting Lab mode bind the MATLAB tab directly is a later option; it needs a new, allowlisted command.

## 6. Lab mode UX

Lab mode today (`apps/web/src/features/labs/LabPreparation.tsx` on PR #2) is preparation only, with a "Monitoring not connected" notice. Add a connection panel that follows the journey's activation order: experiment, required concepts, software opened, connection confirmed.

1. **Open MATLAB / Simulink Online.** This link already exists.
2. **Show Kiki on MATLAB.**
   - No `extension_present`: show install steps.
   - Present but unbound: tell the student to click the Kiki icon on the MATLAB tab and choose "Show Kiki on this tab".
   - Bound: "Kiki is on your MATLAB tab".
3. **Share your MATLAB tab.** A user-gesture button.
   - Picker guidance: choose the **Chrome tab** with MATLAB, not a window or the whole screen.
   - Verify `displaySurface === 'browser'` and that the capture handle matches the bound tab.
   - Otherwise show the block reason with a "Share again" action. Frames that can't be masked are greyed and never analysed.
4. **Guidance active.**
   - Lab mode shows progress, the current action and the observation.
   - The windows on MATLAB show the same step from the same state revision; that is the coherence acceptance.
   - Pause works from either place.
5. **Lifecycle.**
   - Stop sharing → disconnected, with Share again.
   - Provider wait → instructions stay, with the retry time shown.
   - Sign-out (`services.auth.registerSignOutCleanup`) → stop the tracks, detach, `reader_bye`.
   - Reconnecting needs a fresh gesture.

The floating windows replace the pointer for this slice. Keep `pointer.active` false; the windows don't use it.

## 7. Backend boundary — the main open decision

Facts:

- **The demo reader Worker is same-origin only.** Its owner comes from the private Site's `oai-authenticated-user-id` header, and capture receipts are `HttpOnly; SameSite=Strict` cookies. kiki-web cannot call it from another origin.
- **kiki-backend's unified Python FastAPI** ([frontend API handoff](frontend-api.md)) has the same capabilities:
  - `/screen-sessions` with a WebSocket frame transport;
  - `/lab-sessions/{id}/check-stream`, `/context`, `/review` and `/responses`;
  - the identical tracker policy.

  Its auth is an edge-supplied owner or a local cookie, not Firebase, and it is not hosted.
- **kiki-web connected mode** calls its own `apps/api` with a Firebase Bearer token. CORS allows `127.0.0.1:5174`. CONTRACT §6: "all data goes through the API; the backend derives the UID from the token".
  - kiki-web's provisional lab-execution types and endpoint constants (`apps/web/src/contracts/api.ts:301-412, 496-507`) differ from kiki-backend's routes and state shape.
  - Every preparation response is pinned to `monitoring: pending_integration`.
- **Ownership:** screen-share observation and assessment belong to Aditya and are deferred. The integration questions are listed in `apps/web/LAB_PREPARATION_CONTRACT.md:47-57`.

Options:

| Option | Shape | Trade-off |
| --- | --- | --- |
| **A (recommended).** kiki-web's API fronts lab execution | `apps/api` verifies Firebase, then calls kiki-backend's lab/observation service server-to-server with the derived owner. Frames go to `apps/api` (HTTP or WS) and on to kiki-backend | Matches CONTRACT §6 and keeps one API and one auth for the client. Needs a service-to-service contract and hosting for kiki-backend's Python service |
| B. kiki-web calls kiki-backend directly | Add Firebase token verification and CORS for kiki-web origins to kiki-backend's FastAPI | Fewer hops, but two APIs and two auth paths in the client; weakens the single-API rule |
| C. Keep the demo reader, linked from Lab mode | — | Rejected by this instruction |

Either A or B keeps redaction in the browser; the transport does not matter for it. Mapping kiki-backend's lab state to kiki-web's types is needed in both: keep kiki-backend's fields authoritative and map them in one adapter.

## 8. Acceptance

1. **Started from Lab mode.** With the real extension and MATLAB Online, a student starts sharing from `/labs/:sessionId` with no demo page open, and the Kiki windows appear.
2. **Coherence.** Now/Next in Lab mode and in the windows match after every committed read, after a pause from either side, and after an advance.
3. **Clean input.**
   - The model-bound JPEG shows a grey box where Kiki is and never the dev canary.
   - Sharing the wrong surface blocks analysis with a reason.
4. **Lifecycle.** Stop sharing, MATLAB reload, Lab mode reload, sign-out and provider wait each end in the right state with a recovery action.
5. **Latency.** Comparable to the numbers in §1. Measure frame received → committed, and committed → window display.
6. **Automated coverage.** Port L0 and a kiki-web version of L2 (Playwright Chromium with the unpacked dev extension; tab-capture auto-select flags as in `prototypes/floating_guidance/tests/check-local-lab.py`). A fake Simulink page alone cannot pass item 1.

## 9. Open decisions before building

1. **Backend boundary:** option A or B (§7). Owners: the user, Akshita and Aditya.
2. **kiki-web base branch.** PR #2 (`df2de21`, unmerged) is the handover's base. `redesign/engineering-sketchbook` (`2cfc241`) restyles `LabPreparation.tsx`, `Shell.tsx` and `ResumeLab.tsx` from an older base. Lab-mode work must reconcile with it.
3. **Commit identity.** kiki-web's AGENTS.md says `akshitanitr`; the workspace CLAUDE.md says `arpanvihan5-sketch` for Arpan's work.
4. **Production origin** for kiki-web (extension allowlist and capture-handle permission).
5. **Binding.** Whether it stays popup-only or Lab mode may bind the MATLAB tab.

## 10. Do not

- Do not mock a Simulink connection or label screen-inferred progress as verified evidence.
- Do not upload or analyse frames that could contain Kiki windows without redaction.
- Do not ship the demo reader or the dev extension (canary, open shadow root, localhost) to students.
- Do not depend on the stopped annotation/drawing code.
