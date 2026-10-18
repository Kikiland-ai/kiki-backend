# Connected integration testing: kiki-web and kiki-backend across machines

18 October 2026. This is a plan for testing kiki-web Lab mode against this repo's Python service when the two run on different machines, for example one teammate runs kiki-web and another runs kiki-backend. Nothing here has been run yet. kiki-web facts are from `origin/main` at `0ed7c06`; kiki-backend facts are from `main`.

## Why a plain LAN address does not work

kiki-web's API accepts only two backend origins (`apps/api/src/kiki_api/config.py:24-42`):

- **local mode:** exactly `http://127.0.0.1:8100`;
- **cloud mode:** any `https://` origin that is not loopback and has no path, query or trailing slash.

So `http://192.168.x.x:8100` is rejected. The backend must either appear on `127.0.0.1:8100` of the kiki-web machine (an SSH forward), or be reached over HTTPS (ngrok or Tailscale).

The browser has its own rule: screen capture (`getDisplayMedia`) needs a secure context. `http://127.0.0.1` and `http://localhost` qualify; `http://<LAN IP>` does not. The tester's browser should therefore be on the kiki-web machine, or reach kiki-web over HTTPS.

## Constraints every setup must meet

| Check | Where | What it means for a tunnel |
| --- | --- | --- |
| Proxy guard | `prototypes/screen_capture/server.py:349-350`, `cloud_access.py:19-23` | Only active when `KIKI_PROXY_SECRET` is set. Always run with `KIKI_REQUIRE_PROXY=1`, which refuses to start without a 32+ character secret (`server.py:116-117`); otherwise ownership falls back to a cookie anyone can create |
| Origin must equal Host | `server.py:34-38` (compares host and port, ignores scheme), mutations at `:142-144`, WebSocket at `:245` | kiki-web sends `Origin` = the configured backend origin (`lab_upstream.py:24`). Through ngrok, keep the default host header so Host is the public ngrok host. **Do not use `--host-header=rewrite`**: every mutation returns 403 and the WebSocket closes with 1008 |
| No redirects | `lab_upstream.py:36` | Use the exact HTTPS origin; ngrok does not redirect it |
| Streaming | `json_stream/api.py:90` sends `X-Accel-Buffering: no` | Check that `check-stream` chunks arrive incrementally through the tunnel |
| WebSocket | `lab_upstream.py:75-78` turns the origin into `wss://` | ngrok and Tailscale both carry WebSockets |
| Extension origins | kiki-backend `prototypes/floating_guidance/scripts/build-extension.mjs:9-12` has no kiki-web origin; kiki-web `apps/web/scripts/build-lab-test-extension.mjs:9` has `http://127.0.0.1:5174` | For a trial today, use kiki-web's test extension build, or add `http://127.0.0.1:5174` to this repo's dev `readers` (an open next action) |
| MATLAB binding | kiki-web `floating-bridge.ts:9` | Binds only to `https://matlab.mathworks.com` |
| kiki-web web port | `apps/web/vite.config.ts` (5173, strict), `package.json:11` (`--host 127.0.0.1`) | Start with `npm run dev:connected -- --port 5174`, because the API's CORS default is `127.0.0.1:5174`/`localhost:5174` (`config.py:22`) |
| Single API worker | kiki-web WebSocket tickets are in memory | Run kiki-web's API with one worker |
| Firebase sign-in | Firebase project `builder-cup-a8479`, Authentication → Authorized domains | Only matters if testers open kiki-web on a tunnel host; a project Owner must add that host |

## Setups, in order of preference

### 1. SSH forward: kiki-web stays in local mode, no config change

Backend machine (M2):

```sh
KIKI_PROXY_SECRET=<secret> KIKI_REQUIRE_PROXY=1 GEMINI_API_KEY=<key> \
  python -B -m prototypes.backend --port 8100 --data-dir work/backend
```

It binds to `127.0.0.1` by default (`prototypes/backend/__main__.py:9`). M2 needs an SSH server (Windows: the OpenSSH Server optional feature).

kiki-web machine (M1):

```sh
ssh -N -L 127.0.0.1:8100:127.0.0.1:8100 <user>@<M2>
```

Then kiki-web uses `KIKI_LAB_EXECUTION_MODE=local`, `KIKI_LAB_BACKEND_ORIGIN=http://127.0.0.1:8100` and `KIKI_LAB_PROXY_SECRET=<secret>`. Host and Origin are both `127.0.0.1:8100`, and nothing is exposed publicly.

### 2. ngrok: backend over public HTTPS, kiki-web in cloud mode

M2 runs the same backend command, then:

```sh
ngrok http 8100 --url=<your-static-domain>.ngrok-free.app --inspect=false
```

M1 sets `KIKI_LAB_EXECUTION_MODE=cloud` and `KIKI_LAB_BACKEND_ORIGIN=https://<your-static-domain>.ngrok-free.app` (no trailing slash), with the same secret.

- Every call to the backend comes from kiki-web's API (server to server), so ngrok's browser warning page does not apply.
- Use the free static domain so the origin does not change between runs.
- `--inspect=false` keeps ngrok's local inspector from recording the proxy key and screen frames.
- ngrok terminates TLS, so it can see student screens. Use test accounts and non-sensitive screens only.
- Optionally restrict callers to M1's public IP with an ngrok traffic policy. Basic auth would break the API's calls.
- The free tier has monthly data limits. Frames are up to 1 MB about every 2 s, so long sessions use the allowance quickly.
- Neither ngrok nor Tailscale is installed on the current Windows machine yet.

### 3. Tailscale: a real shared private network

Tailscale puts both machines on one private network (a tailnet) without public exposure. It is the closest match to "same subnet".

- Backend only: on M2, `tailscale serve --bg 8100` gives `https://<m2>.<tailnet>.ts.net` with a real certificate. kiki-web uses cloud mode with that origin. Before the trial, check with a `curl` POST that Host is preserved (Origin must equal Host).
- Remote testers opening kiki-web too: on M1, serve the web app (443 → 5174) and the API (for example 8443 → 8000). Then set:
  - `KIKI_CORS_ORIGINS` to the `ts.net` origin;
  - `VITE_API_BASE_URL` to the API's `ts.net` origin;
  - Vite `server.allowedHosts` (and possibly `hmr.clientPort`) in kiki-web `vite.config.ts`;
  - the `ts.net` host in Firebase Authorized domains and in the extension `readers`.

  Do not use ngrok for this case: the browser warning page, an extra CORS header and Firebase domain churn all get in the way, and the app would be public.

## Security rules for any tunnel

- Never expose the backend without `KIKI_REQUIRE_PROXY=1` and a fresh secret; rotate the secret after the trial.
- The proxy secret stays server side in both repos; never in a `VITE_*` variable.
- The Gemini key stays on the backend machine only.
- Never tunnel the Firebase emulators.

## Runbook: first connected trial

1. M2: pull `main`, create a venv and `python -m pip install -r prototypes/screen_capture/requirements.txt`.
2. M2: create a secret with `python -c "import secrets; print(secrets.token_urlsafe(32))"` and share it privately.
3. M2: start the backend on port 8100 with `KIKI_REQUIRE_PROXY=1`, the secret and the Gemini key.
4. M2: `curl http://127.0.0.1:8100/health` succeeds; a `POST /screen-sessions` without the key returns 401.
5. Connect: the SSH forward (setup 1), or start ngrok / `tailscale serve` (setups 2 and 3).
6. M1: `curl <backend origin>/health` succeeds through the forward or tunnel.
7. M1: pull kiki-web `main` and set the lab mode, origin and secret for the chosen setup.
8. M1: start kiki-web's API on port 8000 with one worker, then `npm run dev:connected -- --port 5174` in `apps/web`.
9. M1: build and load the extension: kiki-web's `apps/web/scripts/build-lab-test-extension.mjs`, or this repo's dev build once `127.0.0.1:5174` is in its `readers`.
10. M1: sign in at `http://127.0.0.1:5174`.
11. Open MATLAB Online in another tab and bind it from the extension popup.
12. From `/labs/:sessionId`, start screen guidance and share the MATLAB tab (choose a Chrome tab).
13. Confirm frame acknowledgements, then attach, then that `check-stream` chunks arrive one by one. Watch M2's log for 401, 403 or 1008.
14. Pause and resume from the page and from the windows, then stop; the backend lab should end in `ended`.
15. Rotate the secret, close the tunnel, and record results, latency and any errors in `docs/plans/active.md`.

## Automated checks to add

- **Backend smoke script (this repo):** with the proxy headers and `Origin` set to the tunnel origin, run `GET /health`, `POST /screen-sessions`, a WebSocket `capture_started` plus one fixture JPEG frame, `POST /lab-sessions`, `/attach`, and `/check-stream`, asserting that SSE chunks arrive incrementally. Model it on `tests/test_unified_backend.py`. It tests a tunnel without kiki-web.
- **kiki-web lab Playwright test against a real backend:** `playwright.lab.config.ts` starts a fake analyzer server with `../api/.venv/bin/python` (POSIX only; Windows needs `.venv\Scripts\python.exe`). It needs a switch to skip that server and use `KIKI_LAB_BACKEND_ORIGIN`, and a Firebase ID token from the auth emulator (`demo-kiki-local`).
