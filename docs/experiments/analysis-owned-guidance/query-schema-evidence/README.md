# Checkpoint-specific query rejection — 16 October 2026

The Site's recent logs showed timeouts followed by a Gemini HTTP 400, not a 503. D1 confirmed the inherited 15-minute model cooldown after that 400. The generic UI wording described both as waiting/retrying.

Eight bounded isolated requests used the deployed query builder, a constant-colour synthetic JPEG and the managed cloud's configured Gemini key. They did not read masked Site keys, use the learner's pixels or mutate the live tracker. Complete outcomes and limits are in `manifest.json`.

| Query | HTTP | Total time | Result |
| --- | --- | --- | --- |
| CP-01 control | 200 | 3.212 s | Complete STOP, actual parser passes |
| CP-01 drawing | 200 | 6.258 s | Complete STOP, full drawing validator passes |
| CP-06 control | 200 | 27.639 s | Complete STOP, actual parser passes |
| CP-06 drawing | 400 | 0.980 s | INVALID_ARGUMENT |
| CP-06 original repeated | 400 | 1.272 s | Same INVALID_ARGUMENT |
| CP-06 without string bounds | 400 | 0.811 s | Same INVALID_ARGUMENT |
| CP-06 without target-ID enums | 200 | 3.301 s | Complete STOP, unchanged full drawing validator passes |
| CP-06 without array bounds | 200 | 2.473 s | Complete STOP, unchanged full drawing validator passes |

Actual 400 body: `{"error":{"code":400,"message":"Request contains an invalid argument.","status":"INVALID_ARGUMENT"}}` (formatting in response file). This is query rejection before a model result, not malformed generated JSON. The exact provider-internal rejection rule is not disclosed. Two independent schema simplifications resolving it support a schema-constraint/complexity interaction; the smaller target-enum change was selected.

The fix changes five nested `target_id` generation schemas to `type:string`. It preserves exact authored IDs in the prompt catalogue, criterion/action enums, numeric geometry bounds, array cardinalities and the complete final typed/semantic validator. Unknown IDs and globally valid IDs that belong to a different action are still rejected. No producer contracts, extension changes, checkpoint rules, cooldowns or timeout/failover settings change.

`node-tests.txt` records 126 passing Node checks. Twelve new offline cases construct the real query and commit fixture guidance for every checkpoint; each verifies unknown and wrong-action target rejection. These are distinct from the eight paid API samples. Real Simulink localization and installed-extension placement remain separate acceptance work. The existing eight-second per-key attempt can still time out when the provider is slow; this change does not establish a latency improvement.
