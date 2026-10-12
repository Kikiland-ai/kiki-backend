# LabGuide

Kiki inside a lab tool: it demonstrates the step once with a ghost drag, waits at the control for the student's turn, reacts to wrong moves, spotlights the next button and then asks "why" about the output.

The sequence for every lab step:

1. **Show me.** The pointer flies to the part (pointing), carries a ghost copy to its place (dragging), then celebrates.
2. **Your turn.** The pointer waits on the part with a turning ring. Tap the part, then the slot (drag also works in the real tool).
3. **Wrong move.** The pointer tilts over the wrong slot (unsure) and the callout says why in one sentence. Nothing is undone for the student.
4. **Next control.** Everything else dims and Kiki taps the Run button (tapping).
5. **Why.** Kiki moves to the scope and asks a question (asking), which leads into the English explanation step.

**Consumer provides:** nothing for the demo version. In the app the same pattern is driven by the lab's known screen states and the fault cards. The callout is always attached to the pointer, one sentence, and the step name shows in the tool's title bar.

- Do: let the app's own state decide where the pointer goes; Gemini's screenshot reading only narrates.
- Don't: drag for the student after the demonstration. The second time, the student does it.
