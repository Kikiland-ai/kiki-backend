# Hosted screen-writing delivery correction — 17 October 2026

The user reported practical steps advancing with no visible annotations. The inspected live stream contained **five rejected receipts, eleven cancellations and zero verified paints**, despite successful `lab-observer-drawing/v1` analysis commits. Historical clients replaced the actual rejection reason with `consumer_validation_failed`; do not attribute every prior rejection to a specific stage retrospectively.

A controlled native-browser reproduction introduced **650 ms of server DB delay** in the owned clock route. With legacy send-only timestamps, the real consumer rejected drawing as excessive clock uncertainty and produced no paint. With receive/send timestamps, the same processing delay is excluded from the network uncertainty interval: the real compositor painted independently checked blue pixels, signed its ACK, and the Worker persisted it. Blue pixels remained visible at 1.5 seconds. Moving the source target immediately before paint still rejected the cue and persisted the actual reason.

The correction retains the 250 ms uncertainty cap and accounts for integer timestamp rounding. It does not increase packet lifetime, the 500 ms presentation reservation or API timeouts. The UI's automatic next check now waits up to 2.5 seconds after actual paint, bounded by original expiry and preempted by source/context change. This prevents analysis-start cancellation from immediately erasing a fresh cue. Manual checking still runs on request.

- `live-summary.json`: sanitized current-stream receipt counts and analysis timings; no learner pixels, answers or credentials.
- `clock-before.json`: expected reproduced no-paint failure.
- `clock-after-readable.json`, `clock-after-worker.json`, `controlled-painted.png`: native capture/stream/compositor proof after correction, including readable interval and signed exposure.
- `view-change-*`: stale geometry still rejects after final verification.
- `node-tests.txt`: 129 passing checks, including clock bounds, foreign ownership, malformed timing, every checkpoint's target restrictions and the actual UI's bounded recheck scheduling.

Chrome API dispatch and localization are explicit fixtures. The browser test uses localhost TLS and a test-only controller origin substitution; it does not establish installed-extension or real-Simulink recognition/placement acceptance. Actual learner pixels were viewed transiently to understand the reported lab screen and are not archived here. No paid model calls were made for this correction.
