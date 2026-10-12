# UX Working Doc — Bilingual STEM Learning (AI Builder Cup)

Oct 10, 2026 · @Arpan

## Decisions so far

We are closing the user experience (journey, onboarding, interaction model) before moving to the user interface (screens, components, visuals).

| Topic | Decision | Notes |
| --- | --- | --- |
| Subjects | Electronics, Electrical, Chemical Engineering | Matches the team's backgrounds. Exact chapter not fixed yet. |
| First regional language | Odia | Other languages later. |
| Language dial | Student controls it; the system only suggests | The system never moves the dial on its own. Each change is recorded as evidence. |
| Helper character | Kiki | Lab copilot and in-app guide. |
| Product name | None for now | Revisit later. |
| Visual direction | Google's four colours, playful but not kiddy | Users are 17 to 19 year-old engineering students. |
| Sequence | UX first, then UI | This doc tracks both as we iterate. |
| Demo scope | One branch, in depth. Recommended: Electronics (to confirm). | Electrical and Chemical appear on the branch picker as "coming soon". |

## Core UX concepts

The signature idea: Google's four colours are the four mastery dimensions from the architecture doc, and each concept is a ring that fills one colour at a time.

| Colour | Dimension | Student-facing meaning | Filled by |
| --- | --- | --- | --- |
| Blue | Concept | "I understand it" | Lesson checks, answers in any language |
| Red | Technical words | "I know what it's called" | Word stickers, term matching |
| Yellow | Academic English | "I can explain it in English" | English questions, Teach Kiki |
| Green | Practical | "I can make it work" | Lab tasks, debugging |

A right answer in Odia with a weak English answer keeps Blue full and lowers only Yellow. The screen says so: "You understand this. You just need the English words for it."

Supporting mechanics:

- **Concept map as a circuit board.** Concepts are components, prerequisites are wires. Mastery sends current to the next node. It works as a metaphor for all three branches: signals, power and process flows.
- **Route to Mid-sem.** A Google Maps-style blue route through the map, weighted by past papers, with an ETA. A wrong answer triggers "Rerouting…" through a missing prerequisite.
- **Language dial.** Odia-to-English slider on every lesson. Student-controlled. Kiki suggests a step toward English after a run of correct answers.
- **Word stickers.** Collectible term cards (English term, Odia meaning, audio, mini diagram, example sentence). Reused as drag-in chips when writing English answers.
- **Draw your prediction.** The student sketches the expected waveform or curve before running a simulation. The real output is overlaid on the sketch.
- **Detective debug.** A deliberately broken setup. Kiki asks "why" questions before giving any hint.
- **Teach Kiki.** The student explains the concept to Kiki in English, by voice or text. Kiki plays a confused junior.
- **Flickering nodes.** Mastered nodes dim over days. A short revisit with less help relights them (spaced revision).
- **Kiki's form.** Four Google-coloured dots that bounce while thinking, become an arrow to point, form a "?" to ask, and burst on success.

## Onboarding, end to end

Onboarding is one continuous story: a link arrives in a WhatsApp group, the student learns one concept in 10 minutes, and the session closes with proof they learned it plus a card they can share. Setup questions come after the first win, not before it.

We tell it through one fictional student, used in the demo too:

- **Bikash**, first semester, Electronics and Communication, at an engineering college in Odisha.
- Studied in Odia medium through Class 12.
- Basic Electronics mid-sem in 12 days. A diode rectifier lab next week.
- Has an Android phone with patchy data. Uses the college lab laptop for practicals.

&#91;embedded content: onboarding journey · 3 ways in, 1 session, 2 ways out\]

Whichever way they come in, students go through the same first open, session and close. The share card at the end is how the next student arrives.

## Step 1: How the link reaches them

Every way in is a **smart link**. It carries the student's class context, so they land on something useful with their details already filled in. Nothing to install: it opens in the phone's browser.

What a smart link carries:

| Part | Example | What it does for the student |
| --- | --- | --- |
| Destination | A concept, a mid-sem route, a lab walkthrough, a word sticker | Decides where they land |
| Class code | College, branch, semester, section | Pre-fills the syllabus and mid-sem date, and shows "38 classmates are on this route" |
| Referrer | The classmate who shared it | The first screen says "Shared by Rohan" |

The domain is to be decided, since there is no product name yet. Shape: `<domain>/route/basic-electronics?class=<code>&ref=<id>`.

The ways a link gets to Bikash:

| Channel | Who shares it | What they share | Where it lands |
| --- | --- | --- | --- |
| WhatsApp class group | Class representative, before mid-sem | "Basic Electronics mid-sem route" | The route, with the first stop open |
| WhatsApp, from a classmate | Any student, at the end of their session | "I can explain diodes in English" card | That concept's mini-lesson |
| Class QR code | Professor, on a slide in the first week | Class code | The branch map with the class pre-filled |
| Lab QR code | Lab instructor, printed on the experiment sheet | That experiment | On a phone: a 5-minute warm-up. On a laptop: Kiki's lab walkthrough |

What the WhatsApp message looks like:

- **A rich preview card.** WhatsApp shows the link's preview image and title. The image has Kiki's four dots, the concept name in English with an Odia subtitle, and "10 min · Odia + English".
- **A pre-written message** in mixed Odia and English. The sharer can edit it before sending.

How the first links get into groups:

- **For a real launch,** we recruit one faculty champion and the class representatives in each section. Before each exam they get a ready-made mid-sem route link. Lab instructors get printable QR sheets, one per experiment.
- **For the hackathon demo,** we open on a mock WhatsApp class group. The class representative's message and preview card are on screen, and we tap it.

Phone-to-laptop handoff for labs works like WhatsApp Web. The lab laptop opens a short address and shows a QR code. Bikash scans it with the phone, which is already signed in, and the laptop session joins their account.

## Step 2: First open, the first 60 seconds

Bikash taps the class representative's link. Within 60 seconds there is a greeting from Kiki, a clear promise of what the next 10 minutes will achieve, a language choice, and one "before" question. There is no sign-up, no form and no install prompt.

1. **Kiki arrives (0 to 2 s).** Kiki's four dots bounce in and join up while the page loads. The page is kept light so it loads on slow data.
2. **"Tap to hear Kiki" (2 to 10 s).** Browsers block sound until the user taps, so the first tap is the greeting. Kiki speaks in Odia, with the words on screen: "Namaskar! I'm Kiki. Rohan shared your Basic Electronics mid-sem route." Under it: "Shared by Rohan · 38 classmates on this route".
3. **The promise (10 to 30 s).** A route preview: "Mid-sem in 12 days · 9 stops · First stop: Diode, 10 min". Under it, today's goal as a can-do sentence: "In 10 minutes you'll be able to explain in English why a diode lets current flow only one way." A big blue Start button, and a small "Show me the whole map" link.
4. **"Which feels easy?" (30 to 50 s).** One Class 12 sentence about electric current, shown three ways: mostly Odia, mixed, mostly English. Bikash taps one and the dial is set. Kiki points to the dial: "You can change this any time."
5. **The "before" question (50 to 60 s).** Kiki: "What do you think right now? No marks." One question on today's goal, in English, with "I don't know yet" as a valid answer. Kiki cheers whichever they pick. This answer is saved for the before-and-after at the end of the session.

What the class code saved: college, branch, semester, syllabus and mid-sem date are already known, so Bikash never sees those questions.

## Step 3: The first session

The first session is one concept in about 10 minutes: the diode as a one-way gate, which builds on Class 12 semiconductors. A progress bar along the top shows the four ring colours filling as Bikash goes.

| Beat | Time | What Bikash does | What fills |
| --- | --- | --- | --- |
| 1. Hook | 30 s | Sees a phone charger and hears Kiki in Odia: "The socket gives AC, but your phone needs DC. Who decides which way current flows?" | Nothing yet |
| 2. Learn | 3 min | Short explanation at the dial position, with forward bias, reverse bias and cut-in voltage as tappable English chips. Drags a voltage slider and watches current flow one way only, with the V-I curve drawing live. Two quick check questions. | Blue |
| 3. Collect | 1 min | Gets three word stickers (forward bias, reverse bias, cut-in voltage), hears each one pronounced, and matches each to its picture. | Red, partly |
| 4. Try it in English | 2 min | Answers in English: "Why does a reverse-biased diode not conduct?" Can drag stickers into the answer. If wrong, Kiki diagnoses concept or language and reroutes. | Yellow, partly |
| 5. Say it | 1 min | Records one English sentence by voice: "A diode conducts when…". Kiki plays it back and points out one word to improve. | Yellow |
| 6. Lab tease | 30 s | Sees the locked green segment: "Build a half-wave rectifier in Tuesday's lab to complete this ring." Kiki offers a Monday-night reminder. | Green stays locked |

Beat 5 matters. Hearing your own voice explain an engineering idea in English is the moment we want Bikash to remember, and it feeds directly into the close.

## Step 4: Closing the session

The close proves learning with evidence, not praise. Bikash sees what they could not do 10 minutes ago and can do now, hears their own English, and leaves with one booked next step. It takes about 90 seconds.

1. **Before and after.** Kiki brings back the "before" question, side by side: "10 minutes ago: I don't know yet. Now: correct, in English." This is the core proof.
2. **Your voice.** Kiki replays the English sentence from beat 5: "You said this, in English."
3. **The ring.** Blue, Red and Yellow fill in turn. The Green outline pulses, locked until the lab.
4. **The map reveal.** The view zooms out to the whole route for the first time. The Diode node lights up, current flows to the next node, and the counter drops from "9 stops" to "8 stops". The full map is a reward here, not a setup screen.
5. **Words learned.** "3 new English words." If the dial moved toward English during the session, Kiki shows that too.
6. **Save it.** "Sign in with Google to keep your ring and route." The account ask comes now because there is something to lose. If they skip, progress stays on this phone.
7. **Share (optional).** An "I can explain diodes in English" card showing their ring, with a pre-written WhatsApp message. This is what brings the next student in.
8. **One next step.** Specific and timed: "Next stop: Diode as a rectifier, 12 min", or "Tuesday lab. 5-minute warm-up on Monday at 8 pm?" with a Remind me button.
9. **Goodbye.** Kiki's dots burst in four colours, with one line in Odia.

**When the session goes badly,** the close stays honest. "Today you found a gap: current and voltage basics from Class 12. That's what today was for." The ring shows only what the evidence supports, and the reroute appears as progress: "1 stop added, 6 min". Rings are never filled to make someone feel good.

**A good session, in measurable terms,** has three parts:

- The can-do goal is met: the "after" answer is correct in English.
- At least one ring colour moved forward.
- A next step is booked, either a reminder or a next stop.

## Arriving without a link

A student who finds the product directly, with no class code, adds only two short taps before the same first session. Everything else waits until after the first win.

1. Kiki greets, then "Which feels easy?" (same as Step 2).
2. **About me:** chips for college, branch and semester. For the demo, only Electronics is active and the other branches say "coming soon".
3. **What do you need?** "Mid-sem is coming", "Lab is confusing", "I'm lost in class" or "Get interview-ready". This picks the first node.
4. The "before" question, then the same 10-minute session and close (Steps 3 and 4).
5. **After the close:** "Make your route exact. Snap your syllabus or past papers." Gemini reads them, past-paper weights adjust the route, and they can pop the English words they already know to fill their sticker deck.

## How students use it day to day

Home is the map, not a feed. Most sessions are one tap on a big "Continue with Kiki" button, which runs the Learning Orchestrator's next step. A goal card sits above the map: "Mid-sem in 12 days. 3 stops left."

&#91;embedded content: core learning loop · diagnosis routes every answer\]

A concept gap sends the student back through a prerequisite. A language gap sends them to word stickers and an easier English version. Only answers solid on both move on to the lab.

| Mode | Device | How they enter | What Kiki does | Colours it fills |
| --- | --- | --- | --- | --- |
| Learn | Phone | Continue, or tap a node | Explains at the dial position, checks understanding, diagnoses | Blue, Red |
| Exam | Phone | Goal card or mid-sem date | Shows the route, runs past-paper practice, reroutes on misses | Blue, Yellow |
| Lab | Laptop | "Open on laptop" from a node, or the lab's QR code | Copilot overlay: points at controls, asks for predictions and "why", runs the debug case | Green |
| Revise | Phone | A flickering node or a notification | Two-minute checks with less help and a suggested notch toward English | All four |
| Teach Kiki | Phone, by voice | A ring three-quarters full, or the interview goal | Plays a confused junior, then gives feedback against a rubric | Yellow |

Interaction rules:

- **The dial is always in the lesson header.** The student can drag it any time. Kiki suggests a change with a chip ("3 right in a row. Try one notch more English?"), and the student taps "Yes" or "Not now". Moving toward Odia never costs points. It is recorded as evidence of how much support they need.
- **Kiki is present, not a chat window.** Four dots sit in the corner. Tap or hold to talk, in Odia or English. Kiki answers mostly with actions (a diagram, a simpler version, a hint, pointing at a control) rather than long text.
- **The hint ladder.** Kiki asks a question first, then gives a nudge, then a worked step, and only then the answer. Each rung used is recorded as evidence.
- **Diagnosis drives the next step.** A concept gap sends the student to a prerequisite node ("Rerouting…"). A language gap sends them to word stickers and an easier English version of the same question.
- **Notifications report progress, not guilt.** Examples: "Your Diode node is flickering", "2 stops left before mid-sem", "Lab tomorrow: 5-minute warm-up?". There are no streak warnings.
- **Mastery view.** Four colour bars per subject, a weekly English-percentage trend, the size of the sticker deck, and milestones such as "First concept without Odia". A weekly card can be shared to WhatsApp, which feeds back into acquisition.

## Recommendations on the open questions

Recommended: demo Electronics only, using a "Diodes and rectifiers" chapter that ends in a half-wave rectifier lab inside a browser-based simulator. The other seven answers follow from that choice. Change the status as the team decides.

| Question | Recommendation | Why | Status |
| --- | --- | --- | --- |
| Demo one branch or three? | One branch: Electronics | The lab gives the clearest visual payoff (AC sine wave in, rectified wave out), and the call already named its tools | Agreed |
| Which chapter and first node? | Diodes and rectifiers, about 10 nodes: semiconductor basics, PN junction, forward and reverse bias, V-I characteristic, diode models, half-wave rectifier, full-wave rectifier, filter capacitor, ripple, Zener regulator. First node: the diode as a one-way gate. | Builds on Class 12, appears in first-year Basic Electronics syllabi, and matches the architecture's 10-node target | Proposed |
| Which lab tool? | A browser-based lab that looks like a SPICE simulator, with 5 to 10 known screen states. Kiki still reads screenshots with Gemini. Debug case: the diode is placed backwards, so only the negative half-cycles appear. Real LTspice is the next step after the demo. | The architecture doc prefers a controlled browser simulation. Nothing to install on college laptops, the demo is reliable, and the draw-your-prediction overlay is easy on our own canvas. | Proposed |
| Is the dial one global setting or set per concept? | One global dial. Moving it inside a lesson applies to that lesson, then Kiki asks "Keep this everywhere?" | One setting is easy to understand. Differences between concepts appear as Kiki's suggestions, not as extra settings. | Proposed |
| Spoken-English listening check in onboarding? | Leave it out. Add listening inside lessons later: Kiki reads an English sentence aloud and the student picks its meaning. | Keeps the first minute short. Listening is better measured on real lesson content. | Proposed |
| Syllabus and past-paper upload in the 10-day scope? | Yes, narrowly. Upload one real syllabus or past paper; Gemini maps it onto our curated graph and counts topics. If parsing fails, fall back to the curated graph silently. | A strong Gemini multimodal moment for judges, kept reliable by the curated graph | Proposed |
| Phone-to-laptop handoff? | A QR code on the laptop, scanned by the signed-in phone, like WhatsApp Web. Google sign-in on the laptop as the fallback. | Lab laptops are shared, so students should not type passwords on them, and the pattern is already familiar | Proposed |
| What if Kiki is unsure what is on screen? | Below a confidence threshold Kiki never guesses: "I can't see clearly. Which screen are you on?" It shows three thumbnails of known states to tap. | Pointing at the wrong control destroys trust. A tap costs 2 seconds. | Proposed |
