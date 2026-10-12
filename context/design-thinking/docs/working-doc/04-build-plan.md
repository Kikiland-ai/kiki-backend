# Build plan

Oct 11, 2026 · @Arpan

We build one demo path end to end with cached content by Day 5, make the AI live by Day 6, freeze features on Day 8 and submit on Day 10, Oct 18, 2026. Day 1 is 9 October, following the architecture doc's 10-day plan.

Workstream A starts from the [Breadboard design system](https://claude.ai/artifact/2xtRepczwUyXaNVKP17cuc): 21 components already built as a React 18 bundle, with a local copy in `design-system/project/components/`. Task 4 becomes moving that bundle into the repo, not building the components from scratch.

## Roadmap

*Diagram: build roadmap · 6 phases, 4 gates, Day 3 to Day 10. Shown in the live working doc.*

Each gate is a whole-team checkpoint. If a gate slips, cut the P1 list before moving the next gate.

## Workstreams and scope rules

Four workstreams, each with one owner. With three people, everyone shares workstream D on Days 9 and 10.

| Workstream | Owns | Main features |
| --- | --- | --- |
| A. Frontend | Breadboard UI kit, every screen, motion and sound | 1, 2, 5, 8 to 14, 18, 21, 26 |
| B. AI and backend | Gemini pipelines, Learning Orchestrator, learner state in Firestore, hosting on Google Cloud | 11, 12, 13, 19, 21 |
| C. Content and lab | Concept graph, glossary and Odia review, diode lesson, browser lab simulator, fault cards, demo answers | 8 to 10, 13, 19, 21, 27 |
| D. Demo and pitch | Demo script, student test, impact measures, video, submission | 1, 26, the demo |

Five rules that keep 27 features possible in 8 days:

1. **One demo path, end to end, first.** A thin version of every demo screen exists by Gate 1 before any one screen is polished.
2. **Cache first, then make it live.** Every AI moment ships with cached output by Gate 1, goes live by Gate 2, and falls back to the cache after 4 s.
3. **Build only from the UI kit.** A new component is added to the kit before it appears on a screen.
4. **Feature freeze at Gate 3.** After Day 8, only fixes and polish.
5. **Test on a real mid-range Android phone every day,** on throttled 3G.

If there's time after Gate 3, P1 features are added in this order. Cut from the bottom:

1. Sign in with Google (4), which is cheap with Firebase Auth.
2. Mid-sem route (6).
3. Viva with Kiki (22).
4. Watch mode (23).
5. Software tour (24).
6. Experiment sheet upload (20).

The other features stay as specs in Feature journeys for the pitch's "what's next".

## Checklist

49 tasks across the eight remaining days, ordered by day. Gate rows are checkpoints for the whole team. Update the status as you go. The feature numbers point to the Feature journeys tab, whose "Done when" lines are the acceptance tests.

| # | Task | Feature | Workstream | Day | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Check hackathon rules: deadline, demo length, submission format | — | D | 3 · 11 Oct | Not started |
| 2 | Set up Google Cloud project, Gemini API access, Firestore and hosting | — | B | 3 · 11 Oct | Not started |
| 3 | Repo: React, Vite and Tailwind, tokens as CSS variables, fonts loaded | — | A | 3 · 11 Oct | Not started |
| 4 | Port the UI kit's Kiki, ring, dial, term chip and buttons into React | 9, 10 | A | 3 · 11 Oct | Not started |
| 5 | Test the Odia voice (Cloud Text-to-Speech or Gemini speech); otherwise record lines | 2, 8 | B | 3 · 11 Oct | Not started |
| 6 | Concept graph for the 10 nodes: terms, misconceptions, rubrics, lab links | 5, 8 | C | 3 · 11 Oct | Not started |
| 7 | Glossary: about 30 terms with Odia explanations, checked by a native speaker | 10, 27 | C | 3 · 11 Oct | Not started |
| 8 | Demo script v1, timed to the rules | — | D | 3 · 11 Oct | Not started |
| 9 | Lesson player shell with the eight card types | 8 | A | 4 · 12 Oct | Not started |
| 10 | Diode lesson at all 5 dial levels, generated with Gemini and reviewed | 8, 9 | C | 4 · 12 Oct | Not started |
| 11 | Morphing text, with term chips fixed in place | 9 | A | 4 · 12 Oct | Not started |
| 12 | Breadboard map: 10 nodes, five states, current flow | 5 | A | 4 · 12 Oct | Not started |
| 13 | Learner state and event log in Firestore | — | B | 4 · 12 Oct | Not started |
| 14 | Smart link parsing and the First open screens | 1, 2 | A | 4 · 12 Oct | Not started |
| 15 | Browser lab simulator: parts, wires, Run, scope | 13 | C | 4 · 12 Oct | Not started |
| 16 | Diode explorable: the V-I playground | 8 | A | 5 · 13 Oct | Not started |
| 17 | Term sheet, stickers, collect game and sticker tray | 10 | A | 5 · 13 Oct | Not started |
| 18 | Answer composer and the three diagnosis cards | 11 | A | 5 · 13 Oct | Not started |
| 19 | Gemini grading with separate concept and English scores, as structured JSON | 11 | B | 5 · 13 Oct | Not started |
| 20 | Learning Orchestrator v1: a small fixed set of actions, as JSON | 8 | B | 5 · 13 Oct | Not started |
| 21 | Learning receipt: before and after, ring, map zoom | 14 | A | 5 · 13 Oct | Not started |
| 22 | **Gate 1:** whole demo path clickable with cached content | — | All | 5 · 13 Oct | Not started |
| 23 | Voice scope: record, playback, transcript, one-fix feedback | 12 | A | 6 · 14 Oct | Not started |
| 24 | Notes upload pipeline: extraction, node matching, source tags | 19 | B | 6 · 14 Oct | Not started |
| 25 | Notes upload screens: picker, "What I found", source tag on cards | 19 | A | 6 · 14 Oct | Not started |
| 26 | Hint ladder with all four rungs on every check | 18 | B | 6 · 14 Oct | Not started |
| 27 | Live diagnosis: the Odia retry and rerouting | 11 | B | 6 · 14 Oct | Not started |
| 28 | Student test with 3 to 5 Odia-medium students, and the fix list | — | D | 6 · 14 Oct | Not started |
| 29 | **Gate 2:** AI live everywhere, with 4 s fallbacks | — | All | 6 · 14 Oct | Not started |
| 30 | Pairing QR code, laptop to phone | 13 | B | 7 · 15 Oct | Not started |
| 31 | Prediction canvas, with overlay and similarity message | 13 | A | 7 · 15 Oct | Not started |
| 32 | Copilot overlay: spotlight, stepper, known states, "I can't see" picker | 13 | A | 7 · 15 Oct | Not started |
| 33 | Screenshot reading with Gemini, using the app's own state as ground truth | 13 | B | 7 · 15 Oct | Not started |
| 34 | Fault cards: reversed diode and short stop time, with fixed-when checks | 13 | C | 7 · 15 Oct | Not started |
| 35 | Snap your answer pipeline: photo, Gemini handwriting reading, split marks as JSON | 21 | B | 8 · 16 Oct | Not started |
| 36 | Snap overlay: blue and yellow marks, Odia explanation, rewrite view | 21 | A | 8 · 16 Oct | Not started |
| 37 | Three handwritten demo answers on paper: strong, weak English, weak concept | 21 | C | 8 · 16 Oct | Not started |
| 38 | Phone ring turns green live when the lab finishes | 13 | B | 8 · 16 Oct | Not started |
| 39 | **Gate 3:** feature freeze, every P0 feature done | — | All | 8 · 16 Oct | Not started |
| 40 | Class pulse screen with 40 seeded students | 26 | A | 9 · 17 Oct | Not started |
| 41 | Share card and the opening WhatsApp mock | 1 | D | 9 · 17 Oct | Not started |
| 42 | System states: loading, offline, error, empty, slow AI | — | A | 9 · 17 Oct | Not started |
| 43 | Deploy to Google Cloud and test on a mid-range Android phone on 3G | — | B | 9 · 17 Oct | Not started |
| 44 | Before-and-after measures on test students, if possible | — | D | 9 · 17 Oct | Not started |
| 45 | **Gate 4:** three clean full demo runs (demo freeze) | — | All | 9 · 17 Oct | Not started |
| 46 | Motion and sound pass | — | A | 10 · 18 Oct | Not started |
| 47 | Record the demo video, plus a backup recording | — | D | 10 · 18 Oct | Not started |
| 48 | Submission write-up: problem, demo, Google stack, impact plan | — | D | 10 · 18 Oct | Not started |
| 49 | Submit, and check every requirement | — | D | 10 · 18 Oct | Not started |

Added on 11 October for Kiki's pointer and the exam practice loop (features 28 to 30). The components already exist in the design system, so most of this is wiring and Gemini pipelines.

| # | Task | Feature | Workstream | Day | Status |
| --- | --- | --- | --- | --- | --- |
| 50 | Move KikiPointer, KikiWalkthrough and the five word marks into the app | 28 | A | 5 · 13 Oct | Not started |
| 51 | Walkthrough scripts: Gemini writes each card's steps (target, mark, colour, Odia, English) as JSON | 28 | B | 6 · 14 Oct | Not started |
| 52 | LabGuide in the browser lab: show me, your turn, wrong-move reactions, spotlight | 13 | A | 7 · 15 Oct | Not started |
| 53 | Practice set builder: Kiki's mock from covered stops and past-paper weights | 29 | C | 7 · 15 Oct | Not started |
| 54 | Multi-page snap, Gemini handwriting reading, answers matched to question numbers | 29 | B | 8 · 16 Oct | Not started |
| 55 | Analysis screen (PracticeReport) and the marked answer view | 29 | A | 8 · 16 Oct | Not started |
| 56 | Three handwritten demo pages for the 5-question mock | 29 | C | 8 · 16 Oct | Not started |
| 57 | Repair map generation from the analysis, with prerequisite pull-in | 30 | B | 9 · 17 Oct | Not started |
| 58 | Repair map screen and the re-test | 30 | A | 9 · 17 Oct | Not started |

## The demo script

Everything above serves this one run, about 5 minutes long. If the rules allow only 3 minutes, cut beats 6 and 9 first. Times are cumulative.

1. **0:00 · WhatsApp class group.** The class rep's mid-sem link. Tap it (feature 1).
2. **0:15 · First open.** Kiki greets in Odia, "Which feels easy?", the "before" question (2).
3. **0:45 · Lesson.** Drag the dial and the paragraph morphs from Odia to English while the term chips stay put (Hero 1). Kiki's pointer explains the paragraph word by word, then the V-I explorable and three stickers (8, 9, 10, 28).
4. **1:45 · Try in English.** A language-gap answer: "You understand this. You just need the English words" (11).
5. **2:15 · Say it and the receipt.** Their own English sentence plays back, the ring fills, the map lights up (12, 14, Hero 2).
6. **2:45 · Make it yours.** Upload the professor's notes, and a lesson card shows "From your notes, page 7" (19).
7. **3:15 · Lab on the laptop.** Pair, draw the prediction, run, find the planted fault, and the phone ring turns green (13, Hero 3).
8. **4:15 · Exam practice.** Kiki asks "Practise for the mid-sem?". Three handwritten pages are snapped, the analysis shows 17/25 with 3 marks lost only to English, one answer opens marked blue and yellow, and "Make my repair map" builds the fixes (29, 21, 30: the X factor).
9. **4:45 · The teacher's view.** Class pulse: "62% language gap, 15% concept gap" (26). Close on the impact headline.

## Risks and fallbacks

| Risk | Fallback | Decide by |
| --- | --- | --- |
| Odia voice from text-to-speech sounds poor | A team member records the demo lines | Day 3 |
| Odia text in generated lessons has errors | Native-speaker review of the glossary and the diode lesson. Reports go into the glossary (27) | Day 5 |
| Gemini is slow on stage | Cached output after 4 s, plus a "demo mode" switch that serves everything from the cache | Day 6 |
| Handwriting reading is unreliable | Neatly written, pre-tested demo answers. Show a mark range when unsure | Day 8 |
| Screenshot reading points at the wrong control | The lab is our own browser app, so its state is known for certain. Gemini narrates, and the app's state decides. Known-state picker as backup | Day 7 |
| Too much for the team in 8 days | Cut P1 features in the listed order. Every P0 demo moment can run on cached content | Gate 3 |
| Venue Wi-Fi or a device fails | A backup recording of the full demo, and a local demo-mode build | Day 10 |
