# Handover: Google AI Builder Cup project

Last updated: 11 October 2026, late (Day 3 of the 10-day build; submission on 18 October). Latest sessions: generalised the data model (v2), specified every screen in a new "Student journey" tab, and redrew Kiki as a Clicky-style companion-cursor guide.

Repository: https://github.com/Kikiland-ai/Design-Thinking (private). The project folder is the git working copy; `main` holds everything below. Start with `README.md` for the map of the repo.

To continue in a new Claude session, clone the repo (or open the project folder) and paste:

> Read HANDOVER.md in this folder, then the working doc (live link below, or its markdown copy in `docs/working-doc/`) and the design system it links to. We're continuing the AI Builder Cup project from where the last session stopped. Start with the "Next steps" section.

---

## 1. The product in one paragraph

A bilingual (Odia–English) adaptive learning app for first-year engineering students who studied in Odia medium up to Class 12 and now face English-medium engineering. It teaches each concept in a student-controlled mix of Odia and English, keeps English technical terms stable, and judges **concept understanding and English expression separately**, so a student learns their marks were lost to language, not intelligence. Built on Gemini and Google Cloud for the Google AI Builder Cup. The demo is one branch (Electronics) and one chapter ("Diodes and rectifiers").

## 2. Decisions locked (don't re-open without the user)

| Topic | Decision |
| --- | --- |
| Demo scope | Electronics only; chapter "Diodes and rectifiers"; lab = a browser-based half-wave rectifier simulator |
| Language | Odia first. A 5-notch language dial is **student-controlled**; Kiki only suggests, never moves it |
| Helper | **Kiki**. Two forms: the four Google-coloured dots (presence) and the **pointer**, a cursor with two eyes and the dots trailing. No mouth, limbs or full face. **The pointer is a companion cursor, like Clicky** (user feedback, 11 Oct): it flies to the target and shows the route: halo + filled number = step now, ghost numbers on a dashed path = next two steps, tick = done, dots = flight trail, eyes look at the next step, never covers the target, marks run beside lines |
| Product name | None yet |
| Visual direction | "Breadboard: colour is earned". Google's four colours = four mastery dimensions: Blue concept, Red words, Yellow English, Green lab. Red never means wrong, green never means correct |
| Playfulness | Playful, not kiddy (users are 17 to 19) |
| Source of truth | The student's own notes and syllabus come first; curated content fills the gaps. English is the content source; Odia is generated and reviewed |
| X factor | Written exam practice: the student writes on paper, snaps the pages, Gemini reads the handwriting and marks concept and English separately, and a **repair map** of weak spots follows |
| Generality | Every feature is a template for any course; the diode chapter is the worked example. Lab faults use general "fault cards" (7 fault types). **Data model v2 is subject-agnostic**: any subject (via a subject profile), three scopes (chapter, topic, one concept), and any input through one Kiki door (StudyRequest, matched before generating) |
| Lesson structure | MECE pyramid: lesson plan > 2 to 5 broad concepts > 2 to 5 concepts (topic scope: 1 broad concept; concept scope: 1 and 1). Each concept has an explanation (text + image, voice walkthrough, optional video), an example, a worked question and a check-question mix |

## 3. Where everything lives

All artifacts are **private** to the user. Share them from each page's Share menu before teammates (or Claude Design) can open them.

| What | Link | Local source |
| --- | --- | --- |
| Working doc (5 tabs) | https://claude.ai/code/artifact/8ce032fe-a480-4582-85ab-0068f0f57a80 | none (lives in Claude Docs) |
| Breadboard design system | https://claude.ai/artifact/2xtRepczwUyXaNVKP17cuc | `design-system/project/` |
| Clickable mobile demo (21 screens) | https://claude.ai/artifact/Xc4Xwxj943pPqT3DiAbziJ | `prototype/` |
| Claude Design prompt | none | `prototype/claude-design-prompt.md` |
| Data model v2: types, subject profiles, 3 ledgers, validator | none | `data-model/` (v1 kept in `data-model/archive-v1/`) |
| Working doc, markdown copy (5 tabs, exported 11 Oct) | none | `docs/working-doc/01` to `05`, with diagrams in `docs/diagrams/`. The live doc is the source of truth; re-export after edits |
| Original inputs | none | `AI_Builder_Cup_Product_Vision.docx`, `AI_Builder_Cup_Technical_Architecture.docx`, `Audio Transcript.txt` (repo root) |
| Early working-doc snapshot | none | `docs/archive/` (superseded) |

### The working doc's tabs

1. **UX Working Doc** (main): decisions table, core UX concepts, onboarding end to end (with a journey diagram), day-to-day use (with a learning-loop diagram), open-question recommendations (all agreed), measuring impact, a pointer section "Student journey and data model", and UI sections 1 to 7.
2. **Student journey** (new): every screen, module by module (15 modules), for any subject. Each screen lists what it shows top to bottom, every button and what it does, its states and the data it reads. Includes an app map diagram, wireframes of the first page, Today and the Explain beat, and a table of 11 decisions with Status dropdowns (all Proposed).
3. **Feature journeys**: 31 features in 14 groups, 17 demo-critical. Feature 31 "Ask Kiki or add anything" (the universal intake) is new. Each has Goal / Outcome / Starts from / Steps table / Edge cases / Done when, plus a priority dropdown. Also "Everything beyond onboarding, by type" (8 content types).
4. **Build plan**: roadmap with 4 gates, a 49-task checklist plus 9 added tasks (50 to 58) with status dropdowns, workstreams and scope rules, the timed demo script, and risks.
5. **Data model** (renamed from "Lesson data model"): scopes, the whole-model diagram (content, intake, learner), what changed from the diode-only version, the three worked ledgers, the intake pipeline, concept contents, the validator rules, then the diode chapter as the worked example.

IDs for the Claude Docs tools: project `8ce032fe-a480-4582-85ab-0068f0f57a80`.

| Tab | File id | Body node id |
| --- | --- | --- |
| Main | `3777bf38-9262` | `04d4ec2e-cb59` |
| Feature journeys | `f2a0ae01-4831` | `d2e4bcad-89c3` |
| Build plan | `e17c0802-8384` | `909f1751-14fe` |
| Data model | `02b68f87-17e1` | `b60d259d-c70f` |
| Student journey | `71cbb065-0af9` | `0f38ada5-d393` |

Dropdown enums: Priority `2cb86d94-135c` (P0 / P1 / P2), Build status `01701335-a991`, Status `4f95c1f4-6a3a` (Proposed / Agreed / Changed). Always read a tab with `sinceRev` before editing, because the user may have changed it.

### The design system

- Namespace `window.Breadboard`, React 18, a hand-written classic script: `design-system/project/components/bundle.js` and `bundle.css`. Types are in `components/index.d.ts`.
- **25 components:** Button, Kiki, MasteryRing, LanguageDial, TermChip, MorphText, WordSticker, LessonProgress, DiodeExplorable, DiagnosisCard, VoiceScope, ReceiptCompare, MapNode (including the `repair` state), Snackbar, SourceTag, PredictionCanvas, LabStepper, Spotlight, FaultCard, AnswerOverlay, ClassPulseBar, KikiPointer, KikiWalkthrough, LabGuide, PracticeReport.
- Each component has `preview.html` and `README.md`. There is also a cover and the brand book in `project/README.md`.
- **Kiki assets (redrawn 11 Oct, design system version 5):** 13 guide moves on one series-or-parallel circuit (`kiki-guide-look`, `-path-ahead`, `-trace`, `-connect`, `-your-turn`, `-redirect`, `-show-me`, `-ask`, `-done`, `-words`, `-thinking`, `-listening`, `-unsure`), plus `kiki-guide-storyboard.svg`, `kiki-pointer.svg`, `kiki-dots.svg` and `kiki-sheet.svg`. They are uploaded to the asset store and recorded in `project/design-system.json`. To regenerate them, run `node design-system/tools/build-kiki.js`. The old 11 pose SVGs are kept in `design-system/archive-kiki-v1/`. The live `KikiPointer` component still only does poses; the route marks (halo, step badges, path ahead) are not yet a component.
- **To publish changes:** follow the artifact type's SKILL.md. Publish with `root` = `design-system`, `file_path` = `project/design-system.json`, and `files` = only the changed `project/...` paths. Send `index.d.ts` with contentType `text/plain`. Re-read `project/design-system.json` right before sending it.
- The prototype uses a **copy** of the bundle. After changing the design system, copy `bundle.js` and `bundle.css` into `prototype/` and republish the demo.

### The demo flow

- **Arrive:** class link, Kiki hello, promise.
- **Onboarding questions:** which feels easy, about you, goal, mid-sem plan, the "before" question.
- **Mid-sem route.**
- **Lesson** (8 beats, including "Kiki explains").
- **Learning receipt.**
- **Revision:** map, 2-minute recharge.
- **Exam practice:** prompt, timed paper, snap pages, analysis 17/25, marked answer, repair map.
- **Your space:** stickers, me.

Voice, camera and sign-in are simulated. The full path was click-tested headlessly with no errors.

### The data model (v2)

- `types/content.ts`, `types/intake.ts`, `types/learner.ts`: content (course, subject profile, exam profile, past papers, pyramid, concept parts, practicals), intake (StudyRequest, SourceDoc, Resolution, OutlineProposal, GenerationJob, SmartLink) and learner data (state, attempts with diagnosis, practice, marking, repair, receipts, classes).
- `subject-profiles.json`: the only place subject rules live (Electronics, Electrical, Chemical, Mathematics, generic).
- `ledgers/`: `electronics/diodes-and-rectifiers.json` (chapter, 12 concepts, migrated from v1), `chemical/steady-state-material-balances.json` (topic from notes, past papers compute the exam signal), `mathematics/eigenvalues-from-a-question.json` (one typed question, no practical).
- `validate.js`: run `node data-model/validate.js data-model/ledgers`. All three are valid and type-check against `Ledger`. `node data-model/tools/test-validator.js` catches all 13 seeded errors.
- `tools/migrate-v1-to-v2.js` rebuilds the diode ledger from `archive-v1/`, including four content fixes the new validator found (term order for PIV and reverse saturation current, a missing term link, a missing rubric).

## 4. Conventions the user has approved

- Copy: short plain sentences, sentence case, no emoji, "not yet" instead of "wrong". Grammar that doesn't block meaning is never penalised.
- Every English technical term stays in English in a TermChip; Odia explains it.
- Kiki's word marks: sweep, marker, lens, connect, circle. Colour = skill (terms red, ideas blue, exam English yellow, lab green). Never enlarge text in place.
- Contrast-checked text shades: yellow-ink `#9A5500`, green-ink `#137333`, red-strong `#C5221F` for "owned" fills.
- **All Odia text is placeholder** and needs a native speaker's review. Past-paper weights in the ledger are sample values.

## 5. Next steps (suggested order)

0a. **Build a `KikiGuide` component** that draws the route marks (halo, step badges, dashed path ahead, rails beside lines) around `KikiPointer`, and use it in the prototype's lesson and lab screens.
0. **Confirm the 11 decisions** at the end of the Student journey tab (four tabs Today/Map/Practice/Me, one Kiki door, skippable onboarding, one Explain beat with three modes, and so on). Then update the clickable demo: its nav is still Map/Stickers/Me and its lesson still has separate "Kiki explains" and "Learn" beats.
1. **Share** the doc, design system and demo with the team, and have a native speaker review the Odia (glossary, demo screens, ledger glosses).
2. **Check the hackathon rules** (deadline, demo length, submission format). Checklist task 1 is still open, and the demo script assumes about 5 minutes, with cuts listed for 3.
3. **Test the Odia voice** (Cloud Text-to-Speech or Gemini speech), checklist task 5. If it's poor, record Kiki's lines.
4. **Start the app repo** (React, Vite, Tailwind) and move the Breadboard bundle and tokens into it (tasks 3 and 4).
5. **Load the v2 ledgers into Firestore** and wire the lesson player to them (beats are derived from what each concept contains). Then have Gemini generate the 5 dial levels per concept and the walkthrough scripts in the ledger's shape (task 51).
6. **Build the practice-set pipeline:** multi-page OCR, per-question rubric marking split into concept and English, then repair-map generation (tasks 54 and 57).
7. **Optional:** run the Claude Design prompt to explore the 4 A/B variants (setup dial, route layout, dial placement, receipt order).

## 6. Things to watch

- **Keeping the repo in step with the live doc:** the doc lives in Claude Docs. After editing it, re-export each tab to markdown into `docs/working-doc/` and commit. The export replaces diagrams with placeholders; the PNGs in `docs/diagrams/` are screenshots of those widgets.

- The type-based design system artifact rejects `.ts` files unless sent as `text/plain`, and may show a "newer version" notice when its page saves generated files; read the files, then publish on top.
- Doc widget code must not use the identifiers `top`, `parent`, `self` or `window` (rename them, for example to `y0`).
- Python in this environment is `C:\Users\Arpan Vihan\AppData\Local\Python\pythoncore-3.14-64\python.exe`; the bare `python` alias may fail in some folders. Node 24 is available and is what the scripts use.
