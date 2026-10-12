# AnswerOverlay

Snap your answer: the student's handwritten exam answer marked with green ticks for the concept criteria and yellow underlines where the English cost marks; tapping a mark shows the Odia explanation and exam-ready English.

**Consumer provides:** `data` (`{question, score: {concept, english}, lines: [{tick: {label, ok}, parts: [string | {issue, text}]}], issues: [{kind: "mark" | "tip", odia, fix, cost}]}`). In the app the photo is the background; this component draws a ruled-paper mock in the preview. The paper stays light in dark theme on purpose, like a real sheet.

- Do: separate marks lost to English (wavy yellow) from grammar tips that cost nothing (dotted).
- Don't: show false precision: use a mark range when Gemini is unsure.
