# Experiment B — TOON streaming

Status: prepared, not implemented or deployed. Baseline: `681ad52d37ac0bfced86ceadeaaed6ef8128caf5`. Branch: `experiment/screen-reader-toon-stream`.

## Hypothesis and controlled change

TOON tables may reduce repeated field-name tokens and expose complete actionable rows sooner. Decode them into the exact same authored-ID JSON observation used by the baseline. Compare to both nonstreaming baseline and the independent JSON stream; a smaller token count is not evidence of faster verified progress.

The rejected positional compact trial is not this experiment. Never replace stable IDs with row positions or interchange Carrier and Local carrier. Every criterion/action status/evidence and critical uncertainty stays present. Provisional rows cannot mutate support/progress; wait for complete validated provider STOP and current context.

## Build next, in order

1. Read the baseline, frontend handoff and shared protocol. Preserve the original JSON analyzer as a callable baseline. Keep capture/model/thinking/context/budget/cadence/quota settings identical across arms.
2. Select/pin an actual TOON decoder and declare the exact supported grammar/version. Review canonical quoting, comma/newline escaping, multibyte text, table row counts, field types and ordering before claiming streaming support. A generic line split is insufficient. No TOON dependency is currently installed by this branch.
3. Design versioned full-ID tables for `criteria` and `action_findings`, plus bounded summary/uncertainties. Retain literal status words `match`, `mismatch`, `unknown` initially; reduce representation without hiding meanings. Specify required row counts from the authored current checkpoint, reject duplicates/foreign/missing IDs and unknown fields, then map to `LabAnalysis` and the same semantic validator.
4. Add a separate Python TOON streaming analyzer/transport and experimental router. Gemini responseJsonSchema currently constrains JSON; TOON needs its own prompt/parser enforcement, so record this confound explicitly. Preserve durable provider routing, deadlines and cancellation rather than silently leaving the baseline key pool. Reuse `LabService.check` admission/final validation/save, with a per-request tentative-event sink if needed.
5. Use the same downstream trusted event envelope, cancellation/ordering/client behavior and metrics as experiment A. Provisional complete rows remain outside scientific evidence. A declared TOON row count or end marker is not provider STOP.
6. Pass identical offline safety/semantic/replay gates and existing suites before a deliberately resumed provider smoke/trial. No provider call, dependency installation or deployment is triggered by this preparation-only config.

## Output and return contract

Return exact implementation commit, pinned grammar/decoder and adversarial parse cases, mapping to canonical IDs/schema, prompt/request hashes, OpenAPI/SSE contract, semantic/unknown results, safe paired metrics and unresolved integration. Reject any apparent latency win that introduces hidden-wire matches, early false progression or stale guidance. Keep screen-writing/v0.2 and render/evidence ownership unchanged.

Configuration is `docs/experiments/experiment.config.json`, descriptive only. It is not wired to the runtime. Actual Python hosting/edge SSE acceptance, live Simulink overlay and generic mixed-language quality are separate integration gates. Report any necessary validation tightening distinctly and apply the same evaluation gate to the baseline arm.
