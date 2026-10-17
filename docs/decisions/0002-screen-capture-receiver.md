# First screen-awareness slice: frame receiver

Date: 13 October 2026 · Status: locally implemented; user-browser access check pending

## Decision and authority

The user requested starting the MVP with the concrete outcome: select Share screen and have a small server receive data showing the shared surface. This authorizes implementing/running/testing the isolated capture receiver. It does not require building every part of the earlier plan in this slice or authorize commit/push/deployment.

Use browser getDisplayMedia and binary JPEG frames over WebSocket at 0.5 Hz. FastAPI serves the page and session endpoints. SQLite stores receipt metadata/events; the latest actual image stays in memory. This operationalizes the image-first recommendation for the first slice. Video/WebRTC comparison remains future work if temporal requirements justify it.

## Resulting behavior

The page displays local shared video and the image retrieved back from the server. Frame counts and JSON update only after actual server receipt. Native stop, explicit stop, pause/resume and receiver disconnection control sending. JPEG format/dimensions/size and envelope order are validated; hashes and timestamps establish frame provenance. The client has one in-flight frame and the server limits admissions.

Semantic analysis is explicitly not enabled: latest JSON uses screen-receiver/v1, frame_receipt mode, null summary and not_enabled analysis status. Receiving pixels is not screen understanding or verified practical evidence. The next slice can introduce screen-awareness/v1 with an evaluated vision worker without pretending this metadata already describes the screen.

## Scope tradeoff

Persisting only metadata and the latest in-memory image avoids creating a cloud archive before its value is measured. Past image hashes do not allow visual replay. The earlier build document's proposed raw-evidence/history TTL, durable distributed coordinator, model processing and storage packs are not implemented. Trial limits are 30 minutes, 16 open sessions and 100 total records per data directory. Browser ownership is an HTTP-only random capability cookie, not account authentication.

## Access and verification boundary

Run on a laptop's localhost or the environment's authenticated HTTPS port preview. Remote HTTP will not provide native capture in a secure browser context. The cloud runtime currently exposes no callable port-preview creation tool; its running localhost service is not the user's laptop localhost. A public tunnel/deployment is not implied.

The controlled Chromium test uses the native tab-capture API with automatic selection of a fixture tab. It proves capture, changed pixels, transmission, received-image rendering and lifecycle within this runtime. The user's actual chooser/screen and any remote forwarding still need the user-browser check. No paid model call is needed for the receiver.

Implementation: [receiver README](../../prototypes/screen_capture/README.md), [runtime contract](../../contracts/screen_capture.py), [full design](../architecture/screen-awareness-mvp-build.md) and [plan](../plans/screen-awareness-mvp.md). Exact checks/results are recorded in [active continuation](../plans/active.md).
