Breadboard is the design system for a bilingual Odia–English learning app for first-year engineering students. The app looks like a friendly electronics breadboard on graph paper, and Google's four colours appear only when the student earns them. A new student sees ink on `paper` with one spot of colour, Kiki's four dots. A student near mid-sem sees a map lit up in green, red, yellow and blue.

## Content fundamentals

- Write short, plain sentences. Kiki speaks at most two sentences at a time.
- Address the student as "you". Kiki says "I". Use sentence case everywhere. No emoji, no exclamation marks except in a celebration ("Spot on!").
- Keep every English technical term in English, in a `TermChip`, at every dial level. Never translate the term itself; explain it in Odia in the term's sheet. Example: "`forward bias`ରେ, ପ୍ରାୟ 0.7 V ର `cut-in voltage` ପରେ ଏହା current ପ୍ରବାହିତ କରେ।"
- Name what went wrong as "not yet", never "wrong". A language gap gets this sentence: "You understand this. You just need the English words."
- Buttons state the action: "Start lesson", "Run simulation", "Practise the words".
- The Odia sample copy in these components is placeholder text. A native speaker must review it before the demo.

## Colour

Colour is earned. Brand colour marks mastery and Kiki; everything else is `ink`, `pencil` and `line` on `paper` and `paper-raised`.

| Dimension | Fill token | Text token | Means |
| --- | --- | --- | --- |
| Concept | `green` | `green-ink` | "I understand it" |
| Words | `red` | `red-ink` | "I know what it's called" |
| English | `yellow` | `yellow-ink` | "I can explain it in English" |
| Lab (practical) | `blue` | `blue-ink` | "I can make it work" |

- Always show the four dimensions in this order: concept, words, English, lab, which is green, red, yellow, blue (ring segments clockwise from the top, progress segments). Kiki's four dots keep Google's order (blue, red, yellow, green): they are Kiki's identity, not a progress readout. When Kiki leads with a dimension, the dot of that colour grows.
- Use the fill tokens for shapes only. For text and icons use the `-ink` tokens, which meet 4.5:1 on `paper` and `paper-raised` in both themes. Never set text in `yellow` on paper. Text on a `yellow` fill is `on-yellow`.
- `red` never means wrong; it means Words. `green` never means correct on its own; it means Concept. Correct answers always carry a tick and a word as well as colour. A wrong answer is a dashed `pencil` outline. A correct answer lights up in the colour of the dimension being practised.
- An owned term chip or sticker uses a `red-strong` fill with white text.
- The primary button fill is `blue-ink` with `on-blue-ink` text, because `blue` with white text is below 4.5:1.
- Lab mode is a scope: `scope-glass` background, `scope-grid` lines, `scope-trace` for output, `blue` for the student's prediction, `scope-text` for readouts.
- Use tints (`blue-tint`, `red-tint`, `yellow-tint`, `green-tint`) for quiet grounds behind notes, never as the only signal.

## Type

- Headings: `display-l` and `display-m` (Baloo 2). Odia headings: `odia-display-m` (Baloo Bhaina 2, the same family), set 2px larger with a looser line height.
- Running text: `body` (Noto Sans) for English and `body-odia` (Noto Sans Oriya) for Odia and mixed sentences. Odia glyphs read smaller and need room for vowel marks, so Odia runs are 12% larger with a 1.66 line height; `MorphText` does this automatically.
- English terms: `term`. Labels and pills: `label`. Values and units: `mono` (Roboto Mono) with tabular figures.
- `hand` (Kalam) appears only inside Snap your answer mock-ups.
- All fonts load from Google Fonts; `components/bundle.css` imports them.

## Space, shape and the breadboard

- Spacing steps: `space-1` to `space-8`. `space-2` (8px) is also the breadboard grid: the `.bb-grid-bg` class draws `grid-dot` dots every 8px behind pages.
- Corners: `radius-node` for map nodes, `radius-card` for cards and stickers, `radius-sheet` for bottom sheets, `radius-pill` for buttons, chips and the dial.
- Buttons and stickers sit on a key edge (`key-edge-blue`, `key-edge-neutral`) and press down 2px on tap. Use `lift` only for popovers and sheets.
- The metaphor carries the interface: concepts are components, prerequisites are wires, mastering a concept lights its LED and sends current down the wire, loading is a pulse of current, an error is a broken wire with Kiki's dots drifting apart.

## Motion, sound and haptics

- Tap feedback 120 ms, small changes 250 ms on a spring, screen changes 350 ms, celebrations at most 1.2 s. Current flow is a dashed line moving along a wire.
- With reduced motion on, every animation stops and changes are instant.
- Five sounds only: tap tick, sticker pop, a rising three-note chime, a power-on hum for a mastered concept, and Kiki's voice, which always waits for a tap.
- Android haptics: 10 ms per dial notch, 30 ms on a correct answer.

## Focus and accessibility

- Keyboard focus is a 2px solid `focus-ring` outline with a 2px offset on every interactive component.
- The dial is a slider (arrow keys, Home, End). Rings, scopes and charts carry text labels. Status colours always come with a word ("not yet", "language gap").
- The class pulse hides any concept with fewer than 10 students.

## Iconography

Use Material Symbols Rounded (loaded from Google Fonts in `bundle.css`). Outlined icons switch to filled when something is earned. No emoji, no other icon sets. Kiki is the only character. Kiki has two forms and no other features: the four dots (`Kiki`) and the pointer (`KikiPointer`), a cursor with two eyes. Never add a mouth, limbs or a full face. Static artwork for every pointer state is in the Kiki asset group.

## How Kiki guides

- Kiki uses two forms. The four dots are for presence: the avatar, the caption bar, loading. The pointer is for guidance: whenever Kiki points at, demonstrates or watches something on screen. The student's own cursor or finger is never replaced.
- In a lesson, Kiki explains through `KikiWalkthrough`: a dark caption bar plays one sentence at a time (Odia first, English under it) while the pointer moves to the word or diagram part that sentence is about.
- Kiki marks a word in one of five ways, always in the colour of the skill being taught: **sweep** (an underline draws under the word as it is said), **marker** (a highlighter stroke behind the word while the rest of the paragraph dims), **lens** (a card opens with the word at 28px, its Odia meaning and Hear it), **connect** (a dashed line from the word to the matching point on the diagram) and **circle** (a hand-drawn loop for exam vocabulary). Technical words are red, ideas green, exam English yellow, lab controls blue.
- Words are never enlarged in place, so text never reflows. Only the lens zooms.
- In the lab, Kiki follows `LabGuide`: show me once with a ghost drag, wait at the part for the student's turn, tilt and explain in one sentence after a wrong move, dim everything but the next control and tap it, then ask "why" at the output. The callout is always attached to the pointer.

## Components

Load React 18, then `components/bundle.css` and `components/bundle.js`; everything is on `window.Breadboard`. Build screens only from these components; add a component here before it appears on a screen.

- Actions: `Button`.
- Kiki: `Kiki` (nine states).
- Language: `LanguageDial`, `MorphText`, `TermChip`, `WordSticker`.
- Progress: `MasteryRing`, `LessonProgress`, `ReceiptCompare`, `MapNode`.
- Learning: `DiodeExplorable` (the template for every explorable), `DiagnosisCard`, `VoiceScope`.
- Lab: `PredictionCanvas`, `LabStepper`, `Spotlight`, `FaultCard`.
- Exam: `AnswerOverlay` (Snap your answer), `PracticeReport` (analysis of a written practice set), and `MapNode` in the `repair` state for the weak-spot repair map.
- Feedback: `Snackbar`, `SourceTag`.
- Teachers: `ClassPulseBar`.
- Guidance: `KikiPointer`, `KikiWalkthrough`, `LabGuide`.

`window.Breadboard.samples` holds the worked example used in the previews: the diode lesson at all five dial levels, its glossary and a marked Snap answer.
