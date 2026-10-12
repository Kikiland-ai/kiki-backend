# MapNode

One concept on the breadboard map: a component with an LED, a small mastery ring and an optional past-paper heat badge.

**Consumer provides:** `label`, optional `odia`, `state` (`locked`, `available`, `progress`, `mastered`, `flicker`, or `repair`: a weak spot found by a practice set, drawn with a dashed body and an unlit LED), `values` for the ring, `heat` (such as "4/5" papers), `here` (shows Kiki as the you-are-here pin), `onClick`.

- Do: draw prerequisites as wires; animate current only out of mastered nodes.
- Don't: hide locked nodes: show them dashed so the path ahead is visible.
