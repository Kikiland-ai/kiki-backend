# Continuous screen sessions and provider quota recovery

Date: 14 October 2026. User instruction: no prototype read cap or forced session end; handle actual API limits and optionally use multiple API keys.

The former 30 analyses, 30-minute capture, 1,000 hosted frames, 500 lab mutations, 100 response records and historical run creation caps are removed. Limits on individual images (1 MB, longest dimension 1,600), input size, admitted-frame freshness, sampling cadence and concurrent work remain. These protect accuracy and resources without imposing a session duration. The actual hosted prototype is still the Sites Worker; equivalent Python/FastAPI logic is prepared locally and requires the separate Python host before the edge proxy is enabled.

Capture normally samples at 0.5 Hz, one upload in flight. Analysis starts no faster than once per ten seconds (twelve-second browser spacing), skips unchanged views unless supporting evidence needs another reading, and always selects the newest admitted frame. No pending-frame archive or replay backlog is created. Latest checked image only is retained. A provider cooldown is an observation gap: older results expire, no checkpoint completes from unavailable/newer unseen evidence, no rendering completes a checkpoint, and conceptual understanding remains unassessed.

## Provider coordination

`GEMINI_API_KEY` remains supported. Optional server-only secret `GEMINI_API_KEYS` is a JSON array of objects with `key` and `quota_pool`. The array replaces the single-key configuration. `quota_pool` must identify the actual independently provisioned Google project/model quota pool. Example shape uses dummy placeholders only:

```json
[{"key":"SERVER_SECRET_FOR_PROJECT_A","quota_pool":"project-a"},
 {"key":"SERVER_SECRET_FOR_PROJECT_B","quota_pool":"project-b"}]
```

Do not paste actual keys in chat, commit them or return them to clients. Google project quotas generally apply across keys in the same project. Only the first credential in a pool is selected; a 429 never causes attempts with another key in that same pool. The labels are administrator declarations, not verified Google project identities. If all pools share a higher organization/billing limit, rotation will not help. Raising quota/paid capacity and adaptive cadence address sustained demand; rotation is not a guarantee of unlimited quota.

A frame request can attempt at most two distinct available pools under a single twenty-second deadline. On 429, 5xx or network failure, persist a pool cooldown and use another independent available pool when possible. Honor Retry-After seconds or HTTP dates. Without provider guidance, 429 starts at sixty seconds and network/5xx at ten seconds, with exponentially increasing waits up to five minutes. Longer provider Retry-After is honored. Authentication/configuration failures use fifteen-minute administrative recovery spacing, without trying unrelated keys to bypass a permission failure. Successful requests clear that pool's cooldown. D1/SQLite retain cooldowns across isolate/process restarts; only hashed pool/model identifiers, timestamps and failure counts are persisted.

The lab runtime and generic analysis expose `waiting_for_provider`, safe error category and server UTC `retry_at_ms`; no provider bodies/keys appear. A durable lab deadline prevents repeated paid starts while cooling down. Clients leave capture active and retry a newly captured, provenance-checked frame after the deadline. Transient hosted capture 429/5xx/timeouts also wait and retry a new frame rather than stopping the native share. Explicit pause/stop, browser permission ending or page closure still stop sharing; a login/access loss needs reauthentication. Python WebSocket transport currently requires reconnect after a transport disconnect; API analysis cooldowns never disconnect it.

## Journal and storage

Append-only events have no application count cap. Recent response projections keep the last 100 records (hosted: per kind) to bound prompt/state size; every newly recorded response, including its ID and text, remains in the durable event journal. Existing historical records are preserved. Journal GET is paginated with `after` sequence and `limit` 1–100; consumer must fetch subsequent pages until done. Hosted browser export collects pages; Python export streams pages through its selected revision. The list UI/MCP shows recent runs, not a cap on creating or continuing runs.

No system can promise infinite compute, disk, connection lifetime or third-party availability. This change removes arbitrary session-ending counters, makes API failures recoverable and keeps image memory bounded. Database capacity, journal retention/compaction, organization quotas, fair multi-user scheduling and Python transport reconnect remain operational follow-ups; no silent history deletion is introduced. Provider health updates are durable but not a distributed lease/rate token bucket, so already in-flight concurrent requests can still encounter 429 before a pool cooldown is recorded.

## Acceptance

Controlled tests cover reads beyond 30, capture beyond thirty minutes and 1,000 receipts, journal beyond 500 mutations/100 responses with full paginated records, 429 Retry-After, network/5xx recovery, independent-pool fallback, no same-pool cycling, cold-worker/Python adapter cooldown persistence and preservation of current checkpoint. Browser QA uses an explicitly mocked provider and native controlled tab capture; it does not establish actual Simulink recognition or actual Google quota exhaustion.


14 October follow-up: the user explicitly requested individual-key rotation and 503 failover. The new [rotation decision](key-rotation-and-model-comparison.md) supersedes the two-pool/5xx retry selection policy described above while retaining shared-project 429 cooldowns, continuous capture and retained history.
