# Kiki

The helper character, drawn as four Google-coloured dots that rearrange to show what Kiki is doing.

**Consumer provides:** `state` (`idle`, `listening`, `thinking`, `speaking`, `pointing`, `asking`, `celebrating`, `unsure`, `examiner`), optional `size` (px, default 64), `lead` (`concept` | `words` | `english` | `lab`: that dimension's dot grows to show what is being practised), `direction` (degrees, for `pointing`), `label` (accessible name).

- Do: dock Kiki bottom-right on the phone; float it beside the target in the lab.
- Do: switch to `unsure` when screenshot reading is not confident, and offer the known-state picker.
- Don't: give Kiki a face, speech bubbles longer than two sentences, or any colours beyond the four dots.
