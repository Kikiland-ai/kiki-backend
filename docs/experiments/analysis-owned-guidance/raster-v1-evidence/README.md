# Matched-raster freshness evidence

This bundle contains numeric diagnostics, projected packets and sanitized receipts, not learner images. Original PNGs and painted user-image screenshots remain in ignored local work.

- `hosted-receipts.json`: latest inspected receiver revision has five geometry rejections, six ordered cancellations and no paint. All five geometry rejections have `late_context:false`.
- `supplied-image-pixels.json`: both original PNGs falsely reject under the old mixed-raster comparison and pass under matched dimensions, with the unchanged threshold.
- `raster-regression.json`: six browser pixel cases; injected genuine changes on both supplied images still reject.
- `high-resolution-before.json` / `high-resolution-after.json`: actual native capture/reader/Worker/consumer/compositor replay changes from false rejection to verified paint on the static 1848×1014 controlled source. Model localization and Chrome dispatch are fixtures here.
- `matlab-open-first-placement.json`: actual model paint but failed 0.497 IoU placement gate; no switch test before the failure.
- `matlab-open-report.json`, `matlab-open-packet.json`, `matlab-open-timing.json`: second actual model replay paints box/text, stores a signed receipt and clears old ink on view switch. **Overall status remains FAIL_LOCALIZATION** because IoU 0.464 is below 0.5. Do not cite this as a placement acceptance pass.
- `matlab-closed-result.json`: actual model safely publishes no cue. The freshness comparison passes. The expectation of text-only painted guidance was not met; no canonical text paint is claimed.
- `model-mode-failures.json`: both failed model generations retained as structural diagnostics. Typed mode constraints prevent the reproduced single-target all-resolved/text-only combination; full final validation remains unchanged.
- `checks.json`: offline and browser counts and scope limits. Neither installed-extension nor real running-Simulink acceptance is established.

Free pixel regression from the backend root:

```sh
python prototypes/json_stream_site/scripts/check-writing-frame-raster.py \
  --image 'work/still-frame-diagnostic/user-images/Screenshot 2026-10-17 131012.png' \
  --image 'work/still-frame-diagnostic/user-images/Screenshot 2026-10-17 131115.png'
```

Without `--image`, it runs four synthetic raster sizes. It uses the available local Chromium/Playwright and makes no model or production request. Native replay commands use `check-guidance-pipeline.py --tls --high-resolution` and `--invalidate-before-paint`. The source-image flags run screenshot-backed native replay; they do not automate MATLAB. See the [handoff](../../../handoffs/screen-writing-raster-fix.md) for all failures, provider-call accounting, model-schema correction and uncompleted recognition acceptance.
