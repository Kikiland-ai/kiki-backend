# Screen sharing from kiki-web Lab mode — handoff

Written 17 October 2026; decisions added 18 October 2026, Asia/Kolkata. This handoff is for the next session that builds screen sharing into kiki-web Lab mode. **No kiki-web change has been made yet.** The user's decisions are in §2 and [ADR 0010](../decisions/0010-kiki-web-api-fronts-lab-execution.md). The plan is in §3.

## 1. Outcome and evidence

User instruction:

> "the handoff for the screenshare here happens from a demo site, this should be instead done from the lab mode itself"

The student starts, sees and controls sharing from **kiki-web Lab mode** (`/labs/:sessionId`). The Kiki windows appear on the shared MATLAB tab through the extension. kiki-backend's demo reader becomes a backend QA tool only.

**What already works**, on `experiment/floating-guidance-bubbles`. The user confirmed on 17 October that it works on their real MATLAB Online tab with live Gemini reads (`gemini-3.5-flash-lite`). From the server log:

- 79 reads; tracking advanced CP-DSB-01 → CP-DSB-06; 78 committed, 1 provider 503.
- Frame received → committed: p50 4.7 s, p90 10.1 s, max 18.7 s.
- Gemini time to first byte: p50 3.6 s, about 85% of each read.
- Server work around each read: about 60 ms or less at p50.

## 2. Decisions (user, 18 October)

| Question | Decision |
| --- | --- |
| Backend boundary | **kiki-web's own API (`apps/api`) checks Firebase sign-in and passes lab-execution requests through to kiki-backend.** The browser talks only to kiki-web's API |
| kiki-web base | **`main`** (PR cleanup done; `origin/main` = `93cce9b`, PR #5) |
| Commit identity in kiki-web | **`arpanvihan5-sketch`** <317357476+arpanvihan5-sketch@users.noreply.github.com>. This overrides kiki-web `AGENTS.md:7` (`akshitanitr`) for this work, by explicit user decision |
| kiki-web production web address | **Unknown. Treated as a blocker (B1, §3)** |

## 3. Plan

### Blockers and high priority

| ID | Item | Why it blocks | Owner | Until resolved |
| --- | --- | --- | --- | --- |
| **B1 (high priority)** | **kiki-web production origin and hosting**: HTTPS URL, SPA fallback (`apps/web/README.md:59`), deploy target | Required in three places: the extension allowlist and capture-handle `permittedOrigins` (`build-extension.mjs` `readers`), apps/api `KIKI_CORS_ORIGINS`, and the WebSocket Origin check. No hosted Kiki address exists (`apps/web/active.md:159`) | User / Akshita | Build and test only on dev origins (`http://127.0.0.1:5174`) |
| **B2 (high priority)** | **Host kiki-backend's Python service**: one persistent HTTPS instance with `KIKI_REQUIRE_PROXY=1`, `KIKI_PROXY_SECRET`, `GEMINI_API_KEY(S)` and persistent `KIKI_DATA_DIR` (`deploy/fastapi/runtime.env.example`) | apps/api needs a reachable upstream in production. The Python service is not hosted today (`docs/handoffs/frontend-api.md:136`) | User | Run it locally on `127.0.0.1:8100` |
| B3 | Aditya's agreement: this path is the lab-execution integration for his screen-share/assessment scope | Docs assign screen-share monitoring and assessment to Aditya, deferred (`TEAM_HANDOFF.md:41,116`) | User / Aditya | Build behind the existing `monitoring: pending_integration` until agreed |

### Now — set up and unblock

1. **Sync kiki-web.** The user's checkout is on clean `main` (untracked `.claude/` only), 18 commits behind `origin/main`.
   - Run `git pull --ff-only`.
   - Branch `feature/lab-screen-share` from `93cce9b` or later.
   - Set the repo's `user.name`/`user.email` to `arpanvihan5-sketch` and verify with `git var GIT_AUTHOR_IDENT`.
2. **Raise B1, B2 and B3 with their owners.** Record the answers in kiki-web `apps/web/active.md` and in this file.
3. **Python parity spike.** Run kiki-backend's unified API locally with the proxy guard (install `prototypes/screen_capture/requirements.txt`, then `KIKI_PROXY_SECRET=<32+ chars> KIKI_REQUIRE_PROXY=1 GEMINI_API_KEY=<server-side> python -B -m prototypes.backend --port 8100 --data-dir work/backend`; the default port is 8765; see `SETUP.md`), then:
   - Check that its lab state has every field the window projector reads:
     - from `guidance`: `current_action`, `next_action`, `next_instruction`, `action_position`, `procedure`, `already_tracked`;
     - from `runtime`: `capture_active`, `analysis_status`, `retry_after_ms`, and `candidate` with `admitted_context` and `source_frame.server_received_unix_ms`;
     - from `observation`: `age_ms` and `observation_id`.

     The Python service already computes the guidance fields (`prototypes/lab_tracking/guided.py:99-109`, `service.py:135-148`). The runtime and observation fields are unverified.
   - Add a Python-state fixture to `scripts/test-floating-guidance.mjs`, and port the two Worker fixes if missing: committed `capture_active` and accepted-observation retention.

### Next — build slice 1, local end to end

**kiki-backend (small):**

- Use the existing trusted-upstream contract unchanged. `SiteProxyGuard` (`prototypes/screen_capture/cloud_access.py`) requires `x-kiki-proxy-key` (constant-time compare) and a 1–256 character `x-kiki-owner` on HTTP and WebSocket. It is covered by `tests/test_cloud_access.py`.
- Mutations also need `Origin` equal to the backend's own address, so the caller rewrites it, as `prototypes/json_stream_site/worker/python-proxy.js` does.
- Optionally add an `owner` namespace test for `fb:<uid>`.

**kiki-web `apps/api` — a new `lab_execution` module:**

- **Auth and ownership:** reuse `Depends(identity)` (Firebase `verify_id_token(check_revoked=True)`, Google provider only) and the `CRS-AC-ECE` enrollment check. Load `learners/{uid}/labPreparations/{prepId}`; another user's preparation returns 404.
- **Mapping:** add `learners/{uid}/labExecutions/{prepId}` = `{schema:"lab-execution-link/v1", backendLabId, backend:"kiki-backend-python", practicalId:"PR-AM-DSB", contentVersion, createdAt}`.
  - Create it in a transaction on the first `POST /lab-preparations/{prepId}/execution`, which calls upstream `POST /lab-sessions {operator_trial:true, model_name:<projectRef or "dsb_sc">, progression_mode:"screen_guided"}`.
  - The call is idempotent (`Idempotency-Key`); never create two upstream labs for one preparation.
  - Checkpoint IDs already match (`CP-DSB-01…12`).
- **Upstream client:**
  - Fixed `KIKI_LAB_BACKEND_ORIGIN` (HTTPS in cloud; `http://127.0.0.1:8100` allowed only in local mode) and server-only `KIKI_LAB_PROXY_SECRET` (32+ characters).
  - On every call, send `x-kiki-owner: fb:<uid>` and `x-kiki-proxy-key`, rewrite `Origin` to the upstream origin, and strip all client cookies and `x-kiki-*` headers.
  - Follow no redirects; enforce timeouts and a frame body limit.
  - Move `httpx` from dev to runtime dependencies; add a WebSocket client library.
- **Routes:** a fixed allowlist with no generic path proxy. All under `/lab-preparations/{prepId}/execution`:

  | kiki-web route | Upstream | Notes |
  | --- | --- | --- |
  | `POST` (create/attach link) / `GET` | `POST /lab-sessions` / `GET /lab-sessions/{lab}` | Lab state |
  | `POST /screen-sessions` | `POST /screen-sessions` | Start a capture segment |
  | `POST /stream-ticket` | — | One-time HMAC ticket, about 60 s, bound to uid + prep + screen session. Browsers cannot send `Authorization` on WebSockets |
  | `WS /screen-sessions/{sid}/stream?ticket=` | `WS /screen-sessions/{sid}/stream` | Relay frames both ways. Check `Origin` against the CORS list by hand, since CORS does not apply to WebSockets |
  | `POST /attach` | `POST /lab-sessions/{lab}/attach` | Revision-checked |
  | `POST /check-stream` | `POST /lab-sessions/{lab}/check-stream` | **SSE passthrough** (`StreamingResponse` over an `httpx` stream), chunks in order, no buffering |
  | `POST /context` | `POST /lab-sessions/{lab}/context` | Pause/resume, view and parameter changes, revisit |
  | `POST /review`, `POST /responses` | same | Student confirmations and answers |
  | `GET /events`, `GET /image` | same | Journal and the last checked frame |

- **Error mapping:**
  - Pass 409 through so the client refreshes.
  - A 401 from upstream means a configuration fault; return 503 with "Lab tracking is unavailable; your progress is kept."
  - Upstream down → 503, with the same message.
- **Monitoring:** when an execution link exists, `monitoring.status` stops being pinned to `pending_integration`. Change the Pydantic `Literal`, the Zod literal (`contracts/lab-preparation.ts:15`) and `LAB_PREPARATION_CONTRACT.md` together. `pointerActive` stays false; the floating windows replace the pointer for this slice.
- **Tests** (pytest with a fake upstream):
  - forged `x-kiki-owner` is stripped;
  - another user's prep returns 404;
  - expired, reused or mismatched tickets are refused;
  - SSE arrives in order and incrementally;
  - WebSocket frames are relayed and closed on revoke;
  - upstream down → 503;
  - one upstream lab per preparation under concurrent creates.

**kiki-web `apps/web` — the Lab mode controller** (in `features/labs`):

- An execution service with Zod contracts for the kiki-backend fields actually used. Keep kiki-backend's field names; map them in one adapter.
- A capture hook:
  - `getDisplayMedia` on a user gesture only, with picker guidance (choose the Chrome tab);
  - a frame about every 2 s, longest side at most 1600 px;
  - **redact Kiki rectangles on the copied canvas, then JPEG-encode** ([ADR 0009](../decisions/0009-floating-window-capture-redaction.md));
  - send frames over the ticketed WebSocket, then check with `{revision, frame_id, view_revision}`, the Python flow in `frontend-api.md` "Screen-guided UI binding";
  - stop on sign-out through `withResourceCleanup` / `registerSignOutCleanup`.
- A check-stream client: adopt state **only** from `guidance_committed`; provisional findings are a labelled preview only.
- The Kiki window publisher: port `floating-guidance.js` (pure projector) and `floating-bridge.js` (protocol, `sampleSafety`/`apply`) to TypeScript. The protocol stays `floating-guidance/v0.1` (§4).
- A connection panel replacing "Monitoring not connected" (`LabPreparation.tsx:13`):
  1. Open MATLAB Online.
  2. Show Kiki on MATLAB: detect the extension, or show install steps.
  3. Share your MATLAB tab.
  4. Then show the states: connecting, active, paused, disconnected, completed. Each non-active state gives a reason and a recovery action (CONTRACT §8). Reconnecting needs a fresh gesture.

**Extension:**

- Add `http://127.0.0.1:5174`, plus `:5173` if sample mode is used, to `readers` in `prototypes/floating_guidance/scripts/build-extension.mjs`, then rebuild.
- The production origin is added when B1 resolves.

**Acceptance for slice 1 (local):**

- Ported L0 projector and bridge tests pass in Vitest.
- A Playwright run with the dev extension (Playwright Chromium; flags as in `prototypes/floating_guidance/tests/check-local-lab.py`) proves start-from-Lab-mode, coherence, pause from both sides, clean model-bound frames, and lifecycle.
- The backend is kiki-backend Python with a fake analyzer.
- Then the user repeats L3 on real MATLAB Online from `/labs/:sessionId`, with no demo page open.

### Later

- Resolve B1 and B2: deploy both services and produce a release extension build with the production origin.
- Hosted L3 and a latency comparison against §1.
- Remove the demo reader from the student path.
- Answer the remaining `LAB_PREPARATION_CONTRACT.md:47-57` questions: device control/lease across phone and laptop, the evidence/verdict schema, and how completion feeds practical progress.
- Odia copy in windows; letting Lab mode bind the MATLAB tab without the popup; the pointer or other cues.

## 4. Bridge protocol (unchanged, `floating-guidance/v0.1`)

`window.postMessage` on channel `kiki-floating-guidance`, same origin and top frame only. Requests carry `bridge_id` and get `{type:'response', bridge_id, result}`.

| Direction | Type | Meaning |
| --- | --- | --- |
| page → extension | `reader_hello {stream_id, lab_session_id}` | Become the controller; the extension returns a new `generation` and the bound tab's capture `handle` |
| page → extension | `reader_snapshot {message}` | `replace_snapshot` with `stream_id`, `generation` and an increasing `sequence`; the result is the display ACK |
| page → extension | `reader_command_result` / `reader_bye` | Outcome of a window command / page closing |
| extension → page | `extension_present`, `fg_target_bound {handle, target_origin}`, `fg_target_closed` | Install and binding state |
| extension → page | `fg_command {command, request_id}` | Pause or resume pressed in a window |
| extension → page | `fg_rects {rects, viewport, moving}` | Window rectangles in CSS px, for redaction |
| extension → page | `fg_snapshot_request`, `fg_superseded` | Resend now / another controller took over |

Send a snapshot on every content change and at least every 5 s. The windows mark the connection lost after 15 s of silence. Capture is analysed only when `displaySurface === 'browser'` and the capture handle matches the bound tab; any other frame is greyed and not analysed.

## 5. Facts the plan relies on

| Area | Fact | Source |
| --- | --- | --- |
| kiki-web auth | `firebase_admin.auth.verify_id_token(check_revoked=True)`; Google provider only; UID never taken from the body | `apps/api/.../backend.py:49-63`, `main.py:56-61` |
| kiki-web lab data | Firestore `learners/{uid}/labPreparations/prep-{uuid}` (`lab-preparation/v1`, revisioned PATCH, 409 on stale); one active prep per UID and content version; `monitoring` pinned | `lab_preparation.py:73-91, 224-278, 292-310` |
| kiki-web API today | No outbound HTTP client (`httpx` is dev-only), no SSE or WebSocket routes, exact-origin CORS for `127.0.0.1:5174`/`localhost:5174`, no DELETE | `pyproject.toml:17`, `main.py:28-47`, `config.py:19` |
| kiki-web web | `/labs` and `/labs/:sessionId` in `LabPreparation.tsx`; provisional, unimplemented execution types in `contracts/api.ts:302-455`; sign-out cleanup with a 3 s deadline | `App.tsx:17-18`, `resource-cleanup.ts:6-28` |
| IDs | Practical `PR-AM-DSB`; checkpoints `CP-DSB-01…12`, the same as kiki-backend; `projectRef` is free text | `data-model/cases/analog-modulation-odia.json` |
| kiki-backend upstream | `SiteProxyGuard` and same-origin mutation rule; frames over WebSocket; `check-stream` v2 in Python | `cloud_access.py`, `backend/app.py:17-29`, `json_stream/api.py:16` |
| Demo reader | Same-origin only: Site-injected owner header and `SameSite=Strict` cookies, so kiki-web cannot call it | `json_stream_site/worker/server.js:33-73,163` |

kiki-web facts come from an export of `origin/main` at `93cce9b` (PR #5) on 18 October. The states of PRs #1–#3 were not rechecked.

## 6. Do not

- Do not let the browser call kiki-backend directly, or put `KIKI_LAB_PROXY_SECRET` or a Gemini key anywhere client-side.
- Do not build a generic path proxy; allowlist each route.
- Do not mock a Simulink connection, or label screen-inferred progress as verified evidence.
- Do not upload or analyse frames that could contain Kiki windows without redaction.
- Do not ship the demo reader or the dev extension (canary, open shadow root, localhost) to students.
- Do not depend on the stopped annotation/drawing code.
