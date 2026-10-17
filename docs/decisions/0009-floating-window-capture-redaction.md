# Keep Kiki's windows out of screen reads by redacting the copy

17 October 2026. Implementation decision for the first floating-window slice. It changes the handoff's recommended capture approach (§8: briefly hide the windows, sample, restore). It is a proposal the user can reverse.

## Decision

The windows stay visible in the shared tab at all times. Right after the reader copies a frame to its canvas, and before JPEG encoding, it paints neutral grey (`#7f7f7f`) over every Kiki window rectangle. It pads each rectangle by 16 CSS px and includes positions reported in the last 1.5 s. The uploaded frame and the model input are therefore the redacted copy.

Rectangles come from the content script in CSS pixels with the viewport size. The reader maps them by `frame size / viewport size`.

The reader masks only when it can prove the frame shows the bound tab: `displaySurface === 'browser'` and a capture handle matching the bound tab. Otherwise the whole frame is greyed and not analysed, and the windows say why. This happens when:

- a window, screen or other tab is shared instead of the bound MATLAB tab;
- the bound tab hasn't reported window positions yet;
- a Kiki window is being dragged;
- the frame and viewport aspect ratios differ by more than 4%.

## Why

- No flicker: the student never sees Kiki disappear during sampling.
- No timing dependence: a background tab's delayed frames cannot leak Kiki text, because the mask is applied to the pixels being encoded, not to the live page.
- The covered region is hidden from the student too, so the model loses nothing the student can see. The existing occlusion rule already makes covered connections "unknown".

## Evidence

The L2 local lab check (`prototypes/floating_guidance/tests/check-local-lab.py`) reads the JPEGs actually sent to the fixture model:

- With masking on, there are zero canary pixels and a grey mask over the window.
- With masking switched off as a control, the canary does appear.
- When masking is turned back on, it resumes.

The tab screenshot shows the canary to the learner as a positive control. These are controlled-page results; real MATLAB Online remains for L3a.

## Limits

Per-frame redaction trusts the reported rectangles, so a stale report could leave a gap during a fast resize. The 1.5 s union, the padding and the drag block reduce this. Capture of a whole screen or window is blocked rather than masked. Browser element-capture APIs may later replace this. A native or desktop overlay would need its own approach.
