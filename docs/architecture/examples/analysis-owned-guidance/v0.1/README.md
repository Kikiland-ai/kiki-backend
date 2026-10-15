# Synthetic contract fixtures — analysis-owned-guidance/v0.1

All geometry is authored on a constant-colour 96 x 54 JPEG. No fixture represents the user's screen, a detected Simulink control, an actual paint or an integration pass.

Read [the producer proposal](../../../../handoffs/analysis-owned-guidance-producer-v0.1.md). Model files validate against `contracts/lab_observer_drawing.v1.schema.json`; input/committed/cancel files validate against `contracts/analysis_owned_guidance.v0_1.schema.json` with the pinned local v0.2 schema registered. `trusted.*.json` are test-runtime records; `ordering.trace.json`, `negotiation.proposed.json` and `acceptance-report.json` are labelled metadata rather than wire packets.

Run from repository root:

```sh
python scripts/check-analysis-owned-guidance-contract.py
```

Negative context examples can be shape-valid: do not confuse JSON Schema acceptance with authoritative current-context/frame/action/expiry/ordering validation. The checker exits nonzero if a forbidden case is accepted. Renderer/compositor and production parser acceptance remain separate.
