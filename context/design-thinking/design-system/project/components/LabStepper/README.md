# LabStepper

The lab's Predict, Act, Observe, Explain, Debug stepper with Kiki's current instruction card.

**Consumer provides:** `current` (0 to 4), optional `steps`, `title`, `hint`, `kikiState`, `onNext`, `nextLabel`.

- Do: keep instructions to one action each.
- Don't: skip Predict or Explain in the flow: they produce the evidence.
