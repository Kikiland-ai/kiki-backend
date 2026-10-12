Design the mobile screens for a bilingual Odia–English learning app for first-year engineering students, using the attached Breadboard design system. Cover one complete flow: a student opens a class link, answers the onboarding questions, chooses to prepare for the mid-sem exam, learns one concept, and lands on the revision map. Then produce test variants of four key screens.

## Use the design system exactly

Design system: Breadboard — https://claude.ai/artifact/2xtRepczwUyXaNVKP17cuc
Working reference prototype (match its flow and content): https://claude.ai/artifact/Xc4Xwxj943pPqT3DiAbziJ

- Read the design system's README first and follow it. Use only its colour, type, spacing, radius and shadow tokens. Do not invent colours.
- Build every screen from its components: Button, Kiki, MasteryRing, LanguageDial, MorphText, TermChip, WordSticker, LessonProgress, DiodeExplorable, DiagnosisCard, VoiceScope, ReceiptCompare, MapNode, Snackbar, SourceTag, PredictionCanvas, LabStepper, Spotlight, FaultCard, AnswerOverlay, ClassPulseBar. If a screen needs something new, design it as a new component in the same style and list it at the end.
- Colour is earned: screens are ink on warm paper with a dotted 8px breadboard grid. Blue, red, yellow and green appear only for the four mastery dimensions (Concept, Words, English, Lab, always in that order) and for Kiki's four dots.
- Red never means wrong and green never means correct. A wrong answer is "not yet": a dashed grey outline with a small shake.
- Every English technical term is a TermChip and is never translated. Odia text is 2px larger with looser line height than English.
- Playful but not childish: the users are 17 to 19. Fun lives in motion, Kiki and stickers, not in cartoon illustration. No emoji.

## Frame and constraints

- 390 × 844 Android phone, light theme first, then the dark theme for the four variant screens.
- One main action per screen, a filled Button pinned at the bottom. Touch targets at least 48px.
- Content must work on slow 3G: no video, no photographs.
- Show Kiki docked at the top right or bottom right, never with a face or long speech bubbles (two sentences at most).
- Odia copy below is placeholder text; keep it exactly as written so a native speaker can review it in place.

## The student

Bikash, first semester Electronics, studied in Odia medium up to Class 12. Basic Electronics mid-sem is on Thu 23 Oct, 12 days away. A rectifier lab is next Tuesday. Uses a mid-range Android phone.

## Screens (name artboards exactly like this)

**Arrive**

1. **01 Class link.** A generic group chat (not any real messaging app's branding): "ECE 1st sem · Section A". The class rep Rohan posts a link card: Kiki's dots, "Basic Electronics · Mid-sem route", Odia subtitle "ମିଡ୍-ସେମ୍ ପାଇଁ ପ୍ରସ୍ତୁତି", "10 min · Odia + English · 9 stops".
2. **02 Kiki says hello.** Large Kiki (idle), a "Tap to hear Kiki" button and "Read instead". After the tap, show this second state: Kiki speaking, Odia line "ନମସ୍କାର! ମୁଁ କିକି। Rohan ତୁମ ପାଇଁ Basic Electronics mid-sem route ପଠାଇଛନ୍ତି।", English caption below, and the chip "Shared by Rohan · 38 classmates on this route".
3. **03 The promise.** A dark goal card: "12 days until your mid-sem · 9 stops · about 4 h 30 min". Stop 1 card: empty MasteryRing, "Diode: a one-way gate · 10 minutes". A can-do card: "In 10 minutes you'll be able to explain in English why a diode lets current flow only one way." Buttons: Start, and a text button "Show me the whole map".

**Onboarding questions** (a 5-segment progress bar at the top of each)

4. **04 Which feels easy?** Title plus Odia "କେଉଁଟି ସହଜ ଲାଗୁଛି?". The same Class 12 sentence (Ohm's law) as three choice cards: mostly Odia, half and half, mostly English. After a pick, a card shows the LanguageDial set to level 1, 3 or 5, with "You can change it in every lesson."
5. **05 About you.** A banner: "Filled in from Rohan's class link." College row with Change. Branch chips: Electronics selected; Electrical and Chemical disabled with "soon". Semester chips with Sem 1 selected. Button "Looks right".
6. **06 What do you need right now?** Four goal cards with icons: Mid-sem is coming (tagged "From your link", selected), Lab is confusing, I'm lost in class, Get interview-ready.
7. **07 Your mid-sem plan.** Exam date row "Thu, 23 Oct · in 12 days · from your class". Daily time chips 15, 30 or 60 min. At 30 min, a banner: "You'll finish by 20 Oct, with time left to revise". At 15 min, a yellow-tint banner: "This needs 18 days and you have 12. Kiki will mark 3 low-weight stops as optional." An optional card: "Snap past papers", with a reading state (Kiki thinking) and a done state.
8. **08 The before question.** Kiki asking: "What do you think right now? No marks." Question: "Why does a reverse-biased diode not conduct?" Four options, including "I don't know yet". Button "Build my route".

**Mid-sem route**

9. **09 Your route.** Dark goal card "9 stops · 4 h 30 min · 30 min a day". Kiki line: "Semiconductor basics you already know from Class 12, so we start at the diode." A vertical breadboard route: a blue route line through 10 node squares, each with an LED, an XS MasteryRing, name, "Stop n · minutes" and a past-paper heat badge ("4/5"). Kiki pin on stop 1. Bottom nav: Map, Stickers, Me.
10. **10 Lesson.** Seven beats, each its own artboard (10a to 10g). Top bar: close, LessonProgress, "n/7".
    - **10a Hook:** charger illustration (AC socket, ?, phone DC) and Kiki's Odia question.
    - **10b Learn:** LanguageDial with a ghost suggestion, MorphText at level 3, and a quick-check card.
    - **10c Explore:** DiodeExplorable plus a check: "Below about how many volts does almost no current flow?"
    - **10d Collect:** three WordStickers (forward bias, reverse bias, cut-in voltage), one flipped to its Odia side.
    - **10e Try in English:** the question with sticker chips, the student's answer in handwriting style, then a DiagnosisCard in the "language" state ("You understand this. You just need the English words.") with an "Exam-ready English" yellow-tint card.
    - **10f Say it:** VoiceScope in the feedback state.
    - **10g Lab tease:** a large MasteryRing with Lab locked: "Build a half-wave rectifier in Tuesday's lab to complete this ring."
11. **11 Learning receipt.** ReceiptCompare ("10 minutes ago: I don't know yet" / "Now: …, Correct, in English"). A "You said this, in English" playback row, a large MasteryRing, a dark route card with 9 struck through and "8 stops left", "3 new English words" chips, "Save with your Google account", the share card "I can explain diodes in English" with an Odia line, and the button "Back to my map".

**Revision**

12. **12 Map and revision (home).** Goal card "8 stops · 4 h 20 min left · on track", then "Continue with Kiki: V-I characteristic". A Revise section with four cards:
    - "Semiconductor basics is flickering": a flickering ring and "2-minute recharge".
    - "Practise a 5-mark answer": Snap your answer.
    - "Lab on Tuesday": a 5-minute warm-up.
    - A locked "Exam-day revision" card: opens 23 Oct.

    Then the route list with stop 1 lit and the pin on stop 2.
13. **13 Recharge.** Three quick questions (Words, Concept, English) with "less help this time". Kiki suggests one notch more English on the dial. End state: Kiki celebrating, "Recharged. Next flicker in 5 days, then 12, then 30."
14. **14 Sticker deck.** Filter chips (All, New, Collected, Owned) and a two-column WordSticker grid, plus "Practise 5".
15. **15 How far you've come.** Large chapter ring, four dimension bars with counts, an English card (dial level now and at the start, words owned), milestones (one locked: "First concept without Odia"), settings rows.

**Kiki's guidance** (use KikiPointer, KikiWalkthrough and LabGuide; static art is in the design system's Kiki asset group)

16. **10a+ Kiki explains.** A lesson card between Hook and Learn. A dark caption bar at the bottom shows one sentence (Odia, English under it) with previous, play and next. Kiki's pointer (a cursor with two eyes and four trailing dots) sits on the word the sentence is about. Make one artboard per mark:
    - Sweep: a red underline under "Diode".
    - Marker: a red highlighter behind "forward bias", with the rest of the paragraph dimmed to 40%.
    - Lens: a card under "cut-in voltage" with the word at 28px, its Odia meaning and Hear it.
    - Connect: a dashed blue line from "cut-in voltage" to the knee of the V-I curve, which pulses.
    - Circle: a yellow hand-drawn loop around "conducts".

    Never enlarge text in place.
17. **Lab guide (laptop, 1280 × 800).** The lab tool on scope glass, with Kiki's pointer in each phase:
    - Show me: a ghost drag of the diode from the parts panel to the empty slot.
    - Your turn: waiting, with a turning ring on the diode.
    - Wrong move: unsure, tilted over the resistor slot, with a one-sentence callout.
    - Run: everything dimmed except the Run button, which Kiki taps.
    - Ask: Kiki at the scope asking "Why is the bottom half flat?".

**Exam practice** (use PracticeReport, AnswerOverlay, and MapNode in the repair state)

18. **18 Practise for the mid-sem?** Kiki's prompt card on the home map, then a set picker: Kiki's mock (recommended, 5 questions, 25 marks, 25 min), a past paper from the class, or one 5-mark answer. Add a "How it works" card: write on paper, snap, concept and English marked separately, repair map.
19. **19 Write on paper.** An exam-style question paper with Q1 to Q5 and their marks, a running mm:ss timer in the top bar, and "I've finished writing".
20. **20 Snap your pages.** Three handwritten page thumbnails, an "Add page" tile, a privacy line, then a marking state: Kiki's pointer thinking, with four steps (reading handwriting, matching answers, marking concept, marking English).
21. **21 Your analysis.** PracticeReport: 17/25, a bar split into earned / lost to English / lost to concept, five question rows each with its own mini split, and "Fix these before the exam" with "Make my repair map".
22. **22 One answer, marked.** AnswerOverlay for Q1, plus an "Exam-ready rewrite" card.
23. **23 Repair map.** A dark card "4 fixes · about 38 min, then a re-test". Dashed repair nodes in order of marks lost (Filter capacitor: concept −3; Ripple factor: English −2; Zener diode: concept −2; Half-wave rectifier: English −1), each with its fix and minutes, then a dark re-test node.

## Prototype links

Connect the screens in order. The main button goes forward and back arrows go back. The bottom nav switches between screens 12, 14 and 15. On 10e, all three answers branch to their DiagnosisCard state:
- "solid": both pills yes.
- "language": concept yes, English not yet.
- "concept": both not yet, with a "Rerouting… +1 stop, 6 min" Snackbar.

## Version testing

After the baseline (V1, matching the reference prototype), make two variants (A and B) of each of these four screens. Keep every other element identical so only one thing changes per test. Label each artboard with the variant and a one-line hypothesis.

| Screen | Variant A | Variant B | What we learn |
| --- | --- | --- | --- |
| 04 Which feels easy? | Three sentence cards (baseline) | One sentence with the LanguageDial: the student drags until it feels easy | Which sets a more accurate starting dial, faster |
| 09 Your route | Vertical breadboard list (baseline) | A horizontal circuit-board map with wires and pan, the route drawn on it | Which makes "what's next" clearer within 5 seconds |
| 10b Learn | Dial in the lesson header (baseline) | Dial hidden behind a small "Odia ↔ English" chip that opens a bottom sheet | Whether students change the dial more when it's always visible |
| 11 Learning receipt | Before and after first (baseline) | MasteryRing and map reveal first, before and after below | Which order makes students say "I learned something" |

For each pair, add a small note card: the hypothesis, the task to give 3 to 5 Odia-medium students, and what success looks like (for example, "can say their next step within 5 seconds").

## Deliverables

- All artboards above in light theme, plus dark theme for screens 04, 09, 10b and 11.
- A components-used list per screen, by design system component name.
- A list of any new components you had to create, with states.
- Flag any copy that doesn't fit at 390px wide instead of shrinking it below the design system's type sizes.
