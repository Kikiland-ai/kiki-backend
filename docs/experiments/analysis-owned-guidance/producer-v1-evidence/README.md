# Producer v1 offline evidence

These are retained **synthetic offline** records, not live model, screen-localization, Site-delivery or Simulink-paint measurements. No API calls were paid for. See the [implementation handoff](../../../handoffs/analysis-owned-guidance-producer-v1-build.md).

- `timings.jsonl`: raw stage records for ten paired cases (twenty requests); model tokens remain null because the transport is mocked. Includes run/request IDs and a Python source fingerprint.
- `comparison.json`: metric denominators, medians, p95, outcomes and pairing. Both arms passed all ten requests. The larger drawing request is a real input-size cost; millisecond replay timings do not predict provider latency.
- `acceptance.json`, check logs and `reader-regression-report.json`: schema parity, fifty reference cases, eleven isolated Python tests, eleven Worker tests, paired replay and the full reader suite. The full reader suite includes 117 Python and 98 Node tests.
- `final-*`: producer-only checks/replay rerun after the final live-proof review; the raw trace/comparison come from this final replay.
- `manifest.json`: integrity hashes for the retained data/log files; its parent commit is the published proposal. Dirty-working-tree/source-fingerprint metadata is intentional because checks ran before the implementation commit.

Run `python scripts/run-guidance-evaluation.py --full` for fresh artifacts. Future live comparison needs matched runtime/model/configuration, actual provider tokens/retries and separately correlated renderer paint ACKs. Rendering has no checkpoint authority.
