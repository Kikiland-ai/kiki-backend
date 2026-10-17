# Generated marks through actual paint — 17 October 2026

Version-18 live requests received many provider chunks but failed before a drawing commit; shorter failures were reported as `provider_timeout_or_network_error`. Their raw model output was not retained, so exact historical fields are unknown. No new paint receipt had been reached for those requests.

Two confirmed boundary defects are reproduced here:

1. The flat provider-generation schema required only `kind` and `cue_id`, allowed text marks without anchors, and allowed arbitrary strings in `text_ref`. A real Gemini probe on a controlled gain dialog emitted `text_ref: "Gain is set to 2"`. Both flat and typed-without-reference-enums responses failed the unchanged full validator. Adding only text-reference enums still produced a text mark without an anchor and failed. A compact typed union **plus** authored reference-key enums returned a valid box and anchored text.
2. The actual Worker routed strict `schema_oneOf` exceptions into its generic network catch, retried four keys and reported network failure. Validation guards now classify these as `invalid_output`, stop key failover and log only safe structural diagnostics. Observation text, supplied reference values, screenshots and keys are excluded from production rejection logs.

| Isolated real query | HTTP | Runtime validation |
| --- | --- | --- |
| Flat marks | 200 | Rejected: prose in text_ref |
| Typed marks | 200 | Rejected: prose in text_ref |
| Flat marks with text-ref enum | 200 | Rejected: missing text anchor |
| Typed marks with text-ref enum | 200 | Accepted: box and anchored text |

The corrected real model was then connected to **native getDisplayMedia → actual Worker → real Gemini stream → full validation/commit → actual consumer/compositor → independently checked blue pixels → signed persisted paint ACK** on the same controlled gain-dialog scene. It made one live model request and retained visible pixels at 1.5 seconds. `live-model-paint.json` and `live-model-worker.json` record that successful run. An initial unbound control/setup check is an explicit offline fixture; only the annotation request uses the real provider. The live case does not rerun the separate coherent-panel assertion (`coherent_panel_during_stream:false` means untested in this case); the existing UI/stream tests still cover it.

Six paid requests were made for this diagnosis: four isolated variants, one native attempt that validated the response but failed on a malformed local history precondition, and one corrected native attempt that painted. The failed native setup lacked history.scope; it is a test-fixture failure, not a provider or production tracker diagnosis. After paint, the one-request budget may reject subsequent automatic checks locally; no second live request was dispatched in that run. Existing API timeout/failover/cooldown settings are unchanged.

All 134 Node checks pass, including replay of all four actual model outputs, per-checkpoint generation constraints, strict unknown/unrelated target rejection, wrong-shape no-commit and one-key invalid-output classification. Exact controlled model samples are in `prototypes/json_stream_site/scripts/fixtures/generated-gain-guidance.json`; the controlled page is `gain-dialog.html`.

Limits: Chrome API dispatch is a fixture, and localhost TLS uses a labelled controller-origin substitution. This is real model localization on a controlled page, not actual Simulink/installed-extension acceptance. No learner image or response is archived. `controlled-query-image.jpeg` and `live-model-painted.png` contain only the authored fixture. No latency improvement or accuracy generalization is claimed.

To reproduce a bounded live annotation check from `prototypes/json_stream_site`, use the configured runtime key and inherited proxy/trust. Start `GUIDANCE_FIXTURE_LIVE_MODEL=1 GUIDANCE_FIXTURE_CLOCK_DB_DELAY_MS=650 node --use-env-proxy --use-system-ca scripts/serve-guidance-fixture.mjs --tls`, then run `python scripts/check-guidance-pipeline.py --tls --live-gain --check-readable` from that directory. Ephemeral localhost certificates and browser dependencies are local test prerequisites; no private material belongs in source. The fixture enforces a one-live-request budget. Ordinary tests make no paid calls.
