# Isolated latency experiments and automated evaluation

15 October 2026. The user asked to treat the identified bottlenecks as separate experiments, start with maximum leverage, and replace repetitive manual regression testing. The immutable starting point is `d333908924a8edead0289967c517c2c0ce2fffa2`, Site source `958fd7fb4ae94e0af5ffe592a2fcb09f406af5fb`. Read the [machine-readable registry](latency-experiment-registry.json).

| Order | Experiment / branch | Scope | Gate |
| --- | --- | --- | --- |
| Now | `provider-db-io/v1` / `experiment/provider-db-io` | Reduce provider-router database round trips without changing model input/output or progress rules. | Exact key/429/503/cooldown/lease semantics; bounded query count; deterministic A/B with injected latency; isolated real-user metrics. |
| Next | `stream-context-batch/v1` / `experiment/stream-context-batch` | Reduce per-finding context reads. | Changed views/visits/pause and late chunks still cannot commit or revive guidance. |
| Next | `verifier-context/v1` / `experiment/verifier-context` | Verifier-specific inputs without lesson/help/UI duplication. | Exact authored IDs/values/rules, held-out recognition accuracy and full token accounting. |
| Later | `targeted-vision/v1` / `experiment/targeted-vision` | Requested targets and context-preserving crops. | Explicit requested-target contract, crop provenance/transforms and expanded positive/negative screen corpus. |

Prepare separate branch references from this registry commit; implement and promote only the first arm now. The three prepared arms must not be represented as implemented or live. Token/phase telemetry and the automated runner are shared measurement infrastructure, not evidence of a separate prompt win. Python/FastAPI remains the backend source of truth; the hosted Worker/D1 adapter is tested against its contract. The original buffered baseline/JSON/TOON references stay intact.

## Automated testing boundaries

1. **Offline mechanics:** replay controlled finding sequences through the real owned receiver/tracker/SSE/UI code, including a complete authored lab sequence, two-frame support, explicit student confirmations, wrong settings, pause/revisit, stale response, disconnect, failed key sweeps and recovery. Provider outputs are mocked and labelled. This tests orchestration, not whether the vision model read real pixels correctly.
2. **Offline performance:** run serial and batched provider routing with the same key pool, responses and injected database RTT. Record measured elapsed time and round trips for both arms. Simulated delay demonstrates removed serial work; it is not a hosted latency estimate.
3. **Vision acceptance:** explicitly opt in to a bounded live replay on the labelled saved synthetic screenshots, recording exact image/prompt/request hashes, actual input/output/cache/thinking usage and every timeout/unknown/mismatch. No live model calls in default CI. The initial five-case corpus is narrow; it cannot certify all twelve steps or broad Simulink recognition.
4. **Native integration/usability:** occasional real Simulink Online sharing remains necessary for permissions, actual screen layouts and whether instructions are understandable. This becomes release acceptance, rather than asking the user to rerun the lab for every code edit.

The runner must return a nonzero exit code on acceptance failure and write a machine-readable report with source revision, environment/model/arm, fixture hashes, outcome denominators and timing boundaries. CI runs the free offline checks and retains diagnostic reports. No credentials, learner screenshots, raw provider response bodies or user journals enter artifacts. Keep all failed and slow outcomes; do not manufacture a speedup by comparing only selected successes.

## Observation before implementation

Local inspection reproduced 17 sequential provider database operations for four configured keys, including 15 before the outbound request. The current stage-7 request contains approximately 14,206 text characters excluding its image, including 3,106 procedure characters and 3,712 full-model characters. Actual input-token counts were not retained. Current `provider_ms` also includes router/storage and per-finding context awaits, so it must not be described as isolated Gemini inference. These findings motivate the arms; they are not yet a deployed improvement.

## Completion criteria for the first slice

- Same model/prompt/schema, keys, quota grouping and two-frame/current-context rules.
- One bounded health snapshot per routing attempt, not a scan of three queries per key; preserve rechecks after a failure so a 429 immediately blocks siblings.
- Atomic lease acquisition and crash cursor reservation before HTTP; release on success, cancellation and exceptions without permitting concurrent callers.
- Separate provider DB count/time, pre-HTTP routing, header/stream duration and actual usage metadata.
- Runnable offline reports and CI, with explicit distinction between mechanism, vision and native acceptance.
- Publish only after checks pass; preserve Site audience, sessions, secrets and schema. Revert `KIKI_PROVIDER_IO` to `serial` or the saved prior source to roll back the isolated arm.
