# DiagnosisCard

The result after an English answer, judging Concept and English separately so a language gap never hides real understanding.

**Consumer provides:** `variant` (`solid`, `language`, `concept`), optional `title`, `message`, `actionLabel`, `onAction`.

- `language`: "You understand this. You just need the English words." Action: practise the words.
- `concept`: reroute to a prerequisite. Action label "Rerouting…".
- Do: show "not yet" as a dashed pencil outline. Don't use red or a cross: red means Words.
