# Drawing prompt semantics, version 2

17 October 2026. Integration branch `integration/analysis-owned-guidance`.
Uses BB8's [prompt-design-engineering skill](../../bb8/skills/prompt-design-engineering/SKILL.md) in reference mode, with engineering-debugging support. The user identified prompt engineering as the missing prevention layer for prose in `text_ref` and absent text anchors.

## Diagnosis and change

The original clause was “text uses an authored text_ref and target-relative anchor.” It never defined the key-versus-value distinction, the required `{target_id,u,v}` object, a concrete correct text mark, or the common incorrect output. These are structured-generation semantics and missing-field failures. Historical malformed outputs remain in the earlier generated-marks evidence; v19 already added generation-schema enforcement and accurate `invalid_output` classification. Those deterministic safeguards remain necessary.

The prompt experiment changes only one appended, versioned [writing field prompt](../../prototypes/json_stream_site/worker/guidance-prompt.js), `dsb-step-observer/v5-drawing2`. It describes observer/tracker ownership, image/data boundaries, exact kind-specific fields, action-local references, normalized frame versus target-relative coordinates, field-versus-block identity, abstention, a valid text mark, the invalid prose/missing-anchor case, and a hidden-target example. Its examples take actual offered target IDs and text keys from the trusted catalogue. They contain no example screen rectangles to copy.

The integration-owned prompt is added after the published producer builder. Producer branch and public contracts stay unchanged. Candidate records and timing records both identify drawing2. The control prompt, generation schema, model, sampling, output limit, timeouts, retries, source binding, tracker authority, cancellation, compositor and extension are unchanged. A later, separate rendering investigation corrects capture masking as described below; this was not part of the paired prompt comparison. Rollback is removal of this integration prompt suffix and its version assignment; schema enforcement from v19 should remain.

## Controlled evaluation

The [runner](../../prototypes/json_stream_site/scripts/evaluate-writing-prompt.mjs) captures a production Worker request through the offline setup, substitutes the declared controlled screenshot and makes exactly one live request per arm. It requires explicit `--live`; maximum six calls without retries, each bounded to the existing single-key 20-second limit. The baseline removes only the new suffix. Each pair asserts byte-equivalent schema and user-input hashes; case order alternates arms.

Predeclared rubric: full contract validation; correct current-action mode; visible target rectangle overlap of at least 0.5 IoU with independently specified control bounds; and a mismatch finding on the wrong-phase holdout. The hidden-control preference is text-only guidance. Omitting that candidate is permitted by the public contract and is not a schema failure.

| Controlled case | Previous prompt | New prompt |
|---|---|---|
| Visible Recovery Gain input | Valid box + text; IoU 0.964 | Valid box + text; IoU 0.972 |
| Gain input absent | Valid response, candidate omitted | Valid text-only candidate, no marks |
| Two Local carrier fields, wrong phase | Valid marks; both fields located; mismatch | Valid anchored text on both fields; mismatch |

All six responses are contract valid and HTTP 200. The candidate meets all three rubric expectations; baseline meets two, with the permitted omission above. No invalid-reference recurrence was seen in either arm under the v19 typed schema. This does not establish a reduced malformed-output rate. The two-field case was withheld from edits in this iteration, but it is an existing baseline fixture, not a new blinded dataset. No prompt tuning followed inspection of these outputs.

The suffix adds 802 input tokens on CP06 and 821 on CP05 in these samples. Timings and automatic cache hits are retained without claiming a speedup. Small sample size and controlled images limit conclusions. See [raw results and responses](../experiments/analysis-owned-guidance/writing-prompt-v2-evidence/README.md).

## Connected rendering and a separately discovered capture defect

A separate live-model browser run uses native shared-tab capture, the real Worker/consumer/extension compositor code, actual streamed JSON, independently checked pixels, 1.5-second readability and a persisted signed paint ACK. Chrome API dispatch remains an explicit fixture; no installed-extension or real Simulink acceptance is implied. A follow-up fixture-only correction keeps real-model delivery ACKs labelled `live_provider`; the unbound initial control analysis remains offline. The second run validates that corrected label but fails the screenshot assertion: periodic capture has hidden the ink during JPEG encoding despite an earlier signed paint ACK. That failed screenshot and console remain retained. The third connected run passes actual pixel, 1.5-second readability and signed live-provider paint checks after the masking correction below (3,629 ms analysis-to-tracker-commit; 122.5 ms consumer-receipt-to-paint). The stale-view native negative also passes: no paint and a persisted rejection receipt. All outcomes and budget-exhausted automatic follow-up attempts are retained; nine actual model requests total including the six paired evaluations. No extra localization model call was added to the application.

The second run exposed a separate deterministic reader issue: `capture.js` restored the layer only after asynchronous JPEG encoding. The test caught the layer hidden during that encoding interval after an actual paint. Capture now restores ink immediately after copying and fingerprinting the clean frame into its private canvas, before calling `toBlob`. JPEG pixels, cadence, source attestations and expiry checks are unchanged. A stalled-encoder regression executes the actual capture function and proves copying occurs while masked, release precedes encoding, and upload waits for the encoder. This corrects one avoidable source of invisible guidance; brief masking to capture clean pixels still exists.

The user's two actual MATLAB screenshots are visible in chat but were not supplied as readable files in the execution workspace. `/workspace/attachments` contains only the older pasted text. No recreated or synthetic image is being represented as those exact screenshots. The exact-pixel MATLAB replay and open-dialog-to-closed-dialog cancellation test remain blocked on attachment-file access. Preserve that distinction when reporting acceptance.

Next: load those two image files into a periodically captured source tab, run the unchanged reader/writer pipeline, correlate analysis/commit/paint times and test cancellation on the view switch. Actual installed-extension Simulink paint remains a separate live acceptance check.

## Deployment receipt

Existing private receiver version 20 published successfully at 13:30:37 Asia/Kolkata, 17 October 2026. [Site](https://kiki-screen-receiver.woodsycarp256.chatgpt.site), source `a24506ceadf05dcbba1da73ad9507b17fa1f0c74`, backend `b595babfaa6d5ad6531fa8f7c4d27d9904dfb3b5`, environment revision 11. Standalone source passes all 138 tests; generated Worker hashes match exactly. [Receipt](../experiments/analysis-owned-guidance/writing-prompt-v2-evidence/deployment.json). Existing owner-only audience and all three secrets are preserved. Baseline/producer/renderer branches and latency Site were not changed by this work.

Reload the reader page and re-share to load the capture client correction. No extension reinstall is needed. Native publication is verified; optional postdeploy HTTP asset QA remains unavailable under the existing managed proxy denial and was not retried. No actual MATLAB screenshot or installed-extension acceptance is claimed.

Follow-up: the supplied ZIP is now readable. Exact PNG testing and a confirmed false freshness rejection are covered in [the matched-raster handoff](screen-writing-raster-fix.md), which supersedes the attachment-access blocker and records remaining localization failures.
