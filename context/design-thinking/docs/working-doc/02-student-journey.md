# Student journey, screen by screen

Oct 11, 2026 · @Arpan

This tab defines every screen a student sees, from the first page to the last repair, for any subject, chapter, topic or single question. Each screen lists what it shows from top to bottom, every button and what it does, the states it must handle, and the data it reads. The diode chapter supplies the example values only; every screen works the same way for a Chemical Engineering topic built from notes or one Mathematics question typed at night.

## App map

![app map · 4 tabs, 1 Kiki door, 15 modules](../diagrams/app-map.png)

Every way in leads through one short onboarding into four tabs. Kiki's dots, on every screen, are the single door for anything the student brings, which is what keeps the product general. Lessons, checks, receipts, revision and practicals are full-screen flows that the tabs open; they hide the bottom bar until the student finishes or closes them.

## Rules every screen follows

These rules hold on every screen below, so the per-screen specs only list what is different.

**The shell.** A main screen has a top bar and a bottom bar. Full-screen flows (onboarding, a lesson, a timed paper, the camera, a practical) hide the bottom bar and show a close button instead, so the student is never pulled out by accident.

| Part | What it holds | Behaviour |
| --- | --- | --- |
| Top bar, left | Course switcher: the course title and a down arrow ("Basic Electronics") | Opens a sheet listing the student's courses, "My questions" (their self course) and "Add a course" |
| Top bar, right | Kiki's four dots | Tap opens Ask Kiki (Module 3). The dots show Kiki's state: idle, thinking, has a suggestion |
| Bottom bar | Four tabs: **Today**, **Map**, **Practice**, **Me** | The current tab is filled in blue ink. Tapping the current tab scrolls it to the top |
| Teaching screens | The language dial chip, top right beside Kiki ("Dial 3") | Opens the dial (Module 5). Shown wherever there is teaching text: lessons, Ask Kiki answers, feedback, marked answers |

**Navigation rules.**

- Back always returns to where the student came from; it never skips a step they have not seen.
- Closing a lesson, a paper or a practical mid-way asks once ("Leave the lesson? Your place is saved.") and then saves the exact beat or page.
- Deep links (smart links, notifications, share cards) open the target screen with Today underneath, so Back lands somewhere sensible.

**Kiki.** Two forms only: the four dots for presence and the pointer for guidance. Kiki suggests; the student decides. Kiki never moves the dial, never auto-plays sound without the voice setting on, and never blocks a screen with a pop-up. A suggestion appears as one line beside the dots with two buttons: the action, and "Not now".

**The language dial.** One global setting with five notches: 1 Mostly Odia, 2 Odia with English terms, 3 Half and half, 4 English with Odia help, 5 Exam English. Only the student moves it. Kiki can suggest a notch ("Try one notch more English?"), and every change is recorded as evidence. Technical terms stay in English at every notch, in a term chip.

**Colour means a skill.** Blue concept, red words, yellow exam English, green lab (or the subject's practical label). Red never means wrong and green never means correct. A subject with no practical work shows three ring segments, not an empty fourth.

**Copy.** Short, plain sentences in sentence case, no emoji. "Not yet", never "wrong". Grammar and spelling that do not block meaning are never penalised.

**Generality.** No screen hard-codes a subject. Every label that varies comes from the data:

| On screen | Comes from |
| --- | --- |
| Course, chapter and concept names, can-do lines | `Course`, `LessonPlan`, `Concept` |
| The green dimension's name (Lab, Practical, Drawing, Code) and whether it shows | `SubjectProfile.practice` |
| Which beats a lesson has | What the concept contains: no interactive means no Explore beat; no practical means no Lab tease |
| Exam countdown and paper format | `Goal` and `ExamProfile`; hidden when there is no exam |
| "From your notes, page 3" tags | `SourceRef` on each piece of content |
| "Kiki-made" label | `review.status` is auto\_checked (not yet checked by a teacher) |
| Weight badges ("asked in 4 of 5 papers") | `examSignal`; hidden when its basis is none, marked "estimate" when estimated |

## Three key screens

![wireframes · first page, Today, Explain beat](../diagrams/key-screens-wireframes.png)

These are layout wireframes, not visual design; the Breadboard design system supplies the look. The first page asks for one tap. Today leads with one primary card. The Explain beat shows Kiki's pointer marking the phrase it is narrating, in the colour of the skill (red for a technical term), with the dial chip always in reach.

## Module 1: First page and onboarding

A new student goes from a link to their first lesson in about 60 seconds: one first page, a promise, up to five short questions, and their route. No sign-up is asked for until they have learned something (Module 8). Every question can be skipped; skipped answers get sensible defaults and can be changed in Me.

Flow: link preview > **1.1 First page** > 1.2 Promise > 1.3 Which feels easy > 1.4 About you > 1.5 Goal > 1.6 Plan > 1.7 Before > 1.8 Your route > first lesson.

### 1.0 Before the app: the link preview

What a classmate sees in WhatsApp before tapping. It is built from the smart link, so it names the real course and chapter.

- **Shows:** Kiki's four dots on paper, the title "Learn Diodes and rectifiers in Odia and English", one line "Explained in Odia. Written in exam English. Free.", and the short link.
- **Tap:** opens the web app in the phone's browser. No install and no store page. "Add to home screen" is offered only after the first lesson.
- **Generic rule:** the title uses the link's most specific target: concept, then chapter, then course. A share card shows the sharer's name and what they just learned.

### 1.1 The first page

The page that decides whether the student stays. It must load as text first on 3G, explain the product in one breath, and ask for nothing but one tap.

**Shows, top to bottom:**

1. **Top bar.** Empty on the left. "Sign in" as a text button on the right, for students who already have an account.
2. **Context chip**, only when the student arrived by a link. A class link reads "ECE 1st year · Basic Electronics · from your class group". A share card reads "Bikash shared: Half-wave rectifier". A direct visit shows no chip.
3. **Kiki arrives.** The four dots gather into the pointer, which looks up and waves once (about 1 second, skipped when the phone asks for reduced motion).
4. **Greeting, as a bilingual pair:** the Odia line first, the English line under it in a lighter weight: "Hello, I'm Kiki."
5. **The promise, two lines:** "Learn any chapter in Odia and English. Then write it in exam English." With a class link, a third line names the chapter: "Your class is on Diodes and rectifiers."
6. **Three proof lines, each with a small coloured mark:**
   - Blue: "Ideas explained in Odia, terms kept in English"
   - Yellow: "Your answers marked for the idea and the English separately"
   - Green: "Your syllabus, your notes, your exam" (the subject's practical label is not needed here)
7. **Primary button:** "Start", with "About 1 minute to set up" under it.
8. **Secondary button:** "I have a question right now".
9. **Footer:** "No sign-up needed. Your progress stays on this phone until you save it." Then a "Privacy" link and the app language switch "ଓଡ଼ିଆ | English".

**Buttons:**

| Button | What it does |
| --- | --- |
| Start | Creates an anonymous learner and goes to 1.2 Promise. Link details (course, chapter, exam date) are carried forward |
| I have a question right now | Opens Ask Kiki (3.1) straight away. The onboarding questions are asked after the first answer, in two steps: language, then course |
| Sign in | Google sign-in sheet. A known account goes straight to Today; an unknown one continues to 1.2 with the account attached |
| ଓଡ଼ିଆ / English switch | Changes the app's own labels (buttons, menus). It does not set the teaching dial; that is 1.3 |
| Privacy | A sheet: what is stored, that photos of answers are deleted after marking unless the student keeps them, and how to delete everything |

**States:**

- **Returning on the same phone with anonymous progress:** the greeting becomes "Welcome back", the primary button becomes "Continue" and goes to Today.
- **Slow network:** text and buttons render first from the cached shell; Kiki's animation loads last. The page never shows a spinner on its own.
- **Offline on the very first visit:** "You're offline. Connect once to get started." with "Try again". After the first visit, the shell and the first lesson are cached.
- **Expired or broken link:** the page falls back to the direct-visit version with one line: "That link has expired. You can still start."
- **Link to a single concept (share card):** Start skips 1.4 to 1.6 and goes from 1.3 straight to that concept; the skipped questions are asked after its receipt.

**Data:** reads `SmartLink` (course, plan, concept, class, exam date). Writes a new `Learner` (anonymous) with `onboarding.arrivedVia`.

### 1.2 Promise

Sets expectations for the next ten minutes, so the questions feel worth answering.

**Shows:** step dots in the top bar (five), Kiki saying "Here's what happens next", and a three-step strip: "1. Five quick questions (1 min)", "2. Learn one idea (10 min)", "3. See what changed". Below it, a preview card of the first concept: its title, can-do line and minutes. With no link, the card says "You'll pick the chapter in a moment".

| Button | What it does |
| --- | --- |
| Let's go | 1.3 |
| Skip the questions | Uses defaults (dial 3, goal "understand", the link's chapter or the course's first) and opens the first lesson. The questions wait in Me as "Finish setting up" |
| Close (top left) | Back to the first page |

### 1.3 Which feels easy

Finds the student's starting dial notch by letting them choose, not by testing them.

**Shows:** Kiki asking "Which of these is easiest to read?" Three cards show the **same sentence** at notches 1, 3 and 5. The sentence is the first concept's key idea, or a general science sentence when there is no course yet. Each card has a speaker button. After a pick, a second, smaller pair compares the chosen notch with its neighbour ("And this one?").

| Button | What it does |
| --- | --- |
| A card | Selects it; the card gets a blue outline |
| Speaker on a card | Reads that card aloud at the voice setting's speed |
| Continue | Sets the dial to the chosen notch, shows "Your dial starts at 3. Change it any time from the dial chip." for two seconds, then 1.4 |
| Skip | Dial 3 |

**Data:** writes `Learner.dialLevel` and `onboarding.easyLanguageAnswer`.

### 1.4 About you

Ties the student to a course so everything after this is about their syllabus.

**Shows, with a link:** a confirmation card, "Basic Electronics · B.Tech · Semester 1 · \<college>", with two buttons, and an optional field "What should Kiki call you?".

**Shows, without a link:** three fields: University (search as you type), Branch or course (search, free text allowed) and Semester (chips 1 to 8). Below them sit two escape routes: "Add my syllabus instead" and "I'm not in college".

| Button | What it does |
| --- | --- |
| That's me | Confirms the course, then 1.5 |
| Change | Opens the three fields, prefilled |
| A search result | Picks a course that already exists, often built from a classmate's syllabus. The card says "Built from your class's syllabus" |
| My course isn't listed | Accepts free text, creates the course with no chapters yet, and offers syllabus upload on the route screen |
| Add my syllabus instead | Camera or PDF picker, then the intake flow (3.3) builds the course; onboarding resumes at 1.5 while it reads |
| I'm not in college | Puts the student in a self course ("My questions"); the goal question offers only "Understand" and "Ask a question" |

**Data:** reads `Course` and `ClassGroup`; writes `Learner.courseIds` and `displayName`.

### 1.5 Goal

**Shows:** "What do you want first?" and four cards, each with one line on what happens next:

| Card | Next |
| --- | --- |
| Prepare for an exam | 1.6 Plan, with exam type chips: mid-sem, end-sem, internal, quiz |
| Get ready for a lab or practical | Asks when the lab is and which experiment (the course's practicals, or "Add the experiment sheet"), then 1.7 |
| Understand a chapter | Asks which chapter (the course's plans), then 1.7 |
| Answer one question I have | Opens Ask Kiki (3.1); the route is built later from what they ask |

A class link with an exam date preselects "Prepare for an exam" and the date; the student can change it. The "lab" card uses the subject's practical label and is hidden for subjects with no practical work.

**Data:** writes a `Goal`.

### 1.6 Plan (exam goal only)

**Shows:** the exam date (a date chip, prefilled from the link, with "I don't know yet"), the chapters it covers (a checklist of the course's plans, prefilled from the syllabus or the link, with "Not sure: include all"), and minutes a day (chips: 10, 20, 30, 45). A live summary sits at the bottom: "12 days · 9 stops · about 20 min a day".

| Button | What it does |
| --- | --- |
| Date chip | Date picker; past dates are disabled |
| A chapter | Toggles it; the summary updates |
| Minutes chip | Sets minutes per day; the summary updates, and warns gently if the plan does not fit ("That's 35 min a day. Want to start with the highest-weight stops?") |
| Continue | 1.7 |

**States:** a course with no chapters yet shows "Add your syllabus, or type the chapter names" with a camera button and a text field. A date under 3 days away switches the route to exam-day mode (Module 9).

### 1.7 Before

Captures a baseline so the receipt can show real before-and-after proof.

**Shows:** "Before we start: how sure are you about \<first concept>?" and a five-step bar labelled from "Never heard of it" to "Could teach it". Under it, an optional "Try one quick question" card with the first concept's easiest concept check.

| Button | What it does |
| --- | --- |
| A step on the bar | Records the self-rating |
| Try one quick question | Shows the check inline. Any answer is fine; Kiki says "Thanks. We'll see how this changes." No right-or-wrong colour is shown |
| Continue | Builds the route, then 1.8 |

**Data:** writes `onboarding.beforeScore` and, if answered, an `Attempt`.

### 1.8 Your route

The end of onboarding: the student sees a plan that is about their exam, and one obvious next step.

**Shows, top to bottom:**

1. Title: "Your mid-sem route" (or "Your path through \<chapter>" when there is no exam).
2. A countdown card in ink: "Mid-sem · Thu 23 Oct · 12 days", with "9 stops · 2 h 39 min · about 20 min a day".
3. The stop list. Each stop shows its number, the concept title, minutes, a weight badge ("asked in 5 of 5 papers", or "estimate") and a reason chip ("high weight", "needed first", "from your notes").
4. The first stop is raised, with "Start here".
5. A bridge stop, when the baseline suggests one: "Class 12 check: Semiconductor basics · 2 min".
6. A Kiki line: "Got your professor's notes? Add them and I'll teach from them."

| Button | What it does |
| --- | --- |
| Start: \<first stop> | Opens the lesson player (Module 5) |
| Why this order? | A sheet: "Needed first" stops come before what builds on them; then the highest exam weight; then your notes |
| Edit route | The route editor (4.4) |
| Add notes (Kiki line) | Ask Kiki with the attach tray open (3.1) |

**States:** while a new course is still being generated from a syllabus, the first stop is playable and the rest show "Preparing" with a thin progress line. With no exam date, the countdown card is replaced by "Set an exam date".

**Data:** reads `Route`, `Concept` and `examSignal`; writes `Route`.

## Module 2: Today

Today is the home tab. It answers one question, "what should I do now?", with one primary card and at most four supporting cards. It is the first screen for every returning student.

### 2.1 Today

**Shows, top to bottom:**

1. **Shell:** course switcher, Kiki's dots, bottom tabs with Today selected.
2. **Greeting:** "Good evening, Bikash" and a quiet line "3 lessons this week". There are no streak flames, because they turn missed days into guilt.
3. **Goal card, in ink:** "Mid-sem · Thu 23 Oct · 12 days" and "4 of 9 stops · on track" (or "1 stop behind: 25 min catches you up"). Hidden when there is no dated goal.
4. **Continue card (primary):** the next stop's title, can-do line and minutes, with the main button "Continue with Kiki: V-I characteristic". A lesson left half-way reads "Resume at step 5 of 9".
5. **Ask bar:** a pill reading "Ask Kiki anything, or add your notes", with camera, microphone and attach icons inside it.
6. **Up to four supporting cards**, chosen by the order rules below.
7. **Your route:** the next three stops in compact form, then "See all".

**Supporting cards and their order.** Kiki picks the top four that apply, in this order:

| Order | Card | Shown when | Main button |
| --- | --- | --- | --- |
| 1 | Fix next | A repair plan has open items | "2 fixes from your practice paper · 9 min" opens the repair map (10.8) |
| 2 | Recharge | A mastered concept's review date has passed (it flickers) | "2-minute recharge" (9.1) |
| 3 | Practical soon | A scheduled practical is within 3 days, and the subject has practicals | "5-minute warm-up" (11.3) |
| 4 | Practise for the exam | A dated exam goal exists and at least 3 stops are done | "Practise for the mid-sem" (10.1) |
| 5 | Words | 3 or more word stickers are due for practice | "Practise 5" (7.3) |
| 6 | Preparing | A generation job is running | "3 of 6 lessons ready · Start the first" |
| 7 | Finish setting up | Onboarding questions were skipped | "2 questions, 30 seconds" |
| 8 | Exam-day revision | Locked until exam day; shown in the last 3 days | "Opens on 23 Oct" |

**Buttons:**

| Button | What it does |
| --- | --- |
| Goal card | Map tab, route view (4.1) |
| Continue | Lesson player at the saved beat (Module 5) |
| Ask bar | Ask Kiki (3.1); each icon opens it with that input ready: camera, voice or the file picker |
| A supporting card's button | As in the table |
| "Not now" on a supporting card | Hides it until tomorrow; Kiki remembers |
| A route stop | The concept sheet (4.3) |
| See all | Map tab, route view |

**States:**

| State | What changes |
| --- | --- |
| Just finished onboarding | Only the goal card, Continue, the Ask bar and the route show |
| No course yet ("I'm not in college", or arrived by asking) | The Ask bar becomes the main element, then "Your questions" (concept-scope plans as a list) and "Add a course" |
| Exam today | Exam-day mode: "Mid-sem today, 2 pm" and the exam-day revision card first. No new concepts are suggested |
| Exam date passed | "How did the mid-sem go?" with Good, OK and Hard, then "Snap your paper to see where marks went" (10.4) and "Set the next goal" |
| Route complete | "Route done", then "Practise a full paper" and "Pick the next chapter" |
| Offline | Banner: "Offline. 3 downloaded lessons work." Cards that need the network are dimmed with "Needs internet" |

**Data:** reads `Goal`, `Route`, `ConceptState`, `RepairPlan`, `Practical` and `PracticalRun`, `WordSticker` and `GenerationJob`.

## Module 3: Ask Kiki or add anything

This is how the product stays general. Whatever a student brings, they bring it through one place: Kiki's composer. They can type a question, say it, snap a homework question, add notes, add a syllabus, a past paper or an experiment sheet. Kiki works out what it is, matches it to what already exists, and only then offers to build something new. Every input becomes a `StudyRequest` (data model tab).

### 3.1 Kiki's composer

A bottom sheet that opens from Kiki's dots on any screen, from the Ask bar on Today, or from "I have a question right now" on the first page. It opens half-height and drags up to full.

**Shows, top to bottom:**

1. **Context line:** what Kiki assumes the question is about: "About: Half-wave rectifier" inside a lesson, "In: Basic Electronics" elsewhere. Tap it to change or clear it.
2. **Three suggestion chips** that depend on context. In a lesson: "Explain it more simply", "Why 0.7 V?", "Give me an exam question". On Today: "What's on my mid-sem?", "Add my notes", "Quiz me on yesterday".
3. **The thread** of this conversation, newest at the bottom.
4. **Input row:** a text field reading "Ask in Odia or English", then microphone (hold to talk), camera, attach, and send.
5. Under the field, when empty: "You can also add notes, a syllabus, a past paper or an experiment sheet."

**Buttons:**

| Button | What it does |
| --- | --- |
| Suggestion chip | Sends that text as the question |
| Microphone (hold) | Records; the transcript fills the field for editing before it is sent. Odia, English and mixed speech are all accepted |
| Camera | Camera with page edge detection. One shot for a question; "Add more pages" for notes. Then 3.3 |
| Attach | File picker for PDFs and photos. Then 3.3 |
| Send | Sends the question, which is answered in the thread (3.2) |
| Context line | Change the course or concept the question is about, or clear it |
| Close or swipe down | Closes the sheet; the thread is kept in Me > Your questions |

**What Kiki does with each kind of input:**

| The student sends | Kiki first | Then offers |
| --- | --- | --- |
| A question about something already in their course | A short answer at their dial notch, with term chips | "Open the lesson: \<concept>" |
| A question about something new | A short answer, labelled Kiki-made | "Make this a lesson (about 12 min)", which creates a concept-scope plan in the course, or in My questions |
| A chapter or topic name | Looks for an existing plan | Opens it, or shows an outline to confirm (3.4) |
| A photo of a homework or textbook question | "Is this the question?" with the transcript to confirm | Hints first (the hint ladder, 6.3), and the full worked answer after the student has tried once. Then "Practise more like this" |
| Notes or textbook pages | Reads them (3.3) and matches pages to concepts | "These pages cover 3 of your lessons. I'll teach from your notes there." plus "2 topics are new. Make lessons?" (3.4) |
| A syllabus | Reads it and builds the course outline | The outline (3.4), then a new route |
| A past paper | Reads it and maps each question to concepts | "Exam weights updated from 1 more paper" and "Practise this paper" (10.2) |
| An experiment sheet | Matches it to a practical or creates one | Opens the practical page with "From your experiment sheet" (11.1) |
| Something off-course or unsafe | A short, polite redirect | Back to the course |

### 3.2 Kiki's answer

**Shows, inside the thread:**

1. The answer, at the student's dial notch, 2 to 6 sentences, with technical terms in red term chips.
2. A small visual when one helps (from the matched concept, or generated and labelled Kiki-made).
3. A source line: "From your notes, page 3", "From your course" or "Kiki-made".
4. Action chips (below).

| Button | What it does |
| --- | --- |
| Kiki explains (play) | Kiki's pointer walks through the answer sentence by sentence, with narration |
| Explain more simply | Re-writes this answer one notch towards Odia. The global dial does not move; after the second use in a session, Kiki suggests "Move your dial to 2?" |
| Show in exam English | Re-writes this answer at notch 5, so the student sees the exam wording |
| Open the lesson, or Make this a lesson | As in the table above |
| Ask a follow-up | Focuses the input field |
| Term chip | The term sheet (7.1) |
| This is wrong | Report a problem (12.7), with the answer attached |

**When opened on a question the student is answering** (a check, a practice question), Kiki gives hints, not answers, following the hint ladder (6.3).

### 3.3 Reading what you sent

**Shows:** thumbnails of the pages with a slow scanning sweep, and live lines that update as Kiki works: "Reading 6 pages", "Found: material balances, degrees of freedom", "Matching with your course". A Cancel button.

| State | What the student sees |
| --- | --- |
| A page is blurry or dark | "Page 4 is hard to read" with Retake and Skip this page |
| Mixed Odia and English handwriting | Read as is; nothing to do |
| A file type we cannot read | "I can read photos and PDFs. Try a photo of the page." |
| The pages are not study material | "These don't look like notes or a question. Want to ask me something instead?" |
| It takes longer than about 20 seconds | "Still reading. I'll tell you when it's done." The student can close the sheet; a notification follows |

### 3.4 Confirm the outline

Before building anything new, Kiki shows the plan and the student approves it. This keeps the student in control and stops duplicates.

**Shows:**

1. The title, and a scope badge: "Chapter", "Topic" or "One idea".
2. "Based on: Professor's notes, pages 1 to 6".
3. The outline: broad concepts, each with its concepts. Each concept shows its minutes, and "You have this" when it matches an existing concept.
4. "Not included": the named out-of-scope topics.
5. The total, "About 26 min".

| Button | What it does |
| --- | --- |
| Make these lessons | Starts generation (3.5) |
| A title | Edit it in place |
| × on a concept | Removes it from the plan |
| Drag handle | Reorders concepts |
| Add a topic | Type a topic name to add |
| Not now | Saves the outline as a draft in Me > Your material |

**States:** if the outline would need more than 5 broad concepts, Kiki proposes splitting it into two chapters. If every concept already exists, the screen becomes "You have all of this" with "Open the chapter".

### 3.5 Preparing lessons

**Shows:** each concept in route order with its stage: Writing, Checking, Ready. The first concept is ready in under a minute and shows "Start now". Under the list: "Kiki-made lessons pass automatic checks. A teacher hasn't checked them yet."

| Button | What it does |
| --- | --- |
| Start now | Opens the first ready lesson; the rest keep building |
| Notify me | Closes the screen; a notification arrives when everything is ready |

**States:** "One lesson didn't pass my checks. I'm fixing it." (retried automatically). If a lesson cannot be built: "I couldn't build \<concept> from these pages. Add a clearer page, or I'll use the course's own lesson."

### 3.6 Where it lands

A new plan appears on the Map with a "New" marker and joins the route at the place the student chose. Concept-scope plans from questions collect in the course as "Your questions", or in the "My questions" course when there is no course. When a syllabus arrives later, Kiki offers to fold them into the right chapter. Progress carries over, because it is keyed to the concept.

## Module 4: Map and route

The Map tab shows where the student is in the course. It has two views of the same data: **Route** (an ordered to-do list toward the goal) and **Map** (the breadboard: every concept as a node with its four-colour ring, wired by prerequisites).

### 4.1 Map tab

**Shows, top to bottom:**

1. **Shell**, with the Map tab selected.
2. **A two-way switch:** Route | Map. It remembers the last view.
3. **Route view:** the goal header (as on Today), then every stop. Each stop shows its number, title, minutes, weight badge, reason chip and state: done (full ring), in progress (partial ring), next (raised), later. Finished stops collapse under "4 done".
4. **Map view:** each lesson plan is one breadboard rail, labelled with its title and progress ("Diodes and rectifiers · 4 of 12"). Broad concepts are clusters on the rail and concepts are nodes. Thin traces show prerequisites.
5. **Filter chips** (Map view): All, In my exam, Needs work.
6. **A legend button**, bottom right.

**Node states (Map view):**

| State | Looks like |
| --- | --- |
| Not started | An outlined node with an empty ring |
| In progress | A ring filled per dimension |
| Mastered | A full ring |
| Flickering | The ring pulses softly; the review date has passed |
| Repair | A small wrench badge, from a practice paper (not red, which means words) |
| Bridge | A dashed node for a school topic ("Class 12: Semiconductor basics") |
| Has a practical | A small chip in the subject's practical colour and label |
| From your notes | A small page mark |
| Kiki-made | A small dot with an info sheet on tap |
| New | A "New" tag for 3 days after generation |

**Buttons:**

| Button | What it does |
| --- | --- |
| Route or Map switch | Changes the view |
| A stop or a node | The concept sheet (4.3) |
| A rail title | The plan page (4.2) |
| Filter chip | Dims the nodes that do not match |
| Pinch, drag | Zoom and pan the map; double-tap resets |
| Legend | A sheet explaining the node states and the four colours |
| Edit route (Route view, top right) | Route editor (4.4) |

**States:** a course with many chapters shows each rail collapsed to its progress bar until tapped. A course with no chapters yet shows "Add your syllabus to see your map" with the camera and attach buttons. In the My questions course, the map is a simple list of question plans.

**Data:** reads `LessonPlan`, `BroadConcept`, `Concept`, `ConceptState` and `Route`.

### 4.2 Plan page

One chapter, topic or question plan in full.

**Shows, top to bottom:**

1. Title, with a scope badge (Chapter, Topic or One idea).
2. "The question this answers": the plan's governing question.
3. The can-do line: "By the end you can…".
4. A stats row: number of concepts, minutes, mastered count, and an exam weight summary.
5. Sources: "From your syllabus · your notes". Add "Kiki-made" or "Checked by your teacher" where it applies.
6. Each broad concept as a section, with its concepts as rows: ring, title, minutes, state.
7. "Practicals in this chapter", when there are any.
8. "Not in this chapter": the out-of-scope list, so students know the boundary.

| Button | What it does |
| --- | --- |
| Start, Continue or Revise (sticky at the bottom) | The first unfinished concept, or a chapter recharge when all are mastered |
| A concept row | The concept sheet (4.3) |
| Practise this chapter | A chapter practice set (10.2) |
| Chapter summary | 9.3 |
| Add notes for this chapter | Ask Kiki with the attach tray open and the context set to this chapter |
| Download | Saves the chapter for offline use (12.6) |
| Report a problem | 12.7, with the plan attached |

### 4.3 Concept sheet

A bottom sheet for one concept, opened from a node, a stop or a route row.

**Shows:**

1. The title and can-do line.
2. The four-colour ring with the label and a one-word level for each dimension: Concept, Words, Exam English and the subject's practical label (omitted when not applicable).
3. A status line: "Mastered 3 days ago · next check Fri".
4. "Learn first": prerequisite chips, each with its own small ring.
5. The terms it introduces, as chips.
6. Its exam weight and sources.
7. Its practical, if any.

| Button | What it does |
| --- | --- |
| Learn, Continue or Revise (depends on status) | Lesson player, or a recharge (9.1) when mastered |
| Practise one answer on paper | Snap your answer with this concept's worked question (10.10) |
| Open practical | 11.1 |
| Ask Kiki about this | Ask Kiki with the context set to this concept |
| A prerequisite chip | That concept's sheet |
| A term chip | The term sheet (7.1) |

### 4.4 Route editor

**Shows:** the stops with drag handles, the exam date and minutes-a-day controls at the top, and "Add a stop" at the bottom.

| Button | What it does |
| --- | --- |
| Drag handle | Reorders. If a stop moves before something it needs, a quiet chip appears on it: "Needs Forward and reverse bias first". It is a warning, never a block |
| × on a stop | Removes it. If later stops need it: "3 later stops build on this. Remove anyway?" |
| Add a stop | Search the course's concepts, or ask for a new one (Module 3) |
| Reset to Kiki's order | Restores the suggested order |
| Save | Saves the route and marks it as edited by the student, so Kiki never silently re-orders it again |

## Module 5: The lesson player

One concept, in 10 to 15 minutes, as a run of beats. Nothing in a lesson is authored per beat: the player builds the beats from what the concept contains, so a Chemical Engineering concept from notes and a Mathematics concept from a question play exactly like a diode concept.

**Which beats a concept gets:**

| # | Beat | Shown when | Built from |
| --- | --- | --- | --- |
| 1 | Hook | Always | `canDo`, `example.title`, `examSignal`, `sources` |
| 2 | Explain (three modes) | Always | `explanation`: walkthrough, text + visual, video |
| 3 | Explore | The concept has an interactive | `explanation.modalities.interactive` |
| 4 | Example | Always | `example` |
| 5 | Quick check | Always | Checks in the concept dimension |
| 6 | Collect words | The concept introduces terms | Checks in the words dimension, and `termIds` |
| 7 | Worked question | Always | `workedQuestion` and its rubric |
| 8 | Try in English | Always | A short\_english or long\_written check |
| 9 | Say it | A spoken check exists; otherwise it becomes Teach Kiki | A spoken check |
| 10 | Lab tease | The concept has a practical and the subject has practicals | `practicalId` |

The demo's separate "Kiki explains" and "Learn" beats are now one Explain beat with three modes, because they show the same explanation. Example and Worked question get their own beats because the data model has them for every concept.

### 5.0 The player shell

**Shows:** in the top bar, Close (×) on the left, then the progress bar with one segment per beat this concept has, the dial chip and Kiki's dots. In the bottom bar, the primary button (Next, Check or Continue), and "Explain more simply" as a text button wherever teaching text is on screen.

| Control | What it does |
| --- | --- |
| Close | "Leave the lesson? Your place is saved." with Leave and Stay |
| Progress segment | Jumps back to a finished beat to review it. Forward jumps are only allowed past beats with no question |
| Swipe right | Previous beat |
| Dial chip | Opens the dial: five notches with their labels and a live preview line. Moving it re-renders the current beat at once. Recorded as evidence |
| Kiki's dots | Ask Kiki, with the context set to this concept and beat |
| Explain more simply | The current text one notch towards Odia, for this concept only. The global dial stays; after the second use Kiki suggests a dial change |

### 5.1 Hook

**Shows:** the concept title; a promise card, "By the end you can: explain how a half-wave rectifier works and draw its waveforms"; a teaser question built from the example ("Why does your phone charger need a diode?"); the exam badge ("Asked in 5 of 5 papers", or "estimate"); a source tag when it is from the student's notes; and the minutes.

| Button | What it does |
| --- | --- |
| Start | Beat 2 |
| I know this already | Jumps to two quick checks, one concept and one words. Both right: the concept is marked mastered for concept and words, and the lesson continues at Try in English. Otherwise the lesson continues from beat 2, with no penalty |

### 5.2 Explain

Three modes over the same explanation, switched by a segmented control at the top: **Kiki explains** | **Read** | **Watch** (Watch appears only when the concept has a video). It opens in the concept's default mode, and the student's last choice wins after that.

**Kiki explains** (the walkthrough):

1. The visual at the top, then the explanation text at the dial notch, with term chips.
2. For each walkthrough step, Kiki's pointer marks the step's phrase (sweep, marker, lens, connect or circle) in the colour of its skill, while the narration plays.
3. A caption line at the bottom shows the narration sentence.
4. Controls: play or pause, previous step, next step, speed (0.75, 1, 1.25), captions on or off, and "Step 2 of 4".

**Read:**

1. The visual. Tap it to zoom; it has alt text.
2. The key idea in a boxed line.
3. The explanation text at the dial notch, with term chips.
4. Tapping a sentence toggles it between the current notch and exam English in place. The text is never enlarged.

**Watch:** narrated slides or the short clip, with captions in the chosen language. With data saver on, it shows the size first ("About 1 MB. Play?").

| Button | What it does |
| --- | --- |
| Mode switch | Changes mode and keeps the place: the walkthrough step maps to the sentence it marks |
| A term chip | Pauses the narration and opens the term sheet (7.1) |
| Next | Beat 3. Always enabled; the student decides when they have understood |

### 5.3 Explore

A hands-on moment, rendered by the interactive's kind. Kiki's prompt sits at the top, and "Kiki, show me" demonstrates once.

| Kind | What the student does | Example |
| --- | --- | --- |
| Parameter sweep | Moves sliders (with units) and watches live outputs and a plot | Diode voltage against current; mixer flows against outlet composition |
| Step through | Taps through a worked method one step at a time | The eigenvalue method on one matrix |
| Label parts | Drags labels onto the explanation's visual, then Check | The parts of a PN junction |
| Sort steps | Drags steps into order, then Check | The steps of a material balance |
| Compare toggle | Flips between two cases and sees what changes | Half-wave against full-wave output |
| Simulation | A small embedded run of the concept's practical | The rectifier on the oscilloscope |

Only Label parts and Sort steps count as evidence, as light concept evidence; exploring is never marked.

### 5.4 Example

**Shows:** the example's title and scenario on a card, with "So what?" at the bottom. Tapping it reveals the takeaway. A source tag shows where it came from.

| Button | What it does |
| --- | --- |
| So what? | Reveals the takeaway |
| Another example | Kiki writes one more at the same level, labelled Kiki-made |
| Next | Beat 5 |

### 5.5 Quick check

One or two concept checks. It starts at difficulty 1 and adds a difficulty 2 check only after a right answer. The question screen and the feedback are Module 6.

### 5.6 Collect words

**Shows:** the terms this concept introduces as a small stack. Each one is a term-match check; a right match collects it as a word sticker, which flies to Me > Words. Terms borrowed from earlier concepts show as "Already yours" when collected.

| Button | What it does |
| --- | --- |
| An option | Answers the match |
| Speaker | Plays the English pronunciation |
| Skip this word | Moves on; the word comes back in Practise 5 |

### 5.7 Worked question

The exam answer the student learns to write.

**Shows:**

1. The question and its marks: "Explain the working of a half-wave rectifier with waveforms (5 marks)".
2. The model answer, revealed one line at a time. Kiki marks each line: terms in red, ideas in blue, exam phrasing in yellow.
3. The rubric beside or under it. Each criterion lights up as its line appears ("1 mark: names pulsating DC").

| Button | What it does |
| --- | --- |
| Show next line | Reveals the next line and lights its rubric criterion |
| Show all | Reveals everything |
| Why this line? | Kiki explains that one line |
| Try it on paper | Snap your answer (10.10), marked against this rubric |
| Next | Beat 8 |

### 5.8 Try in English

**Shows:** an English check, such as "In two sentences, explain why the output has gaps." Under the box are two helps: **sentence starters** (exam phrasing chips such as "During the positive half-cycle, …", "This is because …") and a **word bank** of the concept's terms. Long-answer checks offer "Write on paper and snap".

| Button | What it does |
| --- | --- |
| Text box | Type in English. Mixed words are accepted; the feedback shows which words to put in English |
| Microphone | Dictation into the box |
| Starter chip or word chip | Inserts it at the cursor |
| Check | Feedback, split into idea and English (6.2) |
| Write on paper and snap | 10.10 |

### 5.9 Say it, or Teach Kiki

**Say it** (when there is a spoken check): the prompt, a hold-to-talk microphone with the voice scope showing input level, then the transcript and feedback on the idea, the terms used and clarity. One retry.

**Teach Kiki** (when there is no spoken check): Kiki asks a naive question about the concept ("Why doesn't current flow backwards?"). The student explains in English by voice or text, and Kiki marks the terms they used.

| Button | What it does |
| --- | --- |
| Hold to talk | Records; release to send |
| Try again | One more attempt; the better one counts |
| Type instead | A text box replaces the microphone |
| Not now | Skips it ("On a bus? It'll come back in your next recharge.") |

### 5.10 Lab tease

**Shows:** "Try it in the lab: Half-wave rectifier with a capacitor filter", the date if it is scheduled, and "5-minute warm-up". It uses the subject's practical label and is skipped when the concept has no practical.

| Button | What it does |
| --- | --- |
| Open practical | 11.1 |
| Later | Adds a Practical card to Today |
| Finish | The learning receipt (8.1) |

### 5.11 How the lesson adapts

| What happened | What the player does |
| --- | --- |
| Quick check "not yet" on the idea, twice | Back to Explain in a different mode, one notch simpler for this concept, then a sibling check |
| Language gap (idea right, English not yet) | The English beat opens with starters and the word bank already shown; Kiki suggests a simpler notch for explanations only |
| Right first time on both quick checks | Skips the second check |
| Hints used | The answer still counts, with lower weight as evidence |
| The student leaves | Saves the beat; Today's Continue card resumes there |

## Module 6: Checks, hints and diagnosis

Every question in the product, whether in a lesson, a recharge, a practice set or a viva, uses the same question screen and the same feedback. That feedback always judges **the idea and the English separately**: the core promise.

### 6.1 The question screen

**Shows:** the prompt at the dial notch, with English terms in chips and a "Show in exam English" toggle so the student also meets the real wording. Below it is the answer area for the question type. The bottom bar has Check (disabled until there is an answer) and "I'm stuck".

| Question type | Answer area |
| --- | --- |
| mcq | Option cards; one can be picked |
| multi\_select | Option cards with ticks, and "Pick all that apply" |
| numerical | A number keypad, plus unit chips when the subject marks units. The tolerance is applied silently |
| term\_match | Tap a term, then its meaning (or drag) |
| fill\_blank | A sentence with a gap; type, or pick from the word bank |
| order\_steps | Cards to drag into order |
| label\_diagram | Labels to drag onto the visual |
| short\_english | A text box with dictation, sentence starters and the word bank |
| spoken | Hold to talk, with the voice scope; the transcript is shown before checking |
| long\_written | Type it, or "Write on paper and snap" (10.10) |
| diagram | A drawing canvas with axes when relevant, or "Snap a sketch" |
| derivation | Line-by-line entry, or snap |
| predict | The prediction canvas: draw the expected graph or outcome |
| code | A code box with run and check (after the hackathon) |

### 6.2 Feedback

**Shows:** a diagnosis card with two lines, each with its own colour mark: **Idea** (blue) and **English** (yellow), each reading "ready", "nearly" or "not yet". A third line, **Words** (red), lists exam terms used and "Exam words to add" when terms are expected. Under the card, the check's explanation. On the student's own answer, Kiki marks what they used: terms swept in red, the core idea marked in blue, exam phrasing underlined in yellow. The colours show skills, never right or wrong.

| Verdict | Kiki says (example) | Buttons |
| --- | --- | --- |
| Both ready | "Idea right. English exam-ready." | Next |
| Language gap | "Your idea is right. Now say it the exam way: 'depletion region', not 'empty area'." This counts as evidence for the idea | Fix the sentence (rewrite with the suggestion shown), Next |
| Concept gap | "Your English is clear, but the idea isn't there yet. Look at this part again." | See why (Kiki points to the phrase in the explanation), Try another |
| Both not yet | "Let's take this slower." | Explain again, simpler (one notch towards Odia for this concept), then Try another |

The card never says "wrong". A numerical answer with the right value and the wrong unit is a language-style gap: "Right number. The unit is mA, not A."

### 6.3 The hint ladder

"I'm stuck" climbs one rung per tap. Small dots under the button show how many hints were used. There is no penalty wording.

| Rung | What the student gets |
| --- | --- |
| 1. Nudge | A question back: "What does the diode do in the negative half-cycle?" |
| 2. Pointer | Kiki's pointer opens the explanation inline and marks the phrase that holds the answer |
| 3. Worked step | The first step of the solution, written out |
| 4. Show answer | The answer and its explanation. The check counts as "seen", not as mastery, and a similar check returns in the next recharge |

### 6.4 How the rings move (proposed)

| Ring | Evidence that moves it |
| --- | --- |
| Concept (blue) | Concept checks; the idea line of English checks; rubric criteria in marked answers; label and sort interactives |
| Words (red) | Term matches; exam terms used correctly in written and spoken answers; Practise 5 |
| Exam English (yellow) | English checks, spoken answers, Teach Kiki, and the English rubric in marked answers |
| Practical (green) | Predictions, guided steps, faults found, observations, viva answers. Hidden when the subject has no practical work |

Proposed thresholds, to tune in the pilot:

- A dimension is ready at 0.8, with at least two pieces of evidence.
- A concept is mastered when every applicable dimension is ready.
- Review dates follow 2, 5, 12 and 30 days. A concept flickers when its review date passes, and a recharge resets it.
- Answers given after hints count at half weight.

## Module 7: Words

Technical terms stay in English everywhere and become things the student owns.

### 7.1 Term sheet

A bottom sheet that opens from any term chip on any screen.

**Shows:** the English term in large type (never translated), with its symbol and unit when it has them ("Vm, volts"). Under it: a pronunciation button, the support-language explanation (the Odia gloss), the English definition, the sentence from the lesson where the student met it, "Used in" (the concepts that use it), and the collect state.

| Button | What it does |
| --- | --- |
| Speaker | Plays the English pronunciation, then the gloss when voice is on |
| Collect | Adds it as a word sticker (if it is not already collected) |
| Practise | A three-item mini practice for this word |
| A "Used in" concept | That concept's sheet (4.3) |
| Report | Report a problem with this term or its gloss (12.7) |

### 7.2 Words deck

In Me > Words.

**Shows:** "34 of 41 words in Basic Electronics", filter chips (All, Needs practice, New), and the stickers grouped by chapter. Each sticker shows the term and up to three strength dots.

| Button | What it does |
| --- | --- |
| A sticker | The term sheet |
| Filter chip | Filters the deck |
| Practise 5 | 7.3 |
| Course switcher | Shows another course's deck |

**Empty state:** "Words you meet in lessons collect here."

### 7.3 Practise 5

Five quick items on the weakest or most overdue words, in a mixed format:

1. Term to meaning.
2. Meaning to term.
3. Fill the gap in an exam sentence.
4. Say it aloud.
5. Use it in a sentence (typed).

The screen ends with the strength changes. Close is available at any item; progress so far is kept.

## Module 8: Learning receipt, share card and saving progress

The end of every lesson proves something changed, then asks for the sign-in only once that proof exists.

### 8.1 Learning receipt

**Shows, top to bottom:**

1. "What changed", with the concept title.
2. One tap first: "How sure are you now?" on the same five-step bar as the "before" question. Then the before and after bars side by side.
3. The four-colour ring animating from its value before the lesson to after, with each dimension's change ("Words +2").
4. Words collected, as stickers.
5. The English sample compare: the student's first English sentence in this lesson next to their best one, with Kiki's marks on both.
6. Time spent, and the modes used ("Listened and read").
7. An honest Kiki line when something did not move: "English didn't move today. Tomorrow's warm-up starts there."
8. A preview of the next stop.

| Button | What it does |
| --- | --- |
| Next: \<stop> | The next lesson |
| Practise one answer on paper | Snap your answer with this concept's worked question (10.10) |
| Share | The share card (8.2) |
| Done for today | Today. The first time, Kiki offers a reminder: "Same time tomorrow?" with Yes and No |

**Versions:** after the first lesson ever, the save prompt (8.3) follows the receipt. After a fast-track ("I know this already"), the before and after bars are replaced by "Fast-tracked: concept and words ready".

### 8.2 Share card

**Shows:** a preview of the image card: "I learned Half-wave rectifier in Odia and English", the course name, the student's first name and, only if they switch it on, their rings. Scores are never shown by default. The card carries a share link that opens the same concept for a friend (1.1, share-card version).

| Button | What it does |
| --- | --- |
| WhatsApp | Opens WhatsApp with the image and the link |
| Status or Story | Opens the share sheet with the image |
| Copy link | Copies the link |
| Save image | Saves it to the phone |
| Show my rings (switch) | Adds the rings to the card |

### 8.3 Save your progress

Shown once after the first receipt, and again after the third lesson if dismissed. Never more often.

**Shows:** "Save your progress so you don't lose it", and what is saved: rings, words, route and answers. Below that, "Continue with Google" and "Not now".

| Button | What it does |
| --- | --- |
| Continue with Google | Signs in and merges the anonymous progress. A known account with progress asks which to keep, or merges both |
| Not now | Back to the receipt's next step. Progress stays on the phone |

### 8.4 Open it like an app

On Android browsers, after the first receipt: "Add Kiki to your home screen", with Add and Not now. It is not shown again for 14 days after Not now.

## Module 9: Revise

Short, well-timed revisits, so mastered concepts stay mastered.

### 9.1 Two-minute recharge

Opens from Today's Recharge card, a flickering node, the concept sheet or a reminder.

**Shows:** the concept title with its flickering ring and "Last studied 9 days ago". Then three cards, one at a time:

1. Recall the key idea in one sentence (typed or spoken, compared with the key idea).
2. One term match.
3. One concept check.

The end card reads "Recharged. Next check in 12 days."

| Button | What it does |
| --- | --- |
| Start | The first card |
| Answer controls | As in 6.1 |
| Open the full lesson | Shown if two of the three cards are "not yet"; opens the lesson at Explain |
| Done | Back to where the student came from |

### 9.2 Exam-day revision

It appears as a locked card for the last 3 days before an exam and opens on the exam day.

**Shows:**

1. "Mid-sem today, 2 pm · 5 h 12 min".
2. "5 quick checks on your highest-weight topics".
3. The key ideas sheet: every route stop's key idea on one page, at the dial notch, with English terms.
4. The terms and formulas sheet.
5. A calm line: "No new topics today."

| Button | What it does |
| --- | --- |
| Start checks | Five checks, highest exam weight first |
| Key ideas sheet | Opens the sheet; "Listen" plays Kiki reading it |
| Download PDF | Saves both sheets for offline or printing |

### 9.3 Chapter summary

Opens from the plan page.

**Shows:** the governing question, then each concept's key idea with a thumbnail of its visual and its term chips, grouped by broad concept.

| Button | What it does |
| --- | --- |
| Listen | Kiki narrates the key ideas in order |
| A concept | Its sheet |
| Download | Saves for offline use |

## Module 10: Practice

Written exam practice the way the exam is written: on paper. The student snaps the pages, Gemini reads the handwriting and marks each answer against its rubric for the idea, and against the English rubric for language. A repair map then turns the weak spots into short fixes. This is the X factor and the demo's closing moment. The paper format comes from the course's exam profile, so it works for any university pattern.

### 10.1 Practice tab

**Shows, top to bottom:**

1. **Shell**, with Practice selected.
2. **The last result** (once there is one): "Last paper: 17/25 · 3 marks lost to English, not the idea", with "See report".
3. **Recommended:** Kiki's mock built from the route so far and the class's past papers, with "5 questions · 25 marks · 25 min".
4. **From your class:** past papers the class has added, each with its year and format.
5. **Quick:** "Just one 5-mark answer · 8 min".
6. **By chapter:** one set per lesson plan.
7. **Open repair maps**, with their fix counts.
8. **History:** past papers with date and score, newest first.
9. **"Add a past paper"**, at the bottom.

| Button | What it does |
| --- | --- |
| A set card | Its briefing (10.2) |
| See report | The last practice report (10.6) |
| An open repair map | 10.8 |
| A history row | That paper's report |
| Add a past paper | Ask Kiki with the camera ready; the paper is read and mapped to concepts (3.1), then offered as a set |

**States:** no past papers yet: "Add one past paper and I'll weight your route by it." Fewer than three concepts studied: the mock card says "Unlocks after 3 lessons" and offers the quick answer instead.

### 10.2 Set briefing

**Shows:** the title; what is in it (questions, marks, minutes); the chapters it covers; and the rules: "Write on paper like the real exam. When time is up, snap each page." A short checklist: paper, pen, quiet place. A note: "Questions are in exam English. In practice you can tap 'Show in Odia' on any question; I'll note it."

| Button | What it does |
| --- | --- |
| Timed or untimed (switch) | Timed is the default for mocks and past papers |
| Start | The paper (10.3) |
| Download paper | A PDF of the questions, for printing |
| Back | The Practice tab |

### 10.3 The paper

Full screen. Kiki is quiet: the dots are hidden during a timed paper.

**Shows:** the timer in the top bar, in ink ("24:10 left"; at 5 minutes it adds "5 min left" in text, with no warning colour), then the questions Q1 to Q5 with their marks. Each question has a small "Show in Odia" link.

| Button | What it does |
| --- | --- |
| Show in Odia | Shows the question at notch 2 under the English, and records it as support used |
| Pause | Untimed papers only |
| I'm done | Snap pages (10.4) |
| Close | "Leave the paper? You can snap what you have written later." |

When time runs out, one gentle alert reads "Time's up. Finish your sentence, then snap your pages."

### 10.4 Snap pages

**Shows:** the camera with page edge detection and auto-capture when the page is steady, and a strip of page thumbnails. After each capture, Kiki reads the question numbers on the page and shows chips ("Q1, Q2").

| Button | What it does |
| --- | --- |
| Shutter | Captures a page (auto-capture also works) |
| A thumbnail | Opens it: Retake, Rotate, Delete |
| Drag a thumbnail | Reorders pages |
| Question chips | Correct which questions are on the page |
| From gallery | Picks photos already taken |
| Done (3 pages) | Reading (10.5) |

**States:** blurry: "Hold still: page 2 is blurry". Too dark: "More light, please". Camera blocked: "Allow the camera, or pick photos from your gallery". A question with no page: "Q4 has no page. Skip it?"

### 10.5 Reading your answers

**Shows:** live steps: "Reading your handwriting (page 2 of 3)", "Marking Q3 against its rubric", "Checking the English". Below them: "About a minute. You can leave; I'll tell you when it's ready."

**Unclear lines:** when the reading confidence on a line is low, Kiki asks before marking: "Is this what you wrote?" It shows the cropped line and the transcript. The student can correct the transcript but never sees the marks before confirming, so corrections cannot chase marks.

### 10.6 Practice report

**Shows, top to bottom:**

1. **Concept marks:** "17 / 25".
2. **The headline:** "3 marks were lost to English, not to the idea."
3. **English, by criterion:** terms, structure, clarity and completeness, each marked "not yet", "nearly" or "exam-ready".
4. **One row per question:** the question number, marks out of total, a verdict chip (Fine, Idea, English, Both) and "See marked answer".
5. **Support used:** "Show in Odia on 2 questions".

| Button | What it does |
| --- | --- |
| See marked answer | 10.7 for that question |
| Build my repair map | 10.8 |
| Practise again later | Adds the set to Today for 3 days later |
| Share with my teacher | Sends the report to the class teacher (only if the student is in a class and chooses to) |

### 10.7 Marked answer

**Shows:**

1. The student's own page, cropped to this answer. Kiki's marks sit on it: a blue marker on the ideas that earned marks, a red circle where an exam term was missing, and yellow underlines on English that cost clarity.
2. Under it, the rubric. Each criterion shows the marks awarded and the evidence quoted from the answer.
3. The English criteria, each with its level and one tip.

| Button | What it does |
| --- | --- |
| Model answer (switch) | Shows the model answer's lines beside the student's, with matching criteria linked |
| Rewrite this answer | Type it again or snap a new page; it is re-marked and both versions are kept |
| A mark on the page | Shows that mark's reason |
| I think this mark is wrong | Kiki re-checks once and explains. If the student still disagrees, it is flagged for a teacher or the team, and the mark is kept until reviewed |
| Next or Previous question | Moves between answers |

### 10.8 Repair map

Weak spots become a short list of fixes, ordered by the marks they can recover.

**Shows:** a small map of only the concepts this paper touched, with repair badges, and under it the repair items. Each item has:

- the reason: "You knew the idea but didn't name the depletion region";
- the fix and its time: "Practise 5 words · 2 min", "2-minute recharge", "Rewrite Q2's opening · 4 min" or "See the worked question · 3 min";
- its status: to do, done, or re-tested.

| Button | What it does |
| --- | --- |
| Start fix | Opens the fix: a term practice, a recharge, a lesson beat, the worked question or a rewrite |
| Mark done | For fixes done off the app |
| Re-test me | A short re-test (10.9); available any time, suggested once all fixes are done |
| Add to route | Adds the fixes as route stops |

### 10.9 Re-test

One question per repaired spot, through the same flow as 10.2 to 10.6, shortened. The report marks each repair item "Fixed" or "Not yet", and the repair map updates.

### 10.10 Snap your answer (one question)

The one-question version of the whole loop. It opens from "Try it on paper" in a lesson, from the concept sheet, or from the Quick card.

**Flow:** the question and marks > write on paper > snap one page > reading > the marked answer (10.7) > a mini repair list of 1 to 3 fixes. It uses the concept's worked-question rubric, or a past question's rubric when one exists.

## Module 11: Practicals

One module for every kind of hands-on work: a browser simulation, a physical lab, a software tool, a drawing, coding or field work. The kind and the label come from the practical and the subject profile. The whole module is hidden for subjects with no practical work.

### 11.1 Practical page

**Shows, top to bottom:**

1. The title, with a kind badge: Simulation, Lab, Software, Drawing, Coding or Field.
2. The linked concepts, each with its ring.
3. The aim.
4. Apparatus or tools.
5. The scheduled date, if known: "Lab on Tue 21 Oct".
6. "From your experiment sheet", when the class sheet has been added.
7. The steps count, and the student's progress through them.

| Button | What it does |
| --- | --- |
| Warm up (5 min) | The guide (11.3) on the first steps, in the simulation or as a walk-through for a physical lab |
| Start | The full guide (11.3) |
| Software tour | 11.2; shown only when the tool has a tour |
| Add my experiment sheet | Ask Kiki with the camera ready; the sheet is attached and its steps replace the defaults (3.1) |
| Practise the viva | 11.7 |
| Set the lab date | A date picker; adds a reminder |

### 11.2 Software tour

Kiki's pointer walks through the tool's screen with a spotlight on one region at a time: "This is the oscilloscope. Channel 2 shows the voltage across the load." It has Back, Next, "Show me again" and Exit, and a step counter.

### 11.3 Guide: show me, then your turn

**Shows:** the lab stepper (the steps as a vertical list with the current one open), the tool or simulation area, and Kiki's pointer.

| Button | What it does |
| --- | --- |
| Show me | Kiki demonstrates the step: the pointer acts in the simulation, or an annotated picture for a physical lab |
| Your turn | The student does it. In a simulation the checkpoint is checked automatically; in a physical lab they tap "I've done this", optionally with a photo |
| I'm stuck | Practical hints: what to look at, then where, then the answer |
| Restart step | Resets the step |
| Next step | Opens the next step once the checkpoint is met |

### 11.4 Predict

**Shows:** the practical's prediction prompt ("Draw what you expect across the load before you run it") and the prediction canvas with labelled axes.

| Button | What it does |
| --- | --- |
| Draw | Freehand on the axes; Undo and Clear are available |
| Save prediction | Saves it and unlocks Run |
| Run | Runs the simulation and overlays the result on the prediction. Kiki comments on the difference ("You drew the gaps. Nice. The peak is a little lower because of the 0.7 V drop.") |

### 11.5 Run and observe

**Shows:** the simulation output, or for a physical lab the observation table from the practical, with columns and units, for the student to fill. Kiki compares the entered values with the expected result and points out values that look off ("This reading is double the others. Check the range setting?").

| Button | What it does |
| --- | --- |
| A table cell | Number entry with the column's unit |
| Check my readings | Kiki's comparison |
| Download table | A PDF or image for the lab record book |

### 11.6 Debug challenge

Kiki plants a fault from the practical's fault cards.

**Shows:** the symptom ("The output shows only the negative half-cycles") and the seven general fault cards, in the subject's wording. The cards are Component reversed, Wrong value, Missing piece, Wrong connection, Wrong tool setting, Wrong measurement and Wrong assumption.

| Button | What it does |
| --- | --- |
| A fault card | The student's guess at the type of fault |
| Tap the part | In a simulation, the student taps the faulty part |
| Fix it | Applies the fix; the output recovers |
| Reveal | Shows the cause and the fix; the answer counts as seen |

For a physical lab it becomes a scenario: "Your readings are all too low. What happened?" with the same cards.

### 11.7 Viva with Kiki

A spoken practice of the oral exam.

**Shows:** Kiki asking each viva prompt as a polite examiner, a hold-to-talk microphone with the voice scope, and the transcript. Each answer gets feedback on the idea, the terms and the English. The end shows "3 of 4 ready", with the weak ones sent to the repair list.

| Button | What it does |
| --- | --- |
| Hold to talk | Answers the question |
| Ask me again | Repeats the question, slower |
| Hear it in Odia | Repeats the question at notch 2, and records it as support |
| Next question | Moves on |

### 11.8 Practical receipt

**Shows:** steps done, the prediction against the result, faults found, the filled observation table, viva readiness and the change in the practical ring.

| Button | What it does |
| --- | --- |
| Download my record | The observation table and prediction as a PDF |
| Back to the lesson, or the next stop | Continues the route |

## Module 12: Me

The student's own space: what they have mastered, the words they own, the material they added, and their settings.

### 12.1 Me

**Shows, top to bottom:**

1. **Shell**, with Me selected.
2. **The student:** name, course, and "Saved to Google" (or a "Save your progress" button when anonymous).
3. **Overall rings for the course:** one ring per dimension, with the share of concepts ready.
4. **This week:** lessons done, and minutes.
5. **Sections:** Mastery, Words, Your material, Your questions, Courses and goals, Settings, Help.

Each section row opens its screen.

### 12.2 Mastery

**Shows:** two views, switched at the top. **By chapter** is every concept with its four-colour ring, grouped by plan. **By colour** picks one dimension, lists concepts weakest first, and offers a "Practise the weakest" button. Under both views, a small history: rings at the end of each week.

| Button | What it does |
| --- | --- |
| A concept | Its concept sheet (4.3) |
| A colour tab | Switches the dimension |
| Practise the weakest | A recharge on the three weakest concepts in that colour |

### 12.3 Words

The words deck (7.2).

### 12.4 Your material

**Shows:** everything the student added, newest first: notes, syllabus, past papers, experiment sheets and snapped answers. Each row shows its type, page count, status (Reading, Read, Needs help), where it is used ("Used in 4 lessons") and who can see it (Only me, or My class).

| Button | What it does |
| --- | --- |
| A row | Opens the pages, with the concepts each page feeds |
| Rename | Renames it |
| Share with my class | Syllabus and past papers only; classmates get the same course weights |
| Delete | "Lessons built from it stay, without the page tags." Snapped answers are deleted with their images |

### 12.5 Your questions

Every Ask Kiki thread, newest first. Each row has the question and the plan it became, if any. Tapping a row opens the thread.

### 12.6 Courses and goals

**Shows:** the student's courses (with a switch), each course's goals with dates, and "Add a course". "Finish setting up" appears here when onboarding questions were skipped.

| Button | What it does |
| --- | --- |
| A course | Makes it the current course |
| A goal | Edits the date, chapters or minutes a day; the route updates |
| Add a course | 1.4 About you, in a sheet |
| Archive | Hides a finished course and keeps its progress |

### 12.7 Settings

| Setting | Options |
| --- | --- |
| App language | ଓଡ଼ିଆ or English, for buttons and menus |
| Language dial | The current notch, with a small history of changes |
| Voice | On or off; speed 0.75, 1 or 1.25; auto-play walkthroughs |
| Reminders | Time of day; push or WhatsApp (opt-in); quiet hours |
| Data saver | No video by default; lower-resolution images; walkthrough audio only on Wi-Fi |
| Offline | Download chapters; storage used; remove a download |
| Account | Sign in or out; download my data; delete everything |
| Privacy | What is stored and for how long |

### 12.8 Help

| Item | What it does |
| --- | --- |
| Glossary | Every term in the course, A to Z and searchable, each opening its term sheet |
| Report a problem | Choose what is wrong: the explanation, the Odia, a mark, or the app. A screenshot of the last screen is attached and can be removed. Reported content is flagged and hidden after review |
| How marking works | A plain explanation of the idea and English split, and what is never penalised |
| Contact | Email the team |

Report a problem also opens from a long press on Kiki's dots on any screen.

## Module 13: Notifications and reminders

At most one nudge a day, except for results the student is waiting for. Nothing between 10 pm and 7 am. WhatsApp only with opt-in. Every notification ends with a way to stop that kind.

| Trigger | Message (example) | Opens | Counts toward the daily limit |
| --- | --- | --- | --- |
| Daily reminder at the chosen time | "20 minutes today: V-I characteristic is next." | The lesson at its saved beat | Yes |
| A concept starts flickering | "Semiconductor basics is fading. 2 minutes to recharge?" | 9.1 | Yes |
| Lab or practical tomorrow | "Lab tomorrow: half-wave rectifier. 5-minute warm-up?" | 11.3 | Yes |
| Exam in 3 days, and exam day | "Mid-sem in 3 days. Your highest-weight stop is Ripple factor." | Today | Yes |
| Lessons ready (the student started generation) | "Your 6 lessons from your notes are ready." | Plan page (4.2) | No |
| Paper marked (the student submitted it) | "Your practice paper is marked: 17 / 25." | 10.6 | No |
| A teacher shared a link with the class | "Your teacher shared: The Zener voltage regulator." | That concept | Yes |
| Missed 3 days | "Pick up where you left off? 10 minutes is enough." Sent once, never repeated | Today | Yes |

## Module 14: Teachers

Teachers are the scale story, not the demo's main path. They get three screens on the same web app, entered from "I'm a teacher" in the first page's footer.

### 14.1 Set up a class

**Shows:** four steps on one page: the course (search or create), the class name ("ECE 1st year, section B"), upload the syllabus and any past papers, and exam dates. Then the class link appears as a QR code and a WhatsApp message.

| Button | What it does |
| --- | --- |
| Upload syllabus or past paper | The intake flow (3.3); the course is built once and shared with every student who joins |
| Copy WhatsApp message | Copies a ready message with the class link |
| Print QR | A one-page PDF with the QR code, for the notice board or the lab door |
| Share a concept | A link straight to one concept, for after a lecture |

### 14.2 Class pulse

**Shows:** for each chapter, the concepts with the class's average ring. Then "Where the class is stuck": the top three concepts, each with its main reason: **mostly language** (the class knows the idea but cannot write it) or **mostly concept**. Then the class's most common misconceptions, and how many students are active this week. Only aggregates are shown; an individual's answers are seen only if that student shares a report.

| Button | What it does |
| --- | --- |
| A concept | Its breakdown by dimension and its common misconceptions |
| Share with the class | Sends that concept's link to the class |
| Set an exam date | Updates every student's goal date (they are told) |
| Download summary | A PDF for a department meeting |

### 14.3 Check Kiki-made lessons

**Shows:** lessons generated for the class's course that a teacher has not yet checked, with each worked answer and check answer laid out for review.

| Button | What it does |
| --- | --- |
| Approve | Marks the lesson "Checked by your teacher" for every student |
| Edit | Changes a line of an explanation, a worked answer or a check; the lesson re-validates |
| Flag | Hides the lesson until it is fixed |

## Module 15: States every screen handles

These apply everywhere, so individual screens only mention their exceptions.

| State | What the student sees |
| --- | --- |
| Loading | Grey skeleton cards in the shape of the real layout. No full-screen spinner for more than a second |
| Kiki thinking | The dots move in their thinking pattern; the first words of the answer stream in as they arrive |
| Generating | Named stages (Writing, Checking, Ready); the first item becomes usable early; the result carries a Kiki-made label |
| Offline | A thin banner: "Offline. Downloaded lessons still work." Answers and snapped pages queue with "Will send when you're online" and send by themselves later |
| Slow network | After three slow loads Kiki suggests data saver, once |
| Server error | "Something went wrong on our side. Your work is saved." with Try again. Typed answers are kept as drafts on the phone and never lost |
| Camera or microphone blocked | Why it is needed, a button to the phone's settings, and the alternative: pick photos instead, or type instead |
| Hard-to-read handwriting | "Is this what you wrote?" on the unclear lines only (10.5) |
| Flagged content | The lesson is hidden: "This lesson is being fixed. Try \<the related concept> meanwhile." |
| Kiki-made | A small label on generated content. Tapping it explains: "Made by Kiki from your notes and checked automatically. A teacher hasn't checked it yet." |
| Teacher-checked | "Checked by your teacher" in the same place |
| Empty | Every list has a one-line empty state that says what will appear and how to get it ("Words you meet in lessons collect here.") |

**Accessibility, everywhere:**

- Every voice line has captions.
- Every visual has alt text.
- Tap targets are at least 48 px.
- Reduced-motion settings stop Kiki's animations.
- Text can scale to 200% without overlap.
- Colour is never the only signal: every coloured mark also has a label or an icon.

## Decisions this tab makes

These choices are new in this tab, or change the clickable demo. All are proposed until the team agrees; set each row's status.

| # | Decision | Why | Changes in the demo | Status |
| --- | --- | --- | --- | --- |
| 1 | Four bottom tabs: Today, Map, Practice, Me. Words move into Me | Practice is the X factor and needs a home; words are owned, not visited daily | Nav was Map, Stickers, Me | Proposed |
| 2 | Kiki's dots open one composer for asking and for adding anything (notes, syllabus, past paper, sheet, homework photo) | One door keeps the product general and stops duplicate upload screens | Upload entries merge into Ask Kiki | Proposed |
| 3 | "I have a question right now" on the first page skips onboarding | A student with a question gets value first; setup follows | New button | Proposed |
| 4 | Every onboarding question can be skipped, with defaults | Respect for 17 to 19 year-olds; nobody is trapped in setup | Adds "Skip" | Proposed |
| 5 | Kiki explains and Learn become one Explain beat with three modes; Example and Worked question become their own beats | Matches the data model, which has these for every concept | Beat list changes | Proposed |
| 6 | "Explain more simply" changes only the current text; the global dial stays, and Kiki suggests a dial change after the second use | Keeps the dial student-controlled | Clarifies existing behaviour | Proposed |
| 7 | "I know this already" on the Hook fast-tracks a concept after two right checks | Saves time for students who already know it | New button | Proposed |
| 8 | Homework photos get hints before a full solution | Learning, not answer copying | New | Proposed |
| 9 | Kiki shows an outline for approval before building lessons from notes or a syllabus | The student stays in control, and duplicates are avoided | New screen (3.4) | Proposed |
| 10 | Proposed mastery thresholds (0.8 with two pieces of evidence) and review dates (2, 5, 12, 30 days) | A starting point to tune in the pilot | None | Proposed |
| 11 | At most one nudge a day, with quiet hours from 10 pm to 7 am | Reminders should feel helpful, not naggy | None | Proposed |
