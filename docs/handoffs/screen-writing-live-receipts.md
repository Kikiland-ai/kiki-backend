# Live delivery follow-up — 17 October 2026

The user still cannot see shapes even when the browser reports `painted:2`. This follow-up uses BB8 engineering-debugging in reference mode and the Sites workflow. It does not declare the live experience accepted.

## Observed production behavior

Receiver v21, backend `c62edb33d49d0ea4c563acf0695639976a750398`. Sixteen non-cancellation delivery receipts from the current stream between 09:25:03 and 09:31:04 UTC: two signed `live_rendered` receipts, ten content-comparison rejections and four `Expired or foreign source admission.` rejections. Provider analysis and packet publication succeed for the inspected requests. These drawing failures are downstream of analysis, not evidence of HTTP 503.

The uploaded browser trace agrees with the 09:29:18 UTC paint: zero changed tiles out of 572, maximum delta 1.62, 35 ms presentation reservation before requesting paint, then a signed `live_rendered` receipt. The original frame was received at 09:29:06.278 UTC. Its immutable 20-second validity cap means this cue could not survive past 09:29:26.278 UTC; the additional eight-second-from-creation cap makes its maximum remaining life about six seconds. The next ordered cancellation at 09:30:18 is much later and does not explain immediate disappearance. The trace does not retain original mark coordinates, actual expiry/removal time or screenshot evidence after ACK. A cumulative count of two paints is not evidence that any guidance remains visible now, or that the original placement was correct.

The next two browser comparisons reject 1/572 tiles (max delta 3.104) and 33/572 tiles (max delta 13.437). Their exact changed locations were not recorded. Do not attribute these historical pixels to a cursor, compression, simulation status, probe or actual component movement without pixel/location evidence. The v21 raster correction remains valid in its controlled regression, but it has not solved reliable live delivery. Earlier broad wording that the freshness/delivery bug was fully corrected is superseded by this observed limitation.

## Verified controller lifecycle defect and bounded repair

The actual consumer invalidates by clearing all source tickets in the extension, but previously kept the corresponding signed proofs in its own retained map. It could send those proofs on later analysis requests. An admission already awaiting an extension response could also return after invalidation and restore an obsolete entry. Finally, a new capture could create a ticket while an older asynchronous `writer_clear` was pending, then lose that ticket when the clear completed. The uploaded trace includes fresh admission failures immediately after delivery rejection/clear, consistent with this mechanism. The old extension's combined rejection guard does not distinguish missing tickets, actual expiry and foreign connection, so this does not retrospectively assign every one of the four source-admission receipts to the same cause.

Three regression checks execute the actual consumer with explicit browser/extension boundaries. All three fail before the repair and pass afterward, exercising proof reuse, late admission and delayed clear followed by fresh-capture recovery. Source attachment generations now fence admissions, invalidation retires retained proofs, request headers require a current retained object, and captures/admissions wait for the outstanding clear. Cue sequencing still uses its separate epoch; routine producer cancellations do not invalidate otherwise current source tickets. Extension 0.4.0, producer contract and public writing schema remain unchanged. There is no extension reinstall for this repair.

## Visibility and freshness diagnostics

Browser diagnostics now label `painted` as cumulative and expose `current_cue` separately. Paint requests record primitive kinds, normalized coordinates, source-ticket/admission age and requested TTL. Successful receipts record operation count, immutable expiry and remaining validity. Extension expiry notifications clear the active cue/status and log `cue_expired`. These records describe lifecycle and placement requests; they do not prove human visibility or localization quality.

Content mismatches record at most twelve strongest changed grid regions with normalized rectangles and deltas. Marker exclusions and the strict greater-than-three per-tile threshold are unchanged. No image bytes or full fingerprints are logged. This supplies the missing evidence for evaluating small dynamic changes versus actual target movement, without weakening freshness or adding a second model request.

## Verification and continuation

144 Node checks pass, including the three before/after lifecycle regressions and changed-region coordinate/exclusion checks. Context, frozen-reader and BB8 checks pass. Native browser positive/negative results and deployment receipt are retained in `docs/experiments/analysis-owned-guidance/live-receipts-v1-evidence/`; all local fixture failures remain in ignored work. The first browser launch used a fixture server without its TLS flag and failed with connection refused before analysis; corrected fixture setup is recorded separately from application outcomes. No paid provider requests are needed for this deterministic repair.

Next: inspect fresh v22 client diagnostics for actual requested coordinates, expiry and changed-region positions, then reproduce the remaining pixel rejection against the actual live view. Do not declare the two historical paint receipts a successful user experience. Tight model localization and useful cue selection remain unaccepted, as recorded in the raster handoff. Rendering never completes a checkpoint. Preserve existing Sites, secrets, learner records, baseline/producer/latency references and independent renderer branch.

## Publication

Existing owner-private receiver version 22 succeeded at 15:12:21 Asia/Kolkata (09:42:21 UTC), backend `bda51adabbbcdb344d94755c3dbba4c94aa8800c`, Site source `fc6b5f4ae9531e78ff3d601777ae54a35bd8ab9e`, environment revision 13. All three existing secrets, audience and learner records remain preserved. Backend/source/dist Worker SHA256 matches. Both checkouts pass 144 Node checks. See [the receipt](../experiments/analysis-owned-guidance/live-receipts-v1-evidence/deployment.json).

Reload the reader and re-share the same connected MATLAB tab to load the new controller. Extension 0.4.0 remains compatible. Native publication is verified; optional hosted HTTP QA was not attempted under the existing proxy denial. No fresh installed-extension v22 receipt or user-visible acceptance is claimed at publication.
