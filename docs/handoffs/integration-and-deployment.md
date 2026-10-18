# Integration testing and deployment — handoff

18 October 2026, Asia/Kolkata. Written to continue on another machine. It gathers the work done on 18 October towards testing kiki-web and kiki-backend together and towards deployment, what was verified, what is open, and in what order to pick it up. The kiki-web side has a companion file, `docs/plans/backend-integration-and-deployment.md` in kiki-web.

## 1. Resume on a new machine

1. Install Git, **Git LFS** (`git lfs install`), Python 3.12, Node.js 22 or later and the GitHub CLI. Sign in with `gh auth login` as `arpanvihan5-sketch`.
2. Clone both repos into one folder (the old workspace used `Google AI Builder/`):
   ```sh
   git clone https://github.com/Kikiland-ai/kiki-backend.git
   git clone https://github.com/Kikiland-ai/kiki-web.git
   git clone https://github.com/Kikiland-ai/Design-Thinking.git
   ```
   In each repo set `user.name` to `arpanvihan5-sketch` and `user.email` to `317357476+arpanvihan5-sketch@users.noreply.github.com`; check with `git var GIT_AUTHOR_IDENT`. Commits must not credit an AI.
3. Check out the open PR branches (§3) if you are continuing them: `gh pr checkout 7` in kiki-backend, `gh pr checkout 9` in kiki-web.
4. kiki-backend dependencies: `python -m pip install -r prototypes/screen_capture/requirements.txt`, plus `playwright` with Chromium for the floating-window checks. Full offline gate: `python scripts/run-screen-reader-evaluation.py` (no paid calls).
5. kiki-web dependencies: `npm ci` in `apps/web`; `uv sync --frozen` in `apps/api` (add `--system-certs` on networks with TLS inspection).
6. On Windows, set `PYTHONUTF8=1` when running kiki-backend Python directly (§7).

Nothing from the old machine is needed: all work is pushed, and the archived branches are tags. The old workspace also had local-only files (`HANDOVER-kiki-web.md`, `HANDOVER-kit-components.md`, `browser-checks/`); their current content is summarised here and in the kiki-web companion file.

## 2. State on 18 October

| Repo | `main` | Notes |
| --- | --- | --- |
| kiki-backend | `54b841c` | All backend work is on `main` (PRs #2–#6). Stopped work is kept as tags `archive/annotation-v22`, `archive/floating-design-notes`, `archive/guidance-producer`, `archive/toon-stream-plan`, `archive/screen-writing-v02`, `archive/concept-canvas-recovered` |
| kiki-web | `b984c64` | Lab mode merged (PR #7); docs pointing at kiki-backend `main` (PR #8) |
| Design-Thinking | `2a6c843` | kiki-backend's pinned snapshot is `73d16c0`, 8 commits behind |

What exists and how far it is verified:

| Piece | Verified | Not verified |
| --- | --- | --- |
| Screen reader v1 and checkpoint tracker | Offline gate; private Worker Site; live run 17 Oct (78 of 79 reads committed, p50 4.7 s) | Six-item manual acceptance; any hosted Python run |
| Floating Kiki windows (extension) | L0, L1, L2 loops; live run 17 Oct | Release build with a production origin |
| kiki-web Lab mode → kiki-web API → kiki-backend | Contract matches `main`; kiki-web API and Vitest suites; Python receipt fixture; backend smoke script against a local backend | A real browser run of the whole chain; any two-machine run; MATLAB Online through kiki-web |
| Mixed-language text and speech | Real Gemini runs (evidence archive) | Runs from the database side (ADR 0011) |
| Concept canvas library | Verifier and tests; kiki-web publisher contract | Publication (no media bucket) |
| Deployment | Dockerfile and runtime env template exist | Image build (no Docker on the old machine), any host |

## 3. Open PRs — merge in this order

1. **kiki-backend #7** `fix/lab-integration-small` — idempotent `POST /lab-sessions`, `fb:<uid>` owner test, dev extension origins for `:5174`, time-based `until()` in the UI test, `scripts/smoke-lab-upstream.py`, the SSH forward chosen in the testing plan, and this handoff. CI passes.
2. **kiki-web #9** `fix/lab-integration-small` — `skipped` frame handling, create retry with the saved key and body, per-platform Playwright venv path, UTF-8 writes, first CI workflow, and the kiki-web companion handoff. CI passes (web and api jobs). **Merge after kiki-backend #7**: its retry assumes idempotent creation; against an older backend a retry could create a second lab.

GitHub records server-side merges as `ArpanAv3 <arpanvihan5@gmail.com>` and rejects the noreply address for `--author-email`. Use merge commits for code PRs whose commit IDs are cited in docs; squash is fine for documentation-only PRs.

## 4. Integration testing (chosen: SSH forward)

Plan and constraints: [connected integration testing](../plans/connected-integration-testing.md). Summary:

- kiki-web's API accepts the backend only at `http://127.0.0.1:8100` (local mode) or an HTTPS origin (cloud mode), so a plain LAN address does not work. The SSH forward makes the remote backend appear at `127.0.0.1:8100` on the kiki-web machine with no config change and no public exposure.
- Backend machine: OpenSSH Server enabled; backend started with `KIKI_PROXY_SECRET=<32+ chars> KIKI_REQUIRE_PROXY=1 GEMINI_API_KEY=<key> python -B -m prototypes.backend --port 8100 --data-dir work/backend`.
- kiki-web machine: `ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -L 127.0.0.1:8100:127.0.0.1:8100 <user>@<backend machine>`, then `KIKI_PROXY_SECRET=<secret> python -B scripts/smoke-lab-upstream.py` (9 checks, no model calls).
- kiki-web: `KIKI_LAB_EXECUTION_MODE=local`, `KIKI_LAB_BACKEND_ORIGIN=http://127.0.0.1:8100`, `KIKI_LAB_PROXY_SECRET=<secret>`; API on `:8000` with one worker; web with `npm run dev:connected -- --port 5174`; extension from `node prototypes/floating_guidance/scripts/build-extension.mjs`, load `work/floating-guidance/dev/`.
- The 15-step runbook is in the plan. Record results, latency and errors in `docs/plans/active.md`.

What has run: the smoke script passed 9/9 against a real backend on `127.0.0.1:8100` with the proxy guard on, and a wrong secret got 401. An SSH forward passes bytes through unchanged, so the same checks apply through it, but no two-machine run has happened.

Automated checks still to add:

- A frame and `check-stream` step in the smoke script, using a fixture analyzer so it stays free.
- kiki-web's lab Playwright suite against a real backend: a switch to skip its fake-analyzer server and use `KIKI_LAB_BACKEND_ORIGIN`, plus an auth-emulator ID token.

ngrok and Tailscale remain documented alternatives (plan, setups 2 and 3). With ngrok, never rewrite the Host header and run with `--inspect=false`.

## 5. Deployment path

ADR 0010: the browser talks only to kiki-web's API, which forwards an allowlist to this service. Generated content reaches kiki-web through the database (ADR 0011).

| Component | Today | Needed to deploy |
| --- | --- | --- |
| kiki-web web app | No hosting config, no single-page fallback (`apps/web/README.md`) | **B1**: choose a host and HTTPS origin; add the fallback |
| kiki-web API | No Dockerfile; WebSocket tickets in memory | A host; one worker or a shared ticket store; `KIKI_LAB_EXECUTION_MODE=cloud` with the backend's HTTPS origin; `KIKI_CORS_ORIGINS` with B1's origin; Firebase Authorized domains |
| kiki-backend FastAPI | `deploy/fastapi/Dockerfile` (binds 0.0.0.0, port 10000), `runtime.env.example`, `deploy/fastapi/README.md` | **B2**: one instance, one process, persistent volume at `/var/data`, `KIKI_REQUIRE_PROXY=1`, a new proxy secret, Gemini keys. Render was discussed, not provisioned. Build the image once to confirm it (not done) |
| Extension release build | Hosted reader Sites only | Add B1's origin to the release `readers`, then publish privately |
| Media assets | Concept WAVs in Git LFS; kiki-web expects a bucket (`KIKI_MEDIA_BUCKET`) | Being handled separately |
| CI | kiki-backend: offline gate on PRs and `main`. kiki-web: first workflow in PR #9 | Nothing further required to start |

Suggested order once B1 and B2 are decided: build and deploy the backend → run the smoke script against its HTTPS origin → deploy kiki-web's API in cloud mode pointing at it → deploy the web app → add the origin to Firebase, CORS and the release extension → hosted trial on MATLAB Online.

## 6. Decisions waiting on the user

1. **Hosting** for B1 (kiki-web web and API) and B2 (backend).
2. **Owner model.** One shared proxy secret serves two front doors: kiki-web's API (`fb:<uid>` owners) and the ChatGPT Site edge (`deploy/sites/python-proxy.js`, Site user IDs). Anyone with the secret can claim any owner. Options: retire the Site front door for students, give each front door its own secret, or prefix-check owners per secret.
3. **Readiness gate.** kiki-web lets students start screen guidance before passing the seven concept checks (`operator_trial`). Confirm or reverse.
4. **Lab home banner.** It shows "Practise with screen guidance" even when execution is disabled. Options: an API capability field (recommended), a `VITE_` build flag, or a `disabled` monitoring status.
5. **Concept canvases in kiki-web.** Keep or replace kiki-web's C-AM-08 package; React renderers or sandboxed iframes; per-placard or whole-concept narration.
6. **Re-freeze the screen-reader baseline** to add UTF-8 reads in `prototypes/lab_tracking/definition.py` (§7).
7. **Six-item manual acceptance** of screen reader v1: run it or record a waiver.

## 7. Pitfalls found on 18 October

- **Frozen files.** `scripts/check-screen-reader-baseline.py` requires the Python files listed in `docs/baselines/screen-reader-v1.manifest.json` to match byte for byte, and CI runs it. Changes to lab behaviour go in a non-frozen layer (as `prototypes/backend/lab_idempotency.py` does) or need a deliberate re-freeze.
- **Windows encoding.** The frozen `definition.py` reads JSON with the platform encoding, so Python tests, check scripts and kiki-web's lab Playwright server need `PYTHONUTF8=1` on Windows. The offline gate sets it itself.
- **FastAPI 0.141** keeps included routers as one nested route entry; frozen routes cannot be removed individually. `prototypes/backend/app.py` places its replacement first instead.
- **Origin must equal Host** for every backend write and WebSocket. kiki-web sets Origin to the configured backend origin; any proxy or tunnel must keep the Host header.
- **Git LFS.** Without it, `artifacts/cam-review/**/*.wav` arrive as pointer files and `scripts/verify-cam-review.py` fails.
- **Nested worktrees.** A kiki-web worktree inside another kiki-web checkout fails `src/fixtures/assessments.test.ts`, because the outer `package.json` changes module loading. Clean clones and CI pass.
- **Write files with explicit encodings and newlines.** Python's `write_text` on Windows writes CRLF and the ANSI code page by default.

## 8. Where the details are

| Topic | File |
| --- | --- |
| Next actions and what ran | [docs/plans/active.md](../plans/active.md) |
| Connected testing | [docs/plans/connected-integration-testing.md](../plans/connected-integration-testing.md) |
| kiki-web Lab mode status and open items | [kiki-web-lab-mode-screen-share.md](kiki-web-lab-mode-screen-share.md) §0 |
| Decisions | [ADR 0010](../decisions/0010-kiki-web-api-fronts-lab-execution.md), [ADR 0011](../decisions/0011-generated-content-reaches-kiki-web-through-the-database.md) |
| Backend API for frontends | [frontend-api.md](frontend-api.md), `contracts/frontend.openapi.json` |
| Hosting notes | `deploy/fastapi/README.md` |
| Floating windows | [floating-guidance-windows.md](floating-guidance-windows.md) |
| Concept library | [concept-canvas-continuation.md](concept-canvas-continuation.md), `prototypes/concept_library/README.md` |
