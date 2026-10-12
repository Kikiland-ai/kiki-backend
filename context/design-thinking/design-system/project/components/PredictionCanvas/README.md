# PredictionCanvas

A dark scope screen where the student sketches the output they expect before running the simulation; the real trace is then drawn over the sketch with a short verdict.

**Consumer provides:** `expected` (`halfwave`, `fullwave`, `sine`, or a function from 0..1 to -1..1), optional `onResult` (receives a 0 to 1 similarity score).

- Do: always show the input faintly so the student has a reference.
- Don't: reveal the real output before the student has drawn or chosen to skip.
