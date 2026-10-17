# Screen sharing receiver MVP

This is the first implemented screen-awareness slice: select **Share screen**, choose a tab/window/screen, and see the image actually received by a small FastAPI server every two seconds. The page displays local video preview, the server-returned image, receipt statistics and JSON. Pause, resume and native/browser stop are supported.

Capture receipt endpoints still report pixels/provenance without lab interpretations. The same FastAPI app now includes the [Python DSB-SC analysis and reviewed-progress pipeline](../lab_tracking/README.md), with a separate lab observation JSON and browser controls. Capture needs no model key; lab checks require server-side `GEMINI_API_KEY`. No live tool overlay is implemented.

## Run on your laptop

From this repository root, using Python 3.12:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r prototypes/screen_capture/requirements.txt
.venv/bin/python -m prototypes.screen_capture --port 8765
```

Open **http://localhost:8765**, select **Share screen**, and choose a different tab/window or your screen. Check that the received frame count increases and the right-hand image shows your selection. Open the JSON endpoint using the page's link. A normal HTTP localhost page is a browser secure context; remote plain HTTP is not sufficient for getDisplayMedia.

On Windows use `.venv\Scripts\python.exe` in place of `.venv/bin/python`. To run tests, also install `httpx` in that environment and run `python -B -m unittest discover -s tests -v`. Browser smoke tests use Playwright and an available Chromium executable; they are separate from the Python test suite.

## Run in the cloud workspace

```sh
python -B -m prototypes.screen_capture --host 0.0.0.0 --port 8765 --data-dir work/screen-capture
```

Open the environment's authenticated **HTTPS port preview for 8765**, if it provides one. The proxy must preserve cookies, Host/Origin and WebSocket upgrade and pass trusted scheme information for HTTPS. Use the URL it actually returns; localhost in your laptop browser refers to your laptop, not the cloud workspace. No port-preview URL or deployment has been established by this code alone.

If the environment has no HTTPS preview, run on your laptop instead. Opening the HTML as a file or a remote HTTP URL cannot provide the same working capture/API origin. No public tunnel, cloud provisioning or deployment is included.

## Endpoints and wire protocol

| Endpoint | Behavior |
| --- | --- |
| GET / | Capture page and an HTTP-only browser-owner cookie |
| GET /health | Receiver readiness, frame mode and sample cadence |
| POST /screen-sessions | Same-origin browser owner creates a session; returns stream path and limits |
| WS /screen-sessions/{id}/stream | Lifecycle JSON and ordered frame metadata / binary JPEG pairs; server acknowledgments |
| GET /screen-sessions/{id}/observation | Current receipt JSON, count and dynamically computed freshness |
| GET /screen-sessions/{id}/frame | Actual latest JPEG with frame-sequence header; 410 after pixels are unavailable |
| GET /screen-sessions/{id}/events?after=0&limit=100 | Ordered metadata history and next cursor |
| POST /screen-sessions/{id}/stop | Idempotent stop; discard server image bytes |

Frame metadata is validated by [the runtime contract](../../contracts/screen_capture.py); images use JPEG, preserve aspect ratio, have a maximum dimension of 1600 px and are capped at 1 MB. Actual decoded image dimensions and format must match metadata. The server computes SHA-256 over received bytes. An acknowledgment means **received**, not semantically analyzed.

Lifecycle messages are `capture_started`, `pause`, `resume`, `stop` and `heartbeat`. The browser sends at most one frame awaiting acknowledgment; the server independently limits admissions. Frame order/capture time must increase, exact retransmissions are idempotent, and conflicting/invalid input disconnects the producer. One producer per session is allowed.

## Retention, scope and limitations

Only the latest JPEG per active session lives in server memory. Stop/disconnect/restart removes it. SQLite under ignored `work/screen-capture/` stores session state and append-only receipt events, including hashes, server receipt times, client-relative capture times, sequence gaps and original/encoded dimensions. No historical raw screenshots, video or cloud objects are stored. A hash alone cannot reconstruct an old screenshot.

Sessions have no fixed duration or historical record count cap. Explicit stop ends a session; disconnected producers can reconnect. Per-frame size, cadence, ownership and one-producer validation remain. Automatic metadata TTL, adaptive frame selection, event compaction and archived evidence are future slices; do not assume the broader build document's proposed 24-hour/7-day retention is implemented here.

The HTTP-only random owner cookie isolates prototype sessions and same-origin checks guard mutations/WebSocket handshakes. It is a prototype capability, not a signed-in Kiki account or production identity. Run one API process; use an authenticated preview when forwarding. Source switching starts a new share/session; device handoff and a durable distributed coordinator are not implemented. New sessions do not resume an unsaved external tool state.

No frames are sent until native sharing is granted. Server disconnection stops client capture; a slow acknowledgment aborts sharing rather than building a backlog. Pause stops uploads while the browser's capture grant remains active. Stop ends native capture. Closing the page disconnects; server metadata records that gap. Sampling at 0.5 Hz can miss events between frames.

## Validation and next slice

Python tests exercise real JPEG bytes, provenance, ownership, corrupt/mismatched input, duplicates, frame limits, pause/resume, stop, disconnect, restart and capture-clock ordering. A separate Chromium smoke test exercises native tab sharing and the actual server-returned image; automated source selection does not substitute for a real user's chooser/device test.

Next: verify the first real Simulink checkpoint through a reachable Python deployment. The bounded analyzer, reviewed queue and durable lab journal are implemented separately from receipt JSON; see the lab README for actual routes and checks. Reuse [the observation plan](../../docs/plans/screen-awareness-mvp.md) and [full build design](../../docs/architecture/screen-awareness-mvp-build.md); do not label receipt metadata as model understanding.
