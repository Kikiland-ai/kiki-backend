# Writing prompt v2 evidence

Controlled test images only; none are the two MATLAB screenshots attached in the current chat.

- `results.json`: six actual Gemini requests, all HTTP 200 and contract valid. Both arms use identical source/schema hashes. `pass` includes the experiment's text-only preference for the hidden target; baseline omission is permitted by the public contract.
- `*.model.json` and `*.response.txt`: complete actual controlled outputs and streaming responses. No model instructions are taken from these files at runtime.
- `node-tests.txt`: 138 passing Node cases, including strict rejection of missing anchors, prose and foreign references, prompt-example validation, twelve checkpoint request checks prompt-version propagation and a stalled-encoder capture-mask regression.
- `live-pipeline-*`: real-model native-capture/reader/Worker/consumer/compositor replay, actual pixel and signed delivery checks. Chrome APIs are explicitly dispatched by a fixture; `real_simulink_tested` and `installed_extension_tested` remain false. The live-gain case does not assert coherent observation-panel streaming; the separate existing controlled tests cover that behavior.
- `first-pipeline-*`: earlier connected run before correcting its fixture-only delivery sample label. Model trace is `live_provider`, but ACK label was accidentally `offline_replay`; correlate by request ID. This is not a production transport defect.
- `capture-mask-gap-*`: the second connected run, including a failed screenshot assertion despite a prior signed ACK. Ink was hidden during asynchronous JPEG encoding. This failure was retained and led to a separate capture-order correction.
- `offline-panel-*`: separate delayed fixture-provider browser check passes coherent panel streaming while four periodic frames arrive, real pixel visibility and persisted ACK; no paid model calls.
- `stale-view-*`: native view invalidation between verification and paint produces no paint ACK and persists the rejection.
- Automatic subsequent checks exhaust the deliberate one-call fixture budget and are retained as failed stub attempts, not Google API errors or additional paid requests.

Nine actual provider requests: six A/B plus three connected runs. There were no retries of the six A/B requests and no prompt revisions after seeing their outputs. The third connected run passes restoration-before-encoding and 1.5-second actual pixel checks (3,629 ms analysis-to-commit; 122.5 ms consumer-receipt-to-paint); do not count the second run as a passing readability check. The first connected run took 3,538 ms from local analysis start to tracker commit and 93.1 ms from consumer receipt to paint; it is a controlled local sample, not production latency or cross-clock subtraction.

The added field contract costs about 800 input tokens in this small evaluation. No statistical improvement in generation reliability or latency is claimed. Existing v19 generation schemas already prevented the historical invalid outputs in this comparison. Full validation and source/context safety are retained.

Reproduction from the backend prototype directory:

```sh
node scripts/build.mjs
node --test scripts/test-*.mjs
node --use-env-proxy --use-system-ca scripts/evaluate-writing-prompt.mjs --live
```

The last command sends at most six real requests using the configured runtime Gemini credential. It is separate from free CI. Connected browser reproduction uses the existing `serve-guidance-fixture.mjs --tls` and `check-guidance-pipeline.py --tls --live-gain --check-readable` with the environment flags described in the handoff. Preserve source images as controlled fixtures and do not label these results as testing the user's actual screenshots.
