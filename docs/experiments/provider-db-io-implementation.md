# Provider database I/O experiment and automated acceptance

15 October 2026. Implemented on `experiment/provider-db-io`, isolated from the [experiment registry](latency-experiment-registry.json). Parent runtime is `d333908924a8edead0289967c517c2c0ce2fffa2`; prior private Site source is `958fd7fb4ae94e0af5ffe592a2fcb09f406af5fb`. New exact Site source: `c67fc3a5537ddcf98b8d8bfacbb606749687f693`. This arm changes routing storage work and adds measurement; it does not change the vision prompt or interpretation/progress rules.

The separate prepared branches `experiment/stream-context-batch`, `experiment/verifier-context` and `experiment/targeted-vision` all point at the registry commit `42afb87f48905734557411167bcad7c7e4506502`. Their implementations and deployments have not started. Frozen baseline, original JSON and TOON branches are untouched. Avoid cherry-picking this entire arm into them when comparing one variable at a time.

## What changed

The Python streaming provider uses one atomic SQLite upsert to acquire the router lease, one deduplicated cooldown snapshot per attempt and a single final success/release write. The hosted Worker uses the equivalent D1 SQL. The reserved cursor is still durable before HTTP; no consecutive key reuse is permitted with multiple configured keys. A 429 refreshes the snapshot before selecting another key, preventing a sibling in the same quota pool from being sent. Error/cancellation paths release the lease; 503 failover, full-cycle sixty-second cooldown, current retry/deadline and quota rules remain.

A healthy four-key request now needs **4 provider DB operations instead of 17**, and **3 before HTTP instead of 15**. The candidate's healthy count is constant for one through sixteen keys. Retry paths intentionally do extra work to persist faults and recheck shared quotas. This is a 76% reduction in healthy provider DB round trips, not a 76% reduction in model or end-to-end latency.

`KIKI_PROVIDER_IO=batched` is the default; `serial` restores the same routing control without switching prompt/model. Python's inherited nonstream `post` implementation stays frozen; the optimization applies to its streaming pool. The hosted adapter shares the optimized routing path for buffered and streaming requests. `/health.latency_experiment` identifies the arm and mode. No frontend endpoint, provider timeout or SSE version changed.

The three-field short-decision prompt remains SHA-256 `5dc012e6ebec4384d5bf2eaf20ce48c62abd53105b9bfb912aa63cc08a809711`. Authored criteria/action IDs, full JSON plus provider STOP, current frame/owner/visit/workspace/view/parameter/condition, two fresh matching frames and explicit learner confirmations remain gates. Partial rows remain tentative. Canonical now/next stays tracker-owned; rendering cannot complete a checkpoint.

## Measurement

Successful analyses now retain actual `input_tokens`, `cached_tokens`, `thinking_tokens`, `output_tokens`, `total_tokens`, image byte count and request text characters. Unavailable or malformed token counts are null, not zero estimates. Worker metadata additionally records provider-supplied token modalities when available. These fields come from provider usage metadata, not the generated findings schema.

Routing timings include `provider_io_mode`, `provider_db_operations`, `provider_db_ms`, HTTP attempt count, first/last dispatch offsets, header delay and HTTP consumption duration. Stream context validation independently records `context_db_reads` and `context_db_ms`; this arm does **not** batch those reads. HTTP consumption includes awaited parsing/context validation, so its time overlaps context reads; do not sum these as independent phases or describe `provider_ms` as isolated inference. Hosted failed analysis timings retain router metrics where an acquired request produced them; pre-acquisition/configuration failures may lack them. The frozen Python LabService does not persist exception routing metrics, although the streaming pool attaches them to exceptions. Complete Python failure telemetry is still an integration gap.

The retained [offline evidence](evidence/2026-10-15-provider-db-io-offline.json) reports both arms, all outcomes and injected delay. With artificial database RTT of 20 ms, three alternating trials per arm confirmed the query-count reduction. This deliberately simulated experiment makes zero API calls and establishes no deployed latency improvement. Production comparison still needs new admitted-to-committed samples against the recorded short-decision reference; no fresh real-user samples are manufactured here.

## Run regression without manually doing the lab

From the backend checkout:

```sh
python scripts/run-screen-reader-evaluation.py
```

This command builds the actual Worker bundle, runs all Python and Node suites, replays **all twelve checkpoints in both routing modes**, benchmarks routing with controlled DB delay and verifies pinned/frozen sources. It writes `work/evaluations/latest/report.json`, per-check logs and full replay/benchmark JSON, exits nonzero on any failure and removes provider credentials from offline subprocess environments. The report includes source revision/dirty state, Python/Node versions, fixture hashes, phase timings, command results and explicit synthetic/mocked-vision flags.

The full replay uses real owned HTTP capture, signed frame receipts, tracker mutation and SSE commit code with a local SQLite D1 adapter. Each checkpoint receives two different frame sequences. Simulated wrong settings interrupt step 3 and must reset support. Saving/identity and written responses require explicit simulated student actions; pixel matches alone cannot manufacture those reports. Replays never touch a live learner journal. Existing regression tests cover stale view/visit/provenance, disconnect, failed or non-STOP streams, blocked auxiliary tails, UI commitment, rotation/429/503/cooldown and concurrent leases. DOM stubs test client logic; they are not a real browser capture test.

For a bounded real-model recognition smoke, deliberately opt in:

```sh
python scripts/run-screen-reader-evaluation.py --live
```

This adds five analyses of the saved synthetic local-carrier images using server-side environment keys and the configured/default model. Every failure, mismatch or unknown remains in the report; all five expected outcomes must pass. Provider retries can mean more HTTP attempts than analyses. These narrow fixtures cannot certify recognition at every checkpoint. No new paid smoke was run for this DB-only arm because its model input/output is unchanged. Broader labelled real-screen recognition coverage, browser sharing and actual Simulink usability remain sampled release gates.

GitHub Actions workflow `screen-reader-evaluation.yml` runs the offline command on branch pushes, relevant pull requests and manual dispatch, with no API secrets. It retains reports for fourteen days even when a check fails. A failure in the replay or tests should be debugged from its artifact before asking the user to repeat a manual lab run. CI is configured; its first hosted run is not verified here. GitHub CLI run-list access returned Forbidden, and the available connected workflow-list tool filters to pull-request runs (none for this branch commit). Local acceptance is passing; no CI success is asserted.

## Verification and hosting boundary

Local checks pass: 112 Python tests, 69 Node tests, twelve checkpoints in each routing mode, database A/B, 130 pinned source hashes, 31 frozen Python/43 hosted baseline files plus original fixture/policy parity, lab design, 39 writer contract cases, BB8 validation/discovery/twelve reference tests. Exported OpenAPI remains unchanged at 29 HTTP paths. No runtime schema or writer contract is broken.

The live experimental Site remains Worker/D1. Python FastAPI is implemented and tested in this branch but not cloud-hosted. Browser-control tooling is unavailable, so native Simulink sharing/overlay acceptance is not claimed. Keep the user's existing keys, private audience and saved state. Roll back routing with server-side `KIKI_PROVIDER_IO=serial` followed by the Site's normal environment deployment, or republish the saved prior Site source. No database migration or learner reset is required.

Publication succeeded: `appgdep_6ad019222c308191b14bd7e3b41d19a9`, saved version `appgprj_6acfd4c6e6e48191b9110067ba86d556~appgver_3e3f9ce91a9c819198e7b36a25b7a7b6`, environment revision 8, MCP true. Existing private URL: https://kiki-json-stream.woodsycarp256.chatgpt.site . Native deployment success verifies publication; it is not a browser/Simulink acceptance result.
