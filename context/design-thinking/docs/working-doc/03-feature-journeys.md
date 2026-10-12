# Feature journeys

Oct 11, 2026 · @Arpan

## Feature map

The product has 31 features in fourteen groups, and 17 of them are needed for the demo. Feature 21, Snap your answer, is the X factor and closes the demo. Each feature below follows the same template, so it can be built screen by screen:

- **Goal:** what the student is trying to do, in their words.
- **Outcome:** what the student walks away with, and what the system records.
- **Starts from:** every entry point.
- **Steps:** what the student does and how the product responds, in order.
- **Edge cases:** what can go wrong and what happens then.
- **Done when:** the check that says the feature is built.

**Every spec is a template that works for any course and chapter.** The Electronics chapter "Diodes and rectifiers" is only the worked example used in the demo. Wherever a spec says diode, rectifier or V-I curve, read it as "the current concept, lab or graph".

| # | Feature | Student's goal | Colour it feeds | Priority |
| --- | --- | --- | --- | --- |
| 1 | Smart links and sharing | "Open what my friend sent me" | — | P0 demo-critical |
| 2 | First open | "Show me this is worth my time" | Sets the dial | P0 demo-critical |
| 3 | Setup without a link | "Make this about my course" | — | P1 demo nice-to-have |
| 4 | Sign in and saving | "Don't lose my progress" | — | P1 demo nice-to-have |
| 5 | Breadboard map | "Show me where I am" | Shows all four | P0 demo-critical |
| 6 | Mid-sem route | "Tell me what to study, in what order" | — | P1 demo nice-to-have |
| 7 | Syllabus and past-paper upload | "Use my actual syllabus" | — | P1 demo nice-to-have |
| 8 | Lesson player | "Help me understand this" | Blue | P0 demo-critical |
| 9 | Language dial | "Explain it in a way I can follow" | Records support level | P0 demo-critical |
| 10 | Term chips and word stickers | "What does this English word mean?" | Red | P0 demo-critical |
| 11 | Try in English and diagnosis | "Can I answer it like the exam asks?" | Blue, Yellow | P0 demo-critical |
| 12 | Say it and Teach Kiki | "Can I explain it out loud in English?" | Yellow | P0 demo-critical |
| 13 | Lab copilot, with the debug challenge | "Help me get this experiment working" | Green | P0 demo-critical |
| 14 | Learning receipt | "Did I actually learn something?" | Shows all four | P0 demo-critical |
| 15 | Revise | "Don't let me forget it" | All four | P2 after hackathon |
| 16 | Reminders and notifications | "Remind me at the right time" | — | P2 after hackathon |
| 17 | Mastery view | "How far have I come?" | Shows all four | P1 demo nice-to-have |
| 18 | Ask Kiki and the hint ladder | "I'm stuck, help me" | Records hints used | P0 demo-critical |
| 19 | Your notes become lessons | "Teach me from my professor's notes" | Blue | P0 demo-critical |
| 20 | Experiment sheet upload | "Help me with this exact experiment" | Green | P1 demo nice-to-have |
| 21 | Snap your answer (X factor) | "Will this answer get marks in the exam?" | Blue, Yellow | P0 demo-critical |
| 22 | Viva with Kiki | "Don't let me freeze in the viva" | Yellow, Green | P1 demo nice-to-have |
| 23 | Watch mode | "Just show me" | Blue | P1 demo nice-to-have |
| 24 | Software tour | "What is all this on the screen?" | Green | P1 demo nice-to-have |
| 25 | Offline packs | "Let me study without data" | — | P2 after hackathon |
| 26 | Class pulse for teachers | Teacher: "Where is my class stuck?" | All four, per class | P1 demo nice-to-have |
| 27 | Report a problem and the glossary | "This explanation is wrong" | — | P2 after hackathon |
| 28 | Kiki explains (walkthrough) | "Explain it to me like a teacher would" | Blue, Red | P0 demo-critical |
| 29 | Exam practice sets | "Practise the mid-sem the way it's written" | Blue, Yellow | P0 demo-critical |
| 30 | Repair map | "Tell me exactly what to fix" | All four | P0 demo-critical |
| 31 | Ask Kiki or add anything | "Here's my question, my notes, my syllabus" | All four | P0 demo-critical |

For the demo, Teach Kiki inside feature 12 is a nice-to-have. Say it is demo-critical.

## Everything beyond onboarding, by type

After onboarding, every screen a student sees is one of eight content types. Each is built from Breadboard components ([design system](https://claude.ai/artifact/2xtRepczwUyXaNVKP17cuc)) and specified in the features listed.

| Type | What the student gets | Formats | Built from | Features |
| --- | --- | --- | --- | --- |
| Lessons | One concept in about 10 minutes, as a stack of cards | Hook, Kiki explains, Learn, Explore, Quick check, Collect, Try in English, Say it, Lab tease | Lesson player, LessonProgress, MorphText, DiodeExplorable | 8, 9 |
| Explanations | A teacher-style walkthrough: one narrated sentence at a time, with Kiki's pointer marking the word or diagram part it is about | Walkthrough (default), text at the dial level, "Explain it more simply" (one notch toward Odia), source-tagged cards from the student's notes | KikiWalkthrough, KikiPointer, TermChip, SourceTag | 18, 19, 28 |
| Videos | Something to watch when reading is tiring | Narrated slides with Odia/English audio (default, about 1 MB); the walkthrough played as a video; a short generated motion clip (20 s or less, pre-generated) only where motion matters, such as current flow; software tour videos for lab tools | Watch player, KikiPointer | 23, 24, 25 |
| Practice | Questions in the exam's own format, marked for concept and English separately | Quick checks in lessons; short English answers; spoken answers; one 5-mark written answer; full written practice sets; a viva | DiagnosisCard, VoiceScope, AnswerOverlay, PracticeReport | 11, 12, 21, 22, 29 |
| Revision | The right thing to revisit, when it matters | 2-minute recharge for flickering nodes; the repair map from a practice set; exam-day revision; the mid-sem pack summaries | MapNode (flicker, repair), MasteryRing | 6, 15, 19, 30 |
| Lab | Hands-on help inside the simulation tool | Software tour; Kiki's lab guide (show me, your turn); draw your prediction; the debug challenge; experiment sheet upload | LabGuide, Spotlight, PredictionCanvas, FaultCard, LabStepper | 13, 20, 24 |
| Words | The technical vocabulary, owned | Term sheet and lens; sticker deck; Practise 5 | TermChip, WordSticker | 10 |
| Progress | Proof of learning and a reason to come back | Learning receipt, mastery view, share card, class pulse for teachers | ReceiptCompare, MasteryRing, ClassPulseBar | 14, 17, 26 |

## Getting in

### 1. Smart links and sharing

**Goal:** "Open what my friend sent me."

**Outcome:** The student lands on exactly what was shared, with their class already filled in and no sign-up. The system records the referrer, class code, channel and destination.

**Starts from:** a WhatsApp message, a class QR code, a lab QR code, or the Share button inside the product.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Taps Share on a concept, route, sticker or receipt | Builds the card image and a pre-written mixed Odia and English message, then opens the phone's share sheet with WhatsApp first |
| 2 | Edits the message if they like, picks a group, sends | WhatsApp shows the preview card: Kiki's dots, the title in English with an Odia subtitle, "10 min · Odia + English" |
| 3 | A classmate taps the link | The page opens in the browser at under 1 MB, and Kiki's dots appear |
| 4 | — | Reads the destination, class code and referrer. Pre-fills the class and shows "Shared by Rohan · 38 classmates on this route" |
| 5 | — | Continues into First open (feature 2) at that destination |
| 6 | Scans a QR code with the phone camera or Google Lens | Same as step 3. A lab QR code opened on a laptop goes to pairing (feature 13) |

**Edge cases:**

- **Unknown or expired class code:** they still land on the concept, and the branch is asked later (feature 3).
- **Link opened on a laptop outside a lab:** it works, and a small QR code offers "Continue on your phone".
- **Student already signed in:** skip First open and go straight to the destination with their progress.
- **Sharer's privacy:** show the first name only. Sharers can hide their name in Me.

**Done when:** a WhatsApp link opens the exact concept with the class pre-filled in under 3 s on throttled 3G, and WhatsApp shows the preview image and title.

### 2. First open

**Goal:** "Show me this is worth my time."

**Outcome:** The student has heard Kiki, knows what the next 10 minutes will give them, has a dial setting, and has answered the "before" question. The system records the starting dial level, the "before" answer and the time to start.

**Starts from:** any smart link, on a first visit.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Taps "Tap to hear Kiki" | Plays the Odia greeting with captions, naming the sharer |
| 2 | Reads the promise card | Shows the route preview and the can-do sentence. Offers Start, or "Show me the whole map" |
| 3 | Taps Start, then picks one of three versions in "Which feels easy?" | Sets the dial to level 1, 3 or 5 of 5. Kiki points at the dial: "You can change this any time" |
| 4 | Answers the "before" question, or taps "I don't know yet" | Saves the answer for the receipt. Kiki cheers either way |
| 5 | — | Opens the first lesson card (feature 8) |

**Edge cases:**

- **Sound off:** captions are always on, and the tap-to-hear step can be skipped.
- **"Show me the whole map":** opens the map (feature 5) with the first node glowing and Start still one tap away.
- **Tab closed midway:** the state is saved on the device, and returning resumes at the same step.
- **Picked "mostly English" but struggles:** Kiki suggests a notch toward Odia later. The dial never moves on its own.

**Done when:** a student goes from tapping the link to the first lesson card in under 60 s, without typing anything.

### 3. Setup without a link

**Goal:** "Make this about my course."

**Outcome:** The course is set and the first node chosen in a few taps. The system records college, branch, semester and goal.

**Starts from:** a direct visit, a search result, or a link with no class code.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Hears Kiki and picks in "Which feels easy?" | Same as feature 2, steps 1 and 3 |
| 2 | Picks college (search, with nearby colleges first), then branch and semester chips | Loads that course's syllabus. For the demo only Electronics is active, and other branches show "coming soon" |
| 3 | Picks a goal card: mid-sem, lab, lost in class, or interview | Chooses the first node using the rules in the main tab |
| 4 | Answers the "before" question | Opens the first lesson card |
| 5 | After the receipt, sees "Make your route exact" | Offers syllabus and past-paper upload (feature 7) |

**Edge cases:**

- **College not listed:** "Other", type the name, and use the standard syllabus for the branch.
- **Branch not active yet:** "Tell me when it's ready" saves their interest, and they can still try the Electronics demo concept.
- **Not sure of semester:** default to semester 1.

**Done when:** a student goes from the first screen to the first lesson card in under 90 s, typing in at most one field.

### 4. Sign in and saving

**Goal:** "Don't lose my progress."

**Outcome:** Progress is tied to a Google account and synced across phone and laptop. The system records the account and merges any progress saved on the device.

**Starts from:** the Save step of the learning receipt, the Me tab, or laptop pairing when not signed in.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Uses the product without signing in | Saves everything on the device automatically, with a small "Saved on this phone" note |
| 2 | Reaches the receipt's Save step | "Sign in with Google to keep your ring and route", then opens Google's one-tap sign-in |
| 3 | Picks an account | Merges the on-device progress into the account. The ring animates "Saved" |
| 4 | Comes back another day | Recognises them, skips First open and opens the map at their next stop |

**Edge cases:**

- **Declines:** progress stays on the device. Ask again only after the next completed concept, and at most twice.
- **Account already has progress:** merge, keeping the stronger evidence for each concept.
- **Shared family phone:** "Not you? Switch account" in Me.

**Done when:** a student who signs in at the receipt sees the same ring on the laptop after pairing.

## Finding the way

### 5. Breadboard map

**Goal:** "Show me where I am."

**Outcome:** The student sees every concept in the chapter: which are done, which is next, which are locked, and how they connect. They reach the next step in one tap. The system records which nodes they open.

**Starts from:** the Map tab (home), the zoom-out at the end of the receipt, or "Show me the whole map".

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Opens the Map tab | Shows the board of 10 "Diodes and rectifiers" nodes, with Kiki as the pin on the current node, the goal card on top and a big "Continue with Kiki" button |
| 2 | Taps "Continue with Kiki" | Opens the next step the Learning Orchestrator chose: a lesson, a revision or a lab |
| 3 | Or taps a node | Opens the node sheet: name in English and Odia, the XS ring with its four segments explained, prerequisites, past-paper weight ("asked in 4 of 5 papers"), linked lab, and Start or Revise |
| 4 | Taps a locked node | The sheet names the prerequisite to finish first, with "Take me there" and "Try anyway" |
| 5 | Pans and pinches | Moves around the board. Double-tap resets the view |

Node states:

- **Locked:** grey outline, unplugged.
- **Available:** outlined, LED off.
- **In progress:** a partly filled ring.
- **Mastered:** LED on, with current flowing out to the next nodes.
- **Flickering:** the LED dims, meaning it's time to revise.

**Edge cases:**

- **Small phone:** the board becomes a vertical scrolling layout, top to bottom, instead of wide.
- **"Try anyway" on a locked node:** allowed, because the choice is the student's. Kiki warns once, and the result counts as normal evidence.
- **More chapters later:** a chapter switcher at the top of the map.

**Done when:** in testing, students can say what their next step is within 5 s of opening the map, and reach any node in two taps.

### 6. Mid-sem route

**Goal:** "Tell me what to study, in what order."

**Outcome:** An ordered list of stops up to the exam date, with an ETA that updates as they learn. The system records the exam date, the route and every reroute.

**Starts from:** the "Mid-sem is coming" goal, a class route link with the exam date, or the route toggle on the map.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Picks the mid-sem goal, or arrives on a route link | Confirms the exam date (pre-filled by the class code) and asks for daily time: 15, 30 or 60 min |
| 2 | — | Orders the stops by prerequisites, past-paper weight and current mastery. Draws the blue line with pins and an ETA pill: "9 stops · 6 h 40 min · about 30 min a day" |
| 3 | Taps "Start route" or "Continue" | Opens the first stop's lesson |
| 4 | Finishes a stop | The pin becomes a lit node, the counter drops and the ETA updates |
| 5 | Answers in a way that shows a concept gap | Shows a "Rerouting…" toast and redraws the line through the prerequisite: "+1 stop, 6 min" |
| 6 | Opens the app on exam day | Switches to exam-day revision: five quick checks on the highest-weight nodes. After the exam: "How did it go?", then the route is archived |

**Edge cases:**

- **Not enough time for every stop:** Kiki says so honestly: "This route needs 9 hours and you have about 6. Here's the 6-hour version." The lowest-weight stops are marked optional.
- **Missed days:** the route is quietly re-planned, with no guilt message.
- **Skips a stop:** allowed. The stop stays on the route, marked "skipped".

**Done when:** the route shows the right order, and a deliberately wrong concept answer causes a visible reroute within 2 s.

### 7. Syllabus and past-paper upload

**Goal:** "Use my actual syllabus."

**Outcome:** The map and route reflect their own college's syllabus and past-paper weights. The system records which syllabus topics mapped to which nodes, and how often each node's topic appears in past papers.

**Starts from:** "Make your route exact" after the receipt, route settings, or setup.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Taps "Snap your syllabus or past papers" | Opens the camera or file picker. Photos or PDFs, several pages allowed |
| 2 | Takes the photos | Checks for blur on the phone and asks for a retake if a page is unreadable |
| 3 | Uploads | Kiki shows "Reading…" with progress while Gemini pulls out the topics and question topics |
| 4 | Reviews the result | "I found 8 topics. 7 match your map." Shown as a checklist they can untick. Unmatched topics are listed as "Not in this demo yet" |
| 5 | Confirms | Map nodes get heat badges ("in 4 of 5 papers") and the route reorders. Kiki: "Route updated. Rectifiers moved up." |

**Edge cases:**

- **Handwritten or poor photo:** ask for a retake, or offer "Use my branch's syllabus instead".
- **Reading fails or times out:** fall back silently to the curated map, with "I'll use the standard syllabus for now."
- **Wrong subject uploaded:** "This looks like Maths, not Basic Electronics."
- **Privacy:** images are deleted after reading, and the screen says so.

**Done when:** uploading the demo past paper changes at least one node's heat badge and the route order within 15 s.

## Learning a concept

### 8. Lesson player

**Goal:** "Help me understand this."

**Outcome:** The student understands one concept through about six short beats, and Blue fills from the checks inside the lesson. The system records each check answer, time per card, dial level per card, hints used and how they used the explorable.

**Starts from:** "Continue with Kiki", Start on a node sheet, a route stop, or the end of First open.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Opens a concept | Full-screen player: top bar with close, the dial and a four-colour progress bar. The first card states the can-do goal |
| 2 | Reads the Hook card and taps Next | A picture and Kiki's question in Odia, with audio |
| 3 | Reads an Explain card | At most 3 to 5 sentences at the dial level, with term chips and one illustration |
| 4 | Drags the slider on the explorable | Current dots move through the circuit and the V-I curve draws live. Kiki highlights the knee: "See? Almost nothing until about 0.7 V." |
| 5 | Answers a check (multiple choice, or tap on the graph) | Right: a chime and Blue grows. Not yet: a grey shake, and the hint ladder starts (feature 18) |
| 6 | Continues | The Learning Orchestrator picks the next card: another explanation, a simpler one, a visual, or more practice. Usually two or three explain-and-check rounds |
| 7 | — | Hands over to Collect (feature 10), Try in English (feature 11), Say it (feature 12) and the lab tease |

**Edge cases:**

- **Leaves mid-lesson:** resumes at the same card next time.
- **Swipes back:** the previous card is shown and earlier answers are kept.
- **Slow network:** the demo concept is fully cached. Elsewhere, skeleton cards show while content loads.
- **Repeated misses:** the Orchestrator switches approach (a visual instead of text) or reroutes to a prerequisite.

**Done when:** the diode lesson runs end to end in about 10 minutes, Blue matches the check results, and closing and reopening resumes at the same card.

### 9. Language dial

**Goal:** "Explain it in a way I can follow."

**Outcome:** The student controls the language mix at every moment and moves toward English by their own choice. The system records the dial level on every card, every change, and every suggestion accepted or declined.

The five notches. English technical terms stay in English at every level:

1. Odia sentences, with English terms as chips.
2. Mostly Odia, with short English phrases.
3. Half Odia, half English.
4. Mostly English, with Odia for the hardest sentences.
5. English, with Odia only when a sentence is tapped.

**Starts from:** "Which feels easy?" (the starting level), the lesson top bar (always visible), or Me (the default).

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Sees the dial in the lesson header | The knob sits on the current notch |
| 2 | Drags the knob | A haptic tick at each notch and a preview sentence while dragging. On release the paragraph morphs and the term chips stay where they are |
| 3 | Gets 3 right in a row | A ghost knob appears on the next notch: "Try one notch more English?" Yes moves it. "Not now" hides it for the rest of the lesson |
| 4 | Misses 2 in a row after moving up | Kiki offers one notch back: "Let's make this one easier." It never moves the dial itself |
| 5 | Finishes a lesson after changing the dial | "Keep this everywhere?" Yes updates the default |

One firm rule: questions in Try in English are always in English, whatever the dial says. Only the instructions around them follow the dial.

**Edge cases:**

- **A level that isn't generated yet:** show the nearest cached level with a light shimmer, then morph when ready.
- **A student who stays at level 1:** no penalty. Kiki suggests at most once per lesson.
- **Audio:** Kiki's narration follows the dial level too.

**Done when:** dragging the dial in the diode lesson re-renders the text within 300 ms from cache, with every term chip unchanged and in place.

### 10. Term chips and word stickers

**Goal:** "What does this English word mean?"

**Outcome:** The student knows the meaning, pronunciation and use of each key term, and builds a deck they reuse in English answers. The system records terms seen, tapped, collected and used correctly in English, which is the Red evidence.

**Starts from:** any term chip in a lesson or question, the Collect beat, or the Stickers tab.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Taps a term chip | A bottom sheet: the English term large, its Odia meaning, pronunciation at slow and normal speed, a mini diagram, an English example sentence with Odia below, and "Seen in: Diode lesson" |
| 2 | Reaches the Collect beat | Three new stickers fly in. Each one plays its pronunciation when tapped |
| 3 | Drags each term to its picture or meaning | Right: the sticker pops into the deck and Red grows. Not yet: it slides back, with a hint |
| 4 | Writes an answer in Try in English | The sticker tray sits under the answer field. Tapping a sticker inserts the term |
| 5 | Opens the Stickers tab | A deck grid with New, Collected and Owned filters. Tap to flip, or "Practise 5" for a quick game |
| 6 | Uses a term correctly in English answers twice | The sticker turns solid: owned |

**Edge cases:**

- **No single Odia word exists:** the sheet says so and explains the meaning in an Odia phrase instead of a forced translation.
- **Same term, different meaning across subjects** (for example "gain"): the sticker shows the meaning for each subject.
- **Pronunciation:** not graded in the demo.

**Done when:** the three diode stickers can be collected, appear in the answer tray, and turn owned when used correctly.

## Proving it in English

### 11. Try in English and diagnosis

**Goal:** "Can I answer it the way the exam asks?"

**Outcome:** The student answers an exam-style English question and learns whether any gap is in the concept or in the English, then gets the right next step. The system records rubric results split into concept and English, which feed Blue and Yellow.

**Starts from:** the lesson after Collect, route practice in exam mode, or revision.

How diagnosis separates the two gaps: when an English answer is wrong, Kiki offers the same question in Odia. Right in Odia means a language gap. Wrong in Odia too means a concept gap.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Reads an exam-style English question | Instructions follow the dial. Any word can be tapped for a short Odia gloss, which is recorded as support |
| 2 | Writes an answer: types, taps stickers, or speaks | "Help me start" offers a sentence starter, also recorded as support |
| 3 | Submits | Kiki thinks for at most 4 s while Gemini grades against the rubric, scoring concept and English separately |
| 4a | — | **Both solid:** the diagnosis card shows "Concept: yes. English: yes." Blue and Yellow grow, and the lesson moves on |
| 4b | — | **Concept right, English weak:** "You understand this. You just need the English words." Shows a model answer with their own correct words highlighted, offers word practice, then an easier English version |
| 4c | — | **Wrong:** "Try it in Odia?" |
| 5 | Answers in Odia | Right: the language-gap path (4b). Wrong: a concept gap. "Rerouting…" to a prerequisite or a fresh explanation |
| 6 | Retries | Graded on the same rubric, then the matching result card |

One grading rule: grammar mistakes that don't block the meaning are never penalised. The rubric grades the idea and the correct technical terms. Grammar gets one gentle tip at most.

**Edge cases:**

- **Blank or "I don't know":** treated gently as a concept gap, and the hint ladder is offered.
- **Answer typed in Odia:** accepted as concept evidence, then "Now let's try it in English."
- **Very short answer:** Kiki asks "Can you say why?" once.
- **Gemini unsure how to grade:** Kiki says it isn't sure and asks a quick multiple-choice follow-up instead of guessing.

**Done when:** three prepared demo answers (both solid, language gap, concept gap) each produce the right diagnosis card and next step.

### 12. Say it and Teach Kiki

**Goal:** "Can I explain it out loud in English?"

**Outcome:** The student hears themselves explain a concept in English and gets one specific improvement. The system records the transcript and a rubric: key idea present, terms used, clarity. Both feed Yellow. The recording stays on the device unless they share it.

**Starts from:** the Say it beat in every lesson. Teach Kiki opens when a ring is three-quarters full, or from the interview goal.

**Say it:**

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Sees the prompt | A sentence starter ("A diode conducts when…") and the stickers to use |
| 2 | Holds the mic key, or taps to start and stop | The voice scope draws their voice live, for up to 30 s |
| 3 | Releases | Plays it back automatically and shows the transcript, with recognised terms as chips |
| 4 | Listens to Kiki | One praise and one fix: "You used forward bias correctly. Try 'conducts' instead of 'passes'." Then "Try again" or "Keep it" |
| 5 | Keeps it | The recording is saved for the learning receipt |

**Teach Kiki:**

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Opens Teach Kiki | Kiki plays a confused junior: "I don't get why the diode blocks current backwards. Can you explain?" |
| 2 | Explains by voice | Kiki asks one follow-up: "But what happens at 0.3 V?" |
| 3 | Answers | "Oh! I get it now." Then a feedback card: key ideas covered as a checklist, terms used, and one tip |

**Edge cases:**

- **Mic permission denied:** Kiki explains in Odia why it needs to listen, and offers typing instead.
- **Noisy hostel room:** if the transcript is unclear, "I couldn't hear that well. Try again, or type it."
- **Shy student:** "Skip for now" is always allowed. Yellow just doesn't grow from this beat.
- **Speaks in Odia:** accepted as concept evidence, with encouragement to try once in English.

**Done when:** recording, playback, transcript and the one-fix feedback all work in Chrome on a mid-range Android phone within 5 s of release.

## Doing it in the lab

### 13. Lab copilot

**Goal:** "Help me get this experiment working."

**Outcome:** The student builds and runs a half-wave rectifier in the browser lab, predicts the output, compares it with the real result, finds a planted fault and explains the result in English. Green fills. The system records how close the prediction was, which steps were done without help, hints used, time to debug, and the explanation rubric.

**Starts from:** the lab tease ("Open on laptop"), the lab QR code on the experiment sheet, the lab link on a node sheet, or a reminder before lab day.

The lab runs in eight phases: Pair, Brief, Predict, Build, Run, Explain, Debug, Done.

| Step | Phase | Student does | Product responds |
| --- | --- | --- | --- |
| 1 | Pair | Opens the short address on the lab laptop and scans its QR code with their signed-in phone | The laptop says "Hi Bikash". The phone shows "Lab connected" and stays as a companion screen |
| 2 | Brief | Reads and listens | Kiki explains the aim at the student's dial level, shows the circuit diagram, and lists the four parts needed |
| 3 | Predict | Draws the expected output over the input sine wave on the prediction canvas | Saves the sketch for comparison |
| 4 | Build | Drags parts from the palette and wires them | Kiki spotlights the next control ("Pick the diode from here"). On wrong wiring it asks a question instead of fixing it: "Where does current go after the diode?" |
| 5 | Run | Presses Run | The scope shows the output. Kiki overlays the sketch on it: "Close! You missed that the negative half is flat." |
| 6 | Explain | Answers in English, typed or spoken: "Why is the negative half missing?" | Graded like feature 11, feeding Yellow and Green |
| 7 | Debug | Hears "Your lab partner changed something. Find what's wrong." Kiki has planted the fault card that matches their weakest misconception (see Debug challenge below). Demo example: the diode is flipped, so only negative halves appear | Kiki asks "why" questions, and the hint ladder runs if they get stuck. They fix it and run again |
| 8 | Done | Watches | Green fills with the power-on animation. The phone ring turns green at the same moment. A short lab summary (prediction against result, time, hints) goes into the receipt |

**Edge cases:**

- **Kiki unsure of the screen:** "I can't see clearly. Which screen are you on?" with three thumbnails of known states.
- **Skips Predict:** allowed. Kiki says once, "Guessing first helps you learn."
- **Stuck in Build for more than 2 minutes:** Kiki offers a step-by-step mode.
- **Laptop closes or the network drops:** the state is saved and the lab resumes at the last phase.
- **No laptop:** a simplified phone version of the lab, after the hackathon.

**Done when:** the full lab, including either of the two demo faults, can be finished in about 8 minutes. Kiki spotlights the right control in each of the 5 to 10 known states, and the phone ring turns green within 2 s of finishing.

#### Debug challenge, for any course

The planted fault is never hard-coded. Every lab carries a few **fault cards**, and the Learning Orchestrator plants the one that matches the student's weakest misconception. The puzzle is aimed at that student's own gap. The debug screens are the same in every course: symptom, guess, test, fix, explain.

Seven fault types cover any lab, with examples per branch:

| Fault type | Electronics | Electrical | Chemical |
| --- | --- | --- | --- |
| Flipped: direction, sign or orientation | Diode reversed | Transformer polarity swapped | Flow direction reversed |
| Wrong value: size or unit | 100 Ω instead of 10 kΩ | Wrong turns ratio | Grams entered as kilograms in a mass balance |
| Missing piece | No load resistor or ground | Neutral not connected | Recycle stream left out |
| Wrong connection | Series instead of parallel | Star wired as delta | Stream sent to the wrong unit |
| Wrong tool setting | Simulation stop time too short | Wrong meter range | Wrong solver or unit settings |
| Wrong measurement | Probe on the wrong node | Ammeter wired in parallel | Reading the wrong axis |
| Wrong assumption | Ideal diode used at low voltage | Losses ignored | Ideal gas law at high pressure |

What a fault card holds:

- **Type:** one of the seven above.
- **Target misconception:** the concept and misconception it tests.
- **How to plant it:** the exact change to the lab state.
- **Visible symptom:** what the student will see go wrong.
- **Fixed when:** a check on the lab state or the output, within a tolerance.
- **Kiki's "why" questions:** three of them, from open to specific.
- **Explanation rubric:** how the English explanation of the fix is graded.

Where fault cards come from:

1. **Curated** by the team or faculty for the demo labs.
2. **Drafted by Gemini** for any new chapter, from the concept's misconceptions and the lab spec or the student's uploaded experiment sheet (feature 20).
3. **Checked by the simulator.** Each draft is run, and a card is kept only if its output differs visibly from the correct setup, so there are no unfindable faults.

**Demo scope:** two fault cards on the rectifier lab. One is Flipped (diode reversed). The other is Wrong tool setting (stop time too short to show a full cycle). Two students with different mistakes get different faults, which shows on stage that it isn't hard-coded.

**Honest limit:** Kiki's screen reading still covers only the 5 to 10 known states of each lab. We claim the fault design works for any course, not that any course's lab works automatically yet.

## Closing and coming back

### 14. Learning receipt

**Goal:** "Did I actually learn something?"

**Outcome:** The student sees evidence of what changed in this session and leaves with one next step. The system records a session summary and whether it was a good session: the can-do goal met in English, at least one ring colour moved, and a next step booked.

**Starts from:** the end of every lesson, the end of a lab (lab version), or the end of a revision (short version).

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Watches | Before and after side by side: "10 minutes ago: I don't know yet. Now: correct, in English." |
| 2 | Listens | Replays their Say it recording: "You said this, in English." |
| 3 | Watches | The XL ring fills Blue, Red and Yellow in turn. Green pulses if the lab is still to come |
| 4 | Watches | Zooms out to the map. The node lights up, current flows on, and the route counter drops |
| 5 | Reads | "3 new English words", and the dial change if there was one |
| 6 | Signs in, or skips | Only if not yet signed in (feature 4) |
| 7 | Shares, or skips | The share card for WhatsApp (feature 1) |
| 8 | Picks a next step | Two suggestions, for example "Next stop: Diode as a rectifier, 12 min" and "Remind me before Tuesday's lab" |
| 9 | Taps Done | Kiki's four-colour burst and an Odia goodbye, then back to the map |

Versions:

- **Honest version:** "Today you found a gap: current and voltage basics. That's what today was for." The ring shows only what the evidence supports.
- **Lab version:** prediction against result, debug time and Green filling.
- **Revision version:** only the relit node and the next flicker date.

**Edge cases:**

- **No "before" question in this session:** show first try against final try instead.
- **No recording:** skip step 2.
- **Left before the end:** a mini receipt on the next open: "Last time you…"
- **In a hurry:** Skip is always visible, and the whole receipt takes at most 90 s.

**Done when:** the receipt works out and shows all three good-session checks from real evidence, and finishes within 90 s.

### 15. Revise

**Goal:** "Don't let me forget it."

**Outcome:** Mastered concepts stay mastered, with less help each time, which is the adaptive fade-out from the vision doc. The system records retention checks, the flicker schedule and the dial level used in revision.

**Starts from:** a flickering node, a notification, "Continue with Kiki" choosing revision, or exam-day mode.

A node starts to flicker after 2, 5, 12 and then 30 days without use. These intervals are a starting point to tune.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Taps a flickering node | Offers a "2-minute recharge" |
| 2 | Answers 3 or 4 quick questions | One term (Red), one concept (Blue) and one English answer (Yellow), with less help: the dial suggests one notch more English and hints start one rung higher |
| 3 | Gets them right | The LED relights, current flows, and the next flicker is scheduled further out |
| 4 | Misses one | Only that segment dims. Kiki offers a 3-minute mini lesson on that part |

**Edge cases:**

- **Many nodes flickering at once:** Kiki bundles at most three, highest exam weight first, so it never feels like a pile.
- **Exam within 3 days:** revision comes before new route stops.

**Done when:** a mastered node can be set to flicker with a demo time-skip control and relit through a 2-minute check.

### 16. Reminders and notifications

**Goal:** "Remind me at the right time."

**Outcome:** The student comes back at moments that matter, with no guilt. The system records opt-ins, chosen times and which reminders were opened.

**Starts from:** "Remind me" on the receipt or the lab tease, or Me settings.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Taps "Remind me" | Suggests times: tonight 8 pm, tomorrow 7 am, or custom |
| 2 | Picks a time | Kiki explains in Odia why it wants to send notifications, then the browser asks. If declined or unsupported, offers "Add to Google Calendar" |
| 3 | Gets the reminder | Specific text, such as "Diode node is flickering. 2 minutes?" Tapping opens that exact step |

Reminder types: lab warm-up the day before, a flickering node, "2 stops left before mid-sem". At most one per day, with quiet hours from 10:30 pm to 7 am. No streak warnings.

**Edge cases:**

- **iPhone:** web notifications only work once the app is added to the home screen, so Google Calendar is the main fallback.
- **Three reminders ignored in a row:** frequency halves automatically.

**Done when:** a reminder set on the receipt arrives on time and opens the exact step.

### 17. Mastery view

**Goal:** "How far have I come?"

**Outcome:** The student sees overall progress across the four dimensions, their growth in English, and their milestones. This view only reads data, apart from its settings.

**Starts from:** the Me tab, or the profile ring on the map.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Opens Me | A large subject ring with four bars underneath: Concept, Words, English and Lab, each with counts ("7 of 10 concepts") |
| 2 | Scrolls | English growth: the dial level over the weeks and the number of words owned |
| 3 | Scrolls | Milestones such as "First concept without Odia", "First lab without hints" and "10 words owned". Each can be shared |
| 4 | Opens settings | Default dial, sound, reminders, name on shares, switch account, delete my data |

**Edge cases:**

- **Brand-new student:** an empty state with one glowing hole: "Your first component goes here."
- **Delete my data:** confirmed in both Odia and English.

**Done when:** after the demo session, Me shows the correct four-bar summary from learner state and at least one milestone.

## Kiki everywhere

### 18. Ask Kiki and the hint ladder

**Goal:** "I'm stuck. Help me."

**Outcome:** The student gets unstuck with the least help they need, and is never handed the answer first. The system records which hint rung was reached on each question, which lowers the confidence in that mastery, and what they asked.

**Starts from:** Kiki's dots on any screen (tap or hold), a "not yet" answer (Kiki offers help), or being stuck in the lab.

**Ask Kiki** (the student starts it):

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Taps Kiki | A small sheet with three suggestions for this screen ("Explain this more simply", "Show me a picture", "What does this word mean?"), plus mic and text box |
| 2 | Or holds Kiki and speaks, in Odia or English | Kiki's dots become equaliser bars while listening |
| 3 | — | Kiki answers with an action first: a simpler card one notch toward Odia, a diagram, a highlighted term, or pointing at a lab control. Any text is at most two sentences, with audio |
| 4 | Asks about something outside the chapter | "Good question! That's in Transistors, later. Want a one-line answer now?" |

**Hint ladder** (on a question). Each rung takes one tap on "Another hint":

1. **Question back:** "What happens to the depletion region in reverse bias?"
2. **Nudge:** Kiki points at the relevant part of the diagram or the key term.
3. **Worked step:** the first step of the solution.
4. **Answer:** the answer with its explanation, followed by a similar question to try alone.

**Edge cases:**

- **"Just tell me the answer":** Kiki explains why it asks first, but the answer is always at most three taps away. Nothing is locked.
- **Kiki isn't confident:** it says so and offers a question card to take to the professor: "Ask your professor: …"
- **Off-topic or inappropriate request:** a short, polite redirect back to the lesson.
- **Gemini is slow:** "Thinking…", then a cached fallback for the demo concept after 4 s.

**Done when:** on every check in the diode lesson, all four rungs appear in order, and the rung reached shows up in learner state.

## Your own material

### 19. Your notes become lessons

**Goal:** "Teach me from my professor's notes."

**Outcome:** The student's own material (slides, notes, handouts, textbook pages) becomes lessons in the dial format, mapped onto their concept map. As the team agreed in the call, the student's material is the first source of truth and our curated content fills the gaps. The system records the sources uploaded, the concepts found, how they map to nodes, and which source each lesson card came from.

**Starts from:** "Add your notes" on the map or a node sheet, "Make your route exact" after the receipt, or sharing a PDF straight from WhatsApp into the app (possible once it's installed to the home screen).

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Taps "Add your notes", or shares a PDF from WhatsApp | A picker for PDFs, photos of pages, or a Google Drive file |
| 2 | Picks the files | Kiki: "Reading 24 pages…". Gemini pulls out topics, definitions, diagrams and worked examples |
| 3 | Reviews "What I found" | Topics matched to map nodes. Topics not on the map are offered as new nodes marked "from your notes". The student confirms |
| 4 | Opens a lesson on one of those nodes | Cards are generated from their notes first and curated content second. Each card has a source tag ("From your notes, page 7") that shows the page snippet when tapped |
| 5 | Meets a disagreement | Kiki shows both versions: "Your professor uses 0.6 V. Many books use 0.7 V. Use your professor's in the exam." |
| 6 | Taps "Compile my mid-sem pack" | A route plus a one-page summary per node at their dial level, which they can download |

**Edge cases:**

- **Poor scans or handwriting:** a warning on each affected page, and unreadable pages are skipped.
- **Odia-language notes:** accepted too.
- **Very large uploads:** the first 50 pages are processed and the rest queued.
- **Copyright and privacy:** a student's uploads stay private to them. Only material uploaded by faculty is shared with a class.

**Done when:** uploading the demo professor's 10-page PDF produces source-tagged lesson cards for at least 3 nodes within 60 s, and shows a conflict note for one planted difference.

### 20. Experiment sheet upload

**Goal:** "Help me with this exact experiment."

**Outcome:** Kiki knows the student's actual experiment: aim, circuit, component values, procedure, expected output and readings table. It sets up the lab and fault cards from that. The system records the experiment spec, the concepts it maps to, and the fault cards generated.

**Starts from:** the lab link on a node, a lab QR code, or "Upload experiment sheet" in the lab Brief.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Photographs the experiment sheet or lab manual page | Checks readability and crops the page |
| 2 | — | Gemini pulls out the aim, circuit, component values, procedure, expected output, and any viva questions on the sheet |
| 3 | Checks the summary card and edits values if needed | "Half-wave rectifier, 230 V to 12 V transformer, 1N4007 diode, 1 kΩ load. Expected: positive half-cycles only." |
| 4 | Confirms | If a supported lab template matches, it loads with their values, and fault cards are drafted and checked (feature 13) |
| 5 | — | If no template matches, Guide mode: a step checklist, a concept warm-up and viva prep from the sheet, honestly without screen guidance |

**Bench labs** (real equipment, no simulator, including chemical wet labs): the student types readings into the sheet's table and Kiki checks them against the expected values. For example: "Your reading at 5 V looks too high. Check the meter range."

**Edge cases:**

- **Unreadable circuit diagram:** Kiki asks for the key values directly.
- **Sheet doesn't match the chosen node:** Kiki asks which concept it belongs to.

**Done when:** photographing the demo rectifier sheet loads the browser lab with the sheet's component values.

## Exam and viva practice

### 21. Snap your answer (the X factor)

**Goal:** "Will this answer get marks in the exam?"

**Outcome:** A handwritten exam answer is graded like a university exam, with concept marks and English marks separated and drawn on the student's own handwriting. They see exactly which marks the English cost and how to get them back. The system records concept and English scores per marking criterion (Blue and Yellow evidence) and the student's recurring English errors.

**Starts from:** "Practise a 5-mark answer" after a lesson, exam practice on the route, a past-paper question on a node sheet, or the Me tab.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Picks a question, or takes Kiki's | "Explain the working of a half-wave rectifier with a neat diagram (5 marks)." Shows the marking scheme in plain words: definition 1, diagram 1, working 2, waveform 1. Optional 8-minute exam timer |
| 2 | Writes the answer on paper, then taps Snap | Camera with a page-edge guide. Several pages allowed |
| 3 | — | Checks readability and crops. Gemini reads the handwriting and the diagram |
| 4 | Sees the result | Their own photo with marks drawn on it: blue ticks and notes for the concept under each criterion, yellow underlines where the English cost marks. Score: "Concept 4/5 · English cost you 1 mark" |
| 5 | Taps a yellow underline | An Odia explanation, the corrected English sentence, and the term sticker if one applies |
| 6 | Opens "Rewrite" | A model answer built from their own content, not a generic one, with the changes highlighted |
| 7 | Tries again and snaps a second time | Attempt 1 and attempt 2 compared in the receipt |

**Edge cases:**

- **Parts of the handwriting can't be read:** those lines are greyed ("couldn't read"), with an option to type them or retake.
- **Diagram missing or partial:** the diagram is scored on its own.
- **Answer written in Odia:** the concept is graded, and the English version is shown as the model.
- **Uncertain grading:** show a range ("3 to 4 marks"), never false precision.
- **Privacy:** photos are private and deleted after 30 days unless saved.

**Done when:** three prepared handwritten demo answers (strong, weak English, weak concept) each get the correct split marks drawn on the photo within 15 s.

### 22. Viva with Kiki

**Goal:** "Don't let me freeze in the viva."

**Outcome:** The student practises an oral exam in English, either a lab viva or an interview, and learns to answer out loud. The system records the questions, answer transcripts, freeze moments (long silences) and rephrases needed. This feeds Yellow and Green.

**Starts from:** "Practise your viva" at the end of a lab, a node sheet, the interview goal, or a reminder the day before a lab exam.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Picks Lab viva (from the experiment) or Interview (concept questions) | Kiki switches to examiner mode, its dots lining up formally |
| 2 | Listens | A spoken English question: "What is the peak inverse voltage of the diode in a half-wave rectifier?" |
| 3 | Answers by voice | The voice scope draws the answer live |
| 4 | Stays silent for 6 s | Kiki rephrases in simpler English. After another 6 s, it offers the question in Odia, recorded as support |
| 5 | Continues through 5 questions | Difficulty rises, with follow-ups such as "Why?" based on their answers |
| 6 | Sees the result card | For each question: concept right or not, English clarity, freeze moments. The top 3 phrases to practise, and replay for any answer |

**Viva survival phrases:** Kiki also teaches the English phrases that buy time in a real viva, such as "Could you please repeat the question?" and "May I draw it?". Using them counts as a skill, not a weakness.

**Edge cases:**

- **Noisy room:** a typed fallback.
- **Asks for a repeat:** always allowed.

**Done when:** a 5-question rectifier viva runs by voice, with the rephrase and the Odia fallback both working.

## More ways to learn

### 23. Watch mode

**Goal:** "Just show me. I'm tired of reading."

**Outcome:** A 60 to 90 second narrated explainer per concept, following the call's "image with audio" idea. Narration is at the student's dial level, and English terms appear on screen as chips while they are spoken. The system records how much was watched, replays and the dial level. Short generated video is used only where motion matters, such as current flow, and is generated in advance.

**Starts from:** "Watch instead" on an Explain card, a node sheet, revision, or the mid-sem pack.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Taps Watch | The player opens with captions on and the dial visible |
| 2 | Watches | Diagrams and illustrations play in sequence with mixed Odia and English narration. Term chips pop up as they are spoken |
| 3 | Taps a chip | Pauses and opens the term sheet (feature 10) |
| 4 | Moves the dial mid-play | The narration switches language mix at the next sentence |
| 5 | Reaches the end | One check question, which counts as light Blue evidence |

**Edge cases:**

- **Low data:** audio and still images only, about 1 MB per concept.
- **No sound:** captions carry everything.
- **Downloadable:** for offline study (feature 25).

**Done when:** the diode explainer plays at two dial levels with term chips in sync with the narration.

### 24. Software tour

**Goal:** "What is all this on the screen?"

**Outcome:** A first-timer knows each panel of the lab tool before the experiment starts, which lowers lab anxiety. This is the call's "what each window does" idea. The system records tour completion and which panels were revisited.

**Starts from:** the first lab visit, the "?" button in the lab, or a lab QR code for a first-timer.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Opens the lab for the first time | Kiki: "First time here? 2-minute tour." Skip is always offered |
| 2 | Follows the spotlight | It moves panel by panel (parts palette, board, wire tool, Run, scope) with each name in English, an Odia explanation and audio |
| 3 | Does a tiny task on each panel, such as "Drag any part onto the board" | Moves on to the next panel when done |
| 4 | Finishes | "You can find this tour again under ?" |

For real tools later (MATLAB, Multisim, LTspice), the same tour pattern runs on screenshots of known screens, or as a narrated video.

**Done when:** the tour covers every panel of the browser lab, each with one tiny task, in under 2 minutes.

### 25. Offline packs

**Goal:** "Let me study in the hostel without data."

**Outcome:** Lessons, stickers and audio for chosen nodes are downloaded, and progress syncs later. The system records packs downloaded and work queued offline.

**Starts from:** "Download for offline" on a route or a node.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Taps "Download for offline" | Shows the size ("12 MB") and downloads on Wi-Fi by default |
| 2 | Studies offline | Lessons, explorables, stickers and Watch audio all work. English answers are queued: "Kiki will check this when you're online" |
| 3 | Comes back online | Progress syncs and the queued results arrive as a notification |

**Edge cases:**

- **Low storage:** offers a smaller pack without audio.

**Done when:** the diode lesson runs in airplane mode, and queued answers are graded on reconnecting.

## Teachers and trust

### 26. Class pulse for teachers

**Goal (teacher):** "Where is my class stuck, and is it the concept or the English?"

**Outcome:** For each concept the teacher sees three numbers: mastered, language gap and concept gap. They also see the top misconceptions and a suggested action. Only class totals are shown, in groups of at least 10, and individual students stay private unless they choose to share. This is the scale story for judges, because no existing tool can tell a professor this.

**Starts from:** the faculty link with the class code, or a weekly email summary.

| Step | Teacher does | Product responds |
| --- | --- | --- |
| 1 | Opens the class link and signs in with their college Google account | The class map |
| 2 | Looks at the map | Each node has a bar split into mastered, language gap and concept gap. Example: "Reverse bias: 62% language gap, 15% concept gap" |
| 3 | Taps a node | The top 3 misconceptions with anonymised example answers, and the most common English stumbling words, such as "depletion" and "bias" |
| 4 | Picks an action | "Send a 5-minute revision to the class" adds a route stop for everyone. "Make 2 bilingual slides for tomorrow's lecture" generates them with Gemini |
| 5 | Uploads their own notes or slides | They become the first source of truth for the whole class (feature 19) |

**Edge cases:**

- **Class smaller than 10:** the splits are hidden to protect privacy.
- **Individual answers:** never shown unless the student shares them.

**Done when (demo):** a seeded class of 40 synthetic students shows the three-way split on all 10 nodes. A static screen in the pitch is enough.

### 27. Report a problem and the glossary

**Goal:** "This Odia explanation is wrong."

**Outcome:** Mistakes in AI-written content get caught and fixed, and every English term has one approved Odia explanation used everywhere. The system records reports and glossary versions.

**Starts from:** a long-press on any sentence or term.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Long-presses and taps "Something wrong?" | Choices: wrong meaning, bad Odia, wrong science, other. Optional voice note |
| 2 | Sends it | Kiki says thanks. The card shows "Reported" and offers the explanation at another dial level meanwhile |
| 3 | — | The report goes to a review queue for the team or faculty. A fix to a glossary term updates every lesson that uses it |
| 4 | Gets a notification later | "Fixed. Your report helps 38 classmates." |

**The glossary:** one approved Odia explanation per English technical term. All content generation uses it, which keeps terms consistent across lessons, as the architecture doc asks.

**Edge cases:**

- **Spam reports:** rate-limited.

**Done when:** the report flow works end to end, and a glossary edit changes the term sheet everywhere it appears.

## Kiki guidance

### 28. Kiki explains (walkthrough)

**Goal:** "Explain it to me like a teacher would."

**Outcome:** The student follows a narrated explanation in which every sentence is tied to a word or a part of the diagram, and can pause, step back or tap any word. The system records steps played, pauses, replays, words opened in the lens (support), and the dial level during narration.

**Starts from:** the "Kiki explains" card in every lesson (after the Hook), "Explain it again" from the hint ladder, or Watch mode (the same script played as a video).

Kiki has two forms. The four dots stay in the caption bar. The **pointer** (a cursor with two eyes and the four dots trailing behind it) moves over the content. The student's own finger or cursor is never replaced.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Presses play | The caption bar plays sentence 1 (Odia first, English under it, following the dial). The pointer flies to the word and an underline sweeps under it |
| 2 | Keeps listening | Each sentence moves the pointer and marks one target (see the table below). The rest of the paragraph dims while a word is marked |
| 3 | Taps pause, or taps any word | Narration pauses. A tapped word opens in the lens with its Odia meaning and Hear it |
| 4 | Steps back or forward | Replays that sentence and its mark |
| 5 | Reaches the end | "Got it, next", or "Explain it more simply": one notch toward Odia, with a regenerated script |

How Kiki marks a word. Always one target at a time, in the colour of the skill being taught:

| Mark | Looks like | Used for | Colour |
| --- | --- | --- | --- |
| Sweep | An underline draws itself under the word as Kiki says it | First mention of a term | Red for technical words |
| Marker | A highlighter stroke behind the word; the rest of the paragraph dims to 40% | The one idea of this sentence | Red for terms, blue for ideas |
| Lens | The word is marked and a card opens under it: the word at 28px, its Odia meaning, Hear it | A new or hard term | Red |
| Connect | A dashed line from the word to the matching point on the diagram, which pulses | Tying a word to the graph or circuit | Blue |
| Circle | A hand-drawn loop around the word | Exam vocabulary, a word to use exactly | Yellow |

Text is never enlarged in place, so the paragraph never reflows. Only the lens zooms. In the lab, the same pointer follows the LabGuide pattern: show me once with a ghost drag, wait at the part for the student's turn, tilt and explain after a wrong move, dim everything except the next control and tap it, then ask "why" at the output (feature 13).

**Edge cases:**

- **Reduced motion:** the pointer jumps instead of flying, and marks appear instantly.
- **Sound off:** the captions carry everything.
- **Dial changed mid-walkthrough:** the captions switch at the next sentence.
- **Generated scripts:** Gemini writes the steps as structured JSON. A step whose target isn't in the paragraph is skipped, and a card has at most 8 steps.

**Done when:** the diode walkthrough plays 6 steps using all five marks in the right colours, and pause, step back and tap-a-word all work.

## Practice and repair

### 29. Exam practice sets

**Goal:** "Practise the mid-sem the way it's actually written."

**Outcome:** The student attempts a full set on paper, against the clock, and gets an analysis: marks for each question split into concept and English, the total lost to English, and the weak spots. The system records rubric outcomes per question and concept (Blue and Yellow evidence), time taken and recurring English errors. Handwriting photos stay private.

**Starts from:** Kiki's prompt on the home map ("Practise for the mid-sem?"), a route milestone, three days before the exam, a reminder, "Practise this topic" on a node sheet, or later a set assigned by a teacher.

When Kiki prompts: after every 3 completed stops, and 5 days and 2 days before the exam. At most once a day, never during a lesson.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Sees Kiki's prompt and taps "Practise for the mid-sem" | Offers three sets: Kiki's mock (built from the stops covered and past-paper weights), a past paper from the class (needs feature 7), or a single 5-mark answer (feature 21) |
| 2 | Starts the timer | The question paper in the university's format: questions, marks, "draw a neat diagram". Each question can be read in Odia on tap; answers are written in English |
| 3 | Writes on paper, then taps "I've finished writing" | The camera opens with a page-edge guide. Each page is checked for readability, and pages can be reordered |
| 4 | Sends the pages | Kiki shows the marking steps: reading the handwriting, matching answers to questions, marking the concept, marking the English. Gemini reads the handwriting and diagrams and marks each answer against its rubric |
| 5 | Reads the analysis | The score, a bar split into earned, lost to English and lost to concept gaps, a row per question with its own split, and "Fix these before the exam" |
| 6 | Taps a question | That answer marked up on the photo (feature 21): blue for concept, yellow where English cost marks, an Odia explanation and an exam-ready rewrite |
| 7 | Taps "Make my repair map" | Builds the repair map (feature 30) |

Marking rules are the same as feature 11. Grammar that doesn't block the meaning costs nothing. A wrong technical word counts as English cost. An unattempted question counts as a concept gap unless the student marks it "skipped for time". When Gemini is unsure, it shows a mark range.

**Edge cases:**

- **Missing question numbers:** Kiki asks the student to match each answer to its question.
- **Unreadable page:** retake that page only.
- **Answer written in Odia:** the concept is marked, and the English version is shown as the model.
- **Over time:** it is marked anyway, and the time is shown.

**Done when:** the three demo handwriting pages for the 5-question mock produce the 17/25 analysis (3 marks lost to English, 5 to concept) within 20 s.

### 30. Repair map

**Goal:** "Tell me exactly what to fix before the exam."

**Outcome:** A short, separate map of the weak spots from one practice set, ordered by the marks they can win back, each with its own fix and a re-test at the end. Passing the re-test lights those stops on the main map. The system records repair items, fixes done and the re-test result, and updates the evidence.

**Starts from:** "Make my repair map" on the analysis, a "4 repairs left" card on the home map, or a reminder.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Taps "Make my repair map" | Each weak spot becomes a dashed repair node, ordered by marks lost. A concept gap pulls in its prerequisite when the evidence says it is missing |
| 2 | Reads the map | Each node shows the gap type (Concept or English), the marks lost, the minutes needed and the fix. Total time and the exam date are on top |
| 3 | Taps "Start repair" | Fixes run in order, with Kiki's pointer as the pin. Concept gap: a short Kiki explains plus an explore and a check. English gap: a words drill, then rewriting their own answer in exam English. Missing diagram: draw it along with Kiki. One wrong word: a 2-minute drill |
| 4 | Takes the re-test | 4 new questions on the same concepts, written and snapped, or typed if time is short |
| 5 | Passes | The repair nodes light up on the main map and the wires reconnect. If not passed, a node stays with a smaller fix |

**Edge cases:**

- **More than 6 weak spots:** show the top 5 by marks and list the rest as "later".
- **Exam within 2 days:** only the English fixes and the biggest concept gap.
- **A second practice set:** its repairs merge into the same map, and duplicates combine.

**Done when:** from the demo analysis, the repair map shows 4 fixes in order of marks lost, each with its minutes, and a re-test node.

## Bringing anything

### 31. Ask Kiki or add anything

**Goal:** "Here's my question, my notes, my syllabus. Teach me from it."

**Outcome:** Whatever the student brings goes through one door: a typed or spoken question, a homework photo, notes, a syllabus, a past paper or an experiment sheet. It is matched to what already exists first, so there are no duplicates. Anything new becomes validated lessons at the right scope (one idea, a topic or a chapter), with page-level source tags. This feature replaces separate upload entry points for features 7, 19 and 20, and is the front door of feature 18. The full screen-by-screen spec is Module 3 of the Student journey tab.

**Starts from:** Kiki's dots on any screen, the Ask bar on Today, or "I have a question right now" on the first page.

| Step | Student does | Product responds |
| --- | --- | --- |
| 1 | Types, says, snaps or attaches something | Kiki reads it and states what it found: "6 pages of notes on material balances" |
| 2 | Waits a few seconds | Kiki matches it to existing concepts. A question about something known gets a short answer and "Open the lesson". Notes on known concepts are attached as sources |
| 3 | Sees a proposed outline for anything new | Scope badge, broad concepts and concepts, "You have this" marks, out-of-scope list, minutes |
| 4 | Edits or approves the outline | Generation starts in route order; the first lesson is ready in about a minute, labelled Kiki-made |
| 5 | Starts the first lesson, or leaves | The rest finish in the background, with a notification; the new plan appears on the Map and in the route |

**Edge cases:**

- Blurry or dark pages: Kiki asks for a retake of only those pages.
- Something that is not study material: Kiki says so and offers to answer a question instead.
- A homework question: hints first, and the full worked answer after one attempt.
- An outline larger than 5 broad concepts: Kiki proposes two chapters.
- A syllabus arriving later: concept-scope plans from questions fold into their chapter, and progress carries over.

**Done when:** in testing, a typed Mathematics question, 6 pages of Chemical Engineering notes and an Electronics syllabus each end in a playable, validated lesson without a single subject-specific screen; the same question asked twice opens the same concept.
