# Spotlight

Dims a lab tool's interface except one target control, which gets a pulsing blue ring; used by Kiki's copilot and by the software tour.

**Consumer provides:** children laid out as the tool; wrap the target in `Spotlight.Target`. Optional `active` (false removes the dim) and `style`.

- Do: spotlight one control at a time.
- Don't: spotlight a control Kiki is not confident about: switch Kiki to `unsure` and offer the known-state picker instead.
