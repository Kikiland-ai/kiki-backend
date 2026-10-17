# False content-change rejections on unchanged screens

17 October 2026. Branch `integration/analysis-owned-guidance`. Uses BB8 engineering-debugging in reference mode and the existing Sites deployment workflow. This follows the user's request to inspect repeated geometry discards and test the supplied PNGs.

## Confirmed cause

The current receiver's stored receipts show five rejected drawing packets between 13:33:58 and 13:35:37 Asia/Kolkata, all with `Live content differs from the analysed frame; geometry discarded.`, zero paint receipts, and `late_context:false`. The packets reached publication; these were browser freshness rejections after valid analysis. The first inspected packet's encoded frame is 1600×819. Live logs do not retain the two compared fingerprints, so historical per-tile attribution is unavailable.

The consumer compared **JPEG-decoded encoded frame → 256×144 sampling grid** against **native-resolution fresh capture → 256×144 sampling grid**. Capture first resizes large inputs to at most 1600 pixels. Resampling fine text/edges twice gives different brightness averages from sampling the native source directly. The unchanged threshold rejects when any non-excluded tile differs by more than 3 levels.

Controlled native shared-tab reproduction fails at 1848×1014 on a completely static source. The earlier 1200×800 fixture did not exercise capture downscaling. The actual supplied screenshots independently reproduce the fault without modifying a pixel:

| Original image | Encoded dimensions | Old changed tiles / max delta | Matched raster changed tiles / max delta |
|---|---|---|---|
| `Screenshot 2026-10-17 131012.png` (1847×1020), Gain dialog | 1600×884 | 31 / 5.344 | 0 / 1.188 |
| `Screenshot 2026-10-17 131115.png` (1848×1013), diagram | 1600×877 | 16 / 5.844 | 0 / 1.245 |

The ZIP was downloaded by its supplied Sediment ID and its image members were size/path checked before extraction. Original images and rendered user-image screenshots stay in ignored `work/still-frame-diagnostic/`, not in the repository's evidence folder.

## Correction

`guidance-consumer.js` now draws the fresh native sample into the retained analysed frame's exact encoded width and height before fingerprinting. Both sides therefore follow the same raster path. Marker exclusions, per-tile threshold, source binding, view/context/sequence fences, expiry, 500 ms presentation reservation and final extension checks remain enforced.

`writing-protocol.js` exposes a numeric comparison summary. Browser diagnostics record source/comparison dimensions, comparable and changed tile counts, maximum delta and `encoded-frame-raster/v1`. Genuine mismatches include bounded numeric details in the existing rejection reason; server ACK logs can retain them without a wire-schema change. No images or complete fingerprints are logged.

## Additional model-output failure discovered during real PNG testing

Two real model requests generated an invalid optional successor candidate: `text_only` with a resolved `workspace.canvas` target and no unresolved target. The full validator correctly rejected the entire response with `schema_contains`. Adding an explicit prompt rule alone did not prevent recurrence. These are separate from the five hosted geometry rejections above.

The integration generation schema now expresses candidate modes as a compact `anyOf`: annotate requires resolved targets and marks; none has empty targets/marks; text-only has no marks and, when every offered action has one required target, requires unresolved/ambiguous targets with null regions. For multi-target cases, full final validation still enforces the at-least-one-unresolved rule; the provider schema does not replace that check. Long repeated target-ID enums remain absent to preserve the earlier provider-400 fix. Drawing prompt/version telemetry is `dsb-step-observer/v5-drawing3`. Public contracts and producer branch are unchanged.

## Verification and actual limits

140 Node tests pass, including all twelve checkpoint request constructions, mode constraints and unchanged full-validation rejection. Source/context, frozen baseline and BB8 gates pass. The six-source browser pixel regression covers 1200, 1848, 1920 and 2560-pixel controlled sources plus the two original PNGs. Both real PNGs also reject an injected actual pixel change with the same threshold.

The same native 1848×1014 controlled pipeline that rejected an unchanged view before the fix now paints independently checked pixels, persists a signed receipt, stays visible at 1.5 seconds and keeps the observation panel coherent during periodic captures. A high-resolution view mutation immediately before paint still rejects and persists a rejection receipt.

The screenshot-backed browser tests use actual model calls, native shared-tab capture, the real Worker, broker, consumer and extension compositor code. Chrome API dispatch is an explicit fixture; this is not a test of the user's installed extension or a running MATLAB session. To avoid a Chromium odd-raster marker failure in the replay harness, the original PNGs are shown at natural size with at most one white padding pixel in each dimension; the PNG itself is not rescaled. The original odd-raster attempt made zero model calls and is retained locally as a harness failure.

Five actual model requests were made in this follow-up, each limited to one dispatch per server instance, with no per-case key retries:

1. Open Gain screenshot, drawing2: invalid optional mode; no commit/paint.
2. Same screenshot, drawing3 prompt clarification alone: same invalid optional mode; no commit/paint.
3. Same screenshot, typed mode schema: valid analysis and actual box/text paint; independent target IoU **0.497**, below the predeclared 0.5 placement gate. Failed placement retained.
4. Repeated open screenshot to exercise the now-deferred switch checks: valid actual paint, zero changed tiles (max delta 0.896), signed receipt and verified removal of old ink on switching to the diagram screenshot. IoU **0.464**, still below 0.5. The placement test remains failed; its threshold was not relaxed.
5. Closed-dialog screenshot: valid analysis and zero changed tiles (max delta 0.937), but the model omits the current candidate. Published outcome `none`, reason `no_matching_candidate`. This is permitted by the public contract and creates no anchored marks. The stricter test expectation of a painted text-only panel failed; canonical text paint is not claimed.

Automatic follow-up analyses after each live fixture's single-call budget are stub failures, not extra Google requests or HTTP 503s. They are retained in local logs. No failed request or placement result is presented as passing recognition acceptance. Detailed numeric and projected-packet evidence: [raster-v1-evidence](../experiments/analysis-owned-guidance/raster-v1-evidence/README.md).

The freshness/delivery bug is corrected. **Tight target localization and guaranteed useful cue selection remain unaccepted.** They require further analysis-side improvement rather than weakening freshness or fabricating instructions in the extension. Rendering/acknowledging guidance never completes a checkpoint.

Next: publish the existing private receiver, then inspect ordinary updated-client delivery receipts. Reader refresh/re-share is needed; adapter 0.4.0 remains compatible. Do not request the PNGs again: they are now available through the ZIP and local ignored paths. Preserve baseline, producer, independent renderer and latency branches/Sites.
