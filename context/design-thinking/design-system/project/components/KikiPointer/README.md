# KikiPointer

Kiki's guide form: a rounded cursor with two eyes and the four coloured dots trailing behind it, used wherever Kiki points at, demonstrates or watches something on screen.

**Consumer provides:** `state`, optional `size` (px; 40 to 48 on top of lesson content, 46 to 56 in the lab, 72+ for teaching moments), `lead` (`concept` | `words` | `english` | `lab`: that dot grows and colours the tap ripple and wait ring), `flip` (mirror to point left), `label`, `style`.

Place it so the cursor tip, at (12, 8) in the 80 × 80 viewBox, sits on the target. KikiWalkthrough and LabGuide do this for you.

| State | Use it when Kiki is… | What moves |
| --- | --- | --- |
| idle | present but not acting | bobs gently, blinks |
| pointing | showing where to look | nudges toward the tip, dots tucked in |
| tapping | asking the student to tap or click here | presses down; a ripple in the lead colour |
| dragging | demonstrating a drag | tilts and carries a ghost part |
| tracing | reading a word or line with the student | tilts and slides along the text |
| thinking | waiting for Gemini | dots orbit the cursor |
| asking | asking a "why" question | eyes look up, dots form a question mark |
| listening | recording the student's voice | dots become equaliser bars |
| celebrating | marking a success | hops, happy eyes, dots burst |
| unsure | not confident about the screen | tilts, eyes look around, dots drift. Always pair with the known-state picker |
| waiting | waiting for the student at the next control | still, with a turning dashed ring at the tip |

## Guiding like a companion cursor

Kiki behaves like a companion cursor: it lives beside the student's own cursor or finger, flies to the thing that matters, and shows the route instead of describing it. A state alone is a pose; guidance is a state plus these marks around it (see `assets/Kiki/` for every move drawn on the series-or-parallel example):

| Move | Pointer state | Marks around it |
| --- | --- | --- |
| Look here | pointing | Kiki flies in (dots trail its path); a halo and a filled step number land on the target |
| Path ahead | pointing, eyes on the next step | Steps still to come appear as ghost numbers on a dashed route that flows towards them |
| Trace | tracing | A rail beside the wire or text: solid behind Kiki, dashed ahead |
| Connect | pointing | Two targets haloed, joined by arrows, with what they share named |
| Your turn | waiting | A turning dashed ring on the target; Kiki parks beside it, never on it |
| Redirect | pointing | A curved arrow from the student's tap to the right target. Copy says "Look here instead", never "wrong" |
| Show me | dragging | The ghost part travels from the tray to the slot along the route |
| Done | celebrating | The whole route solid, every step ticked |

- Do: show at most three steps at once: the one now and the next two. Further steps appear as the student moves.
- Do: let the eyes lead. Kiki looks at the next step before it moves there.
- Do: run marks beside lines (a rail 8 px off), so the student's diagram stays readable under them.
- Don't: park the pointer on top of the thing the student must tap or read.

## Rules

- Do: keep the body dark with its white outline in both themes. It sits over screenshots, scopes and paper alike, like a system cursor.
- Do: keep the student's own cursor or finger separate. Kiki's pointer never replaces it.
- Don't: give Kiki a mouth, arms or other expressions beyond the two eyes. Personality comes from posture, motion and the dots.
- Don't: move the pointer while the student is dragging; wait, then react.
