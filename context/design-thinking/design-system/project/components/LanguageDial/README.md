# LanguageDial

The five-notch Odia-to-English slider that the student controls; Kiki can only suggest a notch.

**Consumer provides:** `value` (1 to 5) with `onChange`, or `defaultValue`; optional `suggested` (a notch: shown as a dashed ghost knob plus a "Try one notch more English?" chip) and `onAcceptSuggestion`.

Notches: 1 Odia with English terms, 2 mostly Odia, 3 half and half, 4 mostly English, 5 English with Odia on tap. Each notch change vibrates 10 ms on Android. Arrow keys, Home and End work on the knob.

- Do: keep the dial in the lesson header at all times.
- Don't: move the dial without the student. Never penalise a move toward Odia.
