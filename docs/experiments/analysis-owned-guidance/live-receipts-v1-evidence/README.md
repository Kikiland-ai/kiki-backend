# Live receipt and source lifecycle evidence

17 October 2026. See [the handoff](../../../handoffs/screen-writing-live-receipts.md).

- `hosted-deliveries.json`: v21 non-cancellation receipts, selected by deployed backend revision; 2 paints, 10 pixel rejections, 4 combined source-admission rejections. No owner identifiers, secrets or image bytes.
- `lifecycle-before.txt`: all three actual-controller regressions fail against pre-fix source. The initial fixture message-identity setup issue was corrected before collecting this result.
- `node-checks.txt`: all 144 final runtime checks pass, including the same three regressions after repair and the current-cue trace field check.
- `native-positive.json`: native tab capture, delayed streaming analysis fixture, actual Worker/broker/consumer/compositor, signed persisted paint, independently checked blue pixels still visible after 1.5 seconds, valid mark/expiry diagnostics.
- `native-negative.json`: moving the view between verification and paint yields a persisted rejection and no paint ACK.

Chrome API dispatch and model localization are explicit fixtures. These checks establish neither installed-extension acceptance nor actual running-Simulink visibility. No paid model requests were made. User screenshots and the raw uploaded browser trace remain in ignored work/attachment paths. An initial browser invocation lacked the fixture server TLS flag and failed before analysis; application acceptance was run after correcting setup.

The prior model localization gate remains failed; this follow-up does not relax it. Remaining live pixel-change attribution and the user's missed paint remain unresolved. Deployment receipt follows publication.
