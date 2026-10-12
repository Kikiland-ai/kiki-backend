# Button

A tactile pill key with a darker bottom edge that presses down 2px on tap; use one filled Button per screen for the main action.

**Consumer provides:** `children` (the label, a verb: "Start lesson", "Run simulation"), optional `variant` (`filled` default, `tonal`, `text`), optional `icon` (a Material Symbols Rounded name) and any native button props.

- Do: one `filled` key per screen; `tonal` for secondary actions; `text` for links like "Show me the whole map".
- Do: write the label as the action that happens.
- Don't: put two filled keys side by side, or use red or green fills (those colours are mastery dimensions).
