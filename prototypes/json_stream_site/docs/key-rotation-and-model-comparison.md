# Key rotation and screen-model comparison

14 October 2026. User requests individual-key rotation on every outbound request, immediate next-key retry on 503, a one-minute wait after a failed full sweep, and a controlled comparison of other models. This supersedes the two-pool limit and 5xx exponential policy in continuous-screen-analysis.md. Browser Gemma remains a deferred, separate experiment.

## Behavior and compatibility

Python owns prototypes/lab_tracking/provider.py; the temporary hosted Worker mirrors it in worker/provider.js. Normal successful traffic rotates continuously, A → B → C → A. The one-minute cooldown applies when a cycle fails, rather than inserting waits into every healthy cycle. Within a failed cycle, each distinct credential is attempted at most once; 503, other 5xx and transport failure advance to the next eligible key immediately. Success clears the failed sweep. A fully failed/unavailable sweep waits at least 60 seconds before starting another cycle. Retry-After deadlines longer than that remain respected for the affected key/project. The next analysis uses fresh pixels and the ordinary context/provenance checks; no stale frame backlog is accumulated.

At least two distinct configured keys are required to prevent consecutive outbound attempts from using the same key. Duplicate keys are rejected. With two or more configured keys, if the last-used key is the only eligible credential, the router waits for an alternative instead of breaking this rule. A single existing GEMINI_API_KEY remains valid, but cannot provide alternating credentials. All model calls within one backend deployment share a cursor, including generic screen and lab analysis. This is not a cross-deployment cursor shared between the separate Python and Worker hosts.

D1/SQLite provider_rotation stores only credential hashes, last reservation, failed-key hashes, safe error category, retry deadline and a 30-second lease. Selection is reserved before sending; another Worker/process receives provider_rotation_busy and a short retry deadline while the lease is held. Cursor/failed cycle/cooldown survive a new instance. A crashed holder's lease expires and the next attempt advances from its reserved key. The additive hosted migration is drizzle/0002_provider_rotation.sql, appended to the migration journal without changing previous migrations or lab records. Python creates the corresponding prototype table on startup. This intentionally serializes model requests per configured key set; a fair multi-user scheduler and broader concurrency are later work.

Each frame's provider work has a twenty-second budget. With multiple keys, each attempt gets up to eight seconds within that budget; with one key, up to twenty seconds. Slow attempts can exhaust the frame budget before all keys are tried: the remaining sweep survives and continues on a later fresh frame. Expiry/provenance checks still apply after analysis. A provider call failure never ends capture or deletes progress. Pause, native sharing end and actual transport disconnect are separate states.

429 applies to the project/model quota pool; sibling keys are skipped until that pool's deadline (at least 60 seconds, or longer Retry-After). Auth 401/403 quarantines that credential for fifteen minutes and may use another; invalid request/model 4xx does not retry identical payload across every key. No provider bodies, raw credential values or pixels are logged. Worker attempt-failure logs carry model, short hashed key label, safe category and elapsed time. Lab events record the final failure separately. Existing continuous-history and frame retention rules remain intact. Screen-writing/v0.2, checkpoint ownership, journal/evidence and rendering responsibilities are unchanged.

## Site configuration

In the existing private Site's **runtime environment variables**, create secret GEMINI_API_KEYS, for example:

```json
["REPLACE_WITH_KEY_1", "REPLACE_WITH_KEY_2", "REPLACE_WITH_KEY_3"]
```

These are placeholder values, not working keys. The JSON list takes precedence over GEMINI_API_KEY, which remains the single-key fallback when the list is absent. Empty/malformed lists and duplicates fail closed. Up to sixteen distinct credentials are supported. String lists conservatively share one quota pool. For legitimately independent Google projects use actual project identities:

```json
[
  {"key":"REPLACE_WITH_KEY_1","quota_pool":"actual-google-project-a"},
  {"key":"REPLACE_WITH_KEY_2","quota_pool":"actual-google-project-a"},
  {"key":"REPLACE_WITH_KEY_3","quota_pool":"actual-google-project-b"}
]
```

Quota labels are administrator declarations, not identities verified by Google. Multiple keys in one project do not increase RPM/TPM capacity. Save the secret and redeploy the current saved Site version to apply the new environment revision. Editing this coding environment's variables does not update Site production secrets. No additional user keys have been supplied, generated or installed by this change.

The default model is now gemini-3.5-flash-lite. Optional GEMINI_SCREEN_MODEL selects generic observation; GEMINI_LAB_MODEL overrides lab analysis and otherwise inherits GEMINI_SCREEN_MODEL/the default. Both Python and Worker honor lab model choice and record the actual selected model as provenance. The request omits custom temperature and uses minimal thinking for Flash-Lite and low for the tested stronger Flash profile (3.8 rejects minimal). We have not established support for arbitrary model profiles. GET /health exposes configuration validity, key count, rotation enabled and model names without returning credentials. Changing a model must retain output-schema/evidence validation; it never proves checkpoints by itself.

## Controlled live comparison

The same three JPEG fixtures, v3 observer prompt, checkpoint context and structured schema were sent interleaved to three models using the existing configured server credential, with no automatic retries. The fixtures are labelled synthetic UI, not a real Simulink session. They show correct Local carrier parameters, a wrong Local carrier phase, and Carrier parameters at the Local-carrier stage. The focused expected local-parameter findings are match, mismatch and unknown respectively. Root script: scripts/compare-screen-models.py. Raw safe outcomes: docs/evidence/2026-10-14-model-comparison.json in the Site source; local equivalent work/model-comparison/report.json.

| Model | HTTP/inference outcomes | Focused expected findings | Latency |
|---|---|---|---|
| gemini-3.1-flash-lite | Three HTTP 503s | No findings returned | 10.93 / 5.29 / 1.17 s |
| gemini-3.5-flash-lite | Three HTTP 200s, STOP, validated JSON | Three of three matched | 2.92 / 3.09 / 5.48 s |
| gemini-3.8-flash | One transport timeout and two HTTP 503s | No findings returned | 20.02 / 0.64 / 0.83 s |

Calls occurred 15:07:23–15:08:13 UTC, 14 October 2026, from the managed cloud runtime through its configured proxy; this is not a test of deployed Site egress or multiple real credentials. The timeout category does not identify which network/service component caused it. These results justify trying 3.5 Lite for this prototype, and show that 503s also occurred on a newer stronger model. They do not establish long-term uptime, prove retirement caused earlier errors, rule out model-specific capacity, or establish general screen comprehension. The active 3.1 stable endpoint differs from its already retired preview endpoint.

Official sources checked: [model catalog](https://ai.google.dev/gemini-api/docs/models), [deprecations](https://ai.google.dev/gemini-api/docs/deprecations), [project quotas](https://ai.google.dev/gemini-api/docs/rate-limits), [3.8 model configuration](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash), [retry recommendations](https://ai.google.dev/gemini-api/docs/troubleshooting).

## Verification and remaining acceptance

Controlled backend checks cover successful rotation, same-project 503 fallback, full failed-cycle wait, long shared-project 429 cooldown, restart persistence, concurrent reservations, crash lease recovery, partial sweep continuation, cancellation cleanup, malformed/duplicate keys, auth quarantine, unsupported payload rejection, compatible model overrides and actual model provenance. They use explicit fixture credentials/transports. Exact suite counts and publication commit are in active.md. Browser UI was not changed by this slice; no new browser QA was run. A real multi-key hosted run awaits the user's server secrets, and actual Simulink recognition remains an integration trial. The Site is still the Worker adapter; Python FastAPI HTTPS hosting is pending.
