# Storyboard: "Ravi, event day" (58 s breadth prototype)

Draft v0.1 · 20 Nov 2026 · Prototype · illustrative · For a motion designer or a HyperFrames build · Data: [scenario.json](scenario.json) · Turns: [tutor-flow.json](tutor-flow.json) `scriptedPath`

**What the video must prove in under a minute:** the same KiKi engine runs the full loop (Learn → Reflect → Do → Evidence) for a trader, in Hindi, on his own past trade, without giving advice. Order chosen for the story: Reflect before Do, because Ravi practises the fix after he has reasoned it out.

**Persistent on every frame**
- Bottom-left, 14 px, muted ink `#555a53` at 70%: **Prototype · illustrative**
- Bottom-centre on TR-01 to TR-09, 14 px: **Education on a past, illustrative trade. Not investment advice.**
- Beside every block of Hindi: a small outlined chip **Machine draft · native review pending**
- English subtitles under every Hindi line, for jurors

On-screen KiKi lines in TR-04 to TR-07 are shortened for reading time. The full scripted lines, routes, canvas cues and evidence are in `scriptedPath` (turn → shot mapping in each turn's `video` field).

## Shot list

| # | Time | Mode | On screen (what to build) | On-screen text | Narration |
|---|---|---|---|---|---|
| TR-01 | 0:00–0:04 | Case | Off-white desk `#f6f7f2`. A white sketchbook case card (2 px ink border, 4 px hard ink shadow, 6 px radius) slides up. Header in small caps; four rows; Ravi's written thesis in italic. Right: a small dark plot panel with a spot sparkline ticking up while a premium readout counts down ₹90.25 → ₹59.55 in plain ink (no red). | Header: "PAST TRADE · PAPER BOOK · ONBOARDING WEEK 2"<br>Rows: "24200 CE (weekly) × 4 lots · lot 75" · "Bought D-1 15:25 · ₹90.25" · "Sold D0 15:25 · ₹59.55" · "Spot 24,040 → 24,150 · +110"<br>Thesis: "Policy positive → index ऊपर → call खरीदे"<br>Headline: **"Direction सही। फिर भी loss।"** (EN: "Direction right. Still a loss.") | VO (EN): "Ravi called the direction right, and still lost money." |
| TR-02 | 0:04–0:07 | Learn | Push into a KiKi lesson page laid out like the real app's lesson screen: left rail of four numbered pages (page 2 active), placard card, language dial top-right. Chips across the top. | Rail title: "चार पन्ने / एक idea"<br>Chips: "Draft content" · "Machine draft" · "Source: Desk playbook EV-2"<br>Dial: "हिंदी ⟷ English · 2 of 5 · हिंदी, terms English में" | VO: "KiKi turns his desk's playbook into lessons in Hindi." |
| TR-03 | 0:07–0:14 | Learn | Placard (red margin line, three punch holes, "STEP 2 OF 4", title, active **Listen** button with waveform). Term chips with the app's dotted red underline. Beside it, the dark plot panel shows an **example** (labelled "Example"; the lesson comes from the playbook, not from Ravi's trade): the IV line draws upward into a dashed event marker; on KiKi's second sentence it drops sharply after the marker while a small premium readout shrinks ₹90 → ₹60. Cue track below. | Placard text (see "Learn placard" below)<br>Chips: **IV · premium · IV crush · theta** | KiKi (Hindi TTS): "Event से पहले अनिश्चितता होती है, इसलिए IV बढ़ता है। Event के बाद IV गिरता है: यही IV crush है।"<br>Subtitle: "Before an event there's uncertainty, so IV rises. After it, IV falls: that's IV crush." |
| TR-04 | 0:14–0:20 | Reflect | Tutor screen (layout below). Canvas: candles D-1 and D0 with entry and strike lines and the event marker. Graph map: n1 already filled, n2 lights. Ravi's reply types in. A **dashed** misconception edge n2 → s1 lights (no red, no "wrong"). Canvas cross-fades to the payoff chart: ghost "before" curve, bright "after" curve sinking; a green arrow drops between them at spot 24,150; then the split label. Scripted turns 2 and 3. | KiKi: "Index 110 points ऊपर गया… फिर premium ₹90 से ₹60 क्यों?"<br>Ravi: "शायद operators ने खेल किया… stop hunt हुआ होगा।"<br>KiKi: "देखिए: spot वही, पर IV 17.5% → 11%।"<br>Canvas: "IV 17.5% → 11%" · "Move +₹40 · IV −₹48 · time −₹23" | VO: "Then they talk his trade through on a decision graph. No lecture: KiKi shows him." |
| TR-05 | 0:20–0:24 | Reflect | Canvas back to candles. A shaded band 23,736 to 24,344 over D0; the 24,150 close underlined inside it. Evidence chip pops in the conversation (green left border). Map: s1 → n3 lights. Turn 4. | KiKi: "24050 straddle ≈ ₹304। असल move कितना हुआ?"<br>Ravi: "±304 price था, आया सिर्फ़ 110। Option महँगा खरीदा।"<br>Canvas: "Priced move ≈ ±304" · "असल +110"<br>Chip: "Market sentiment · ok" | VO: "The market priced a 304-point move. It moved 110." |
| TR-06 | 0:24–0:30 | Reflect | Canvas: expiry payoff, flat max-loss line against a ₹10,000 budget marker. Then a quick second exchange: a reply that only cuts lots brings up a hint chip; the next reply lands. Canvas adds the spread's after-event curve beside Ravi's. Map: n4 → n5, a small hint tick on n5. Turns 5, 6 and 7. | KiKi: "Event budget ₹10,000। आपने कितना risk लिया?" · Ravi: "₹27,000, budget से लगभग तीन गुना।" · Chip "Risk and sizing · ok"<br>KiKi: "Playbook के हिसाब से setup?" · Ravi: "शायद 1 lot ही लेता।" · Chip "Hint 1 · playbook §4" · Ravi: "Defined-risk: 24200/24400 call spread, 2 lots, budget के अंदर।"<br>Canvas: "Max loss −₹27,075" · "Playbook setup −₹442.50 · आपका trade −₹9,210"<br>Chip: "Time to the right trade · partial (1 hint)" | VO: "Sizing, then the playbook's setup. One hint, and he gets there." |
| TR-07 | 0:30–0:34 | Reflect | Ravi's two lines appear in a journal card. Two evidence chips (yellow and red left borders). Map: n6 → c1 fills with a double ring; a small ink stamp "Conclusion". Turns 8 and 9. | KiKi: "अब desk के लिए एक-दो line में लिखिए।"<br>Ravi: "Direction सही था, पर market ±304 price कर रहा था और आया 110। IV crush और theta ने premium खा लिया; size budget का 2.7 गुना था। अगली बार: implied move, defined-risk, 1% budget।"<br>Chips: "Articulation · ok" · "Words · ok" | VO: "The conclusion is his, in his words." |
| TR-08 | 0:34–0:45 | Do | Generic dark trading terminal, **no product UI, no logos** (spec below), replaying D-1 15:25 in paper mode. KiKi's floating guidance window top-right. Three blue marks appear in order: circle on the 24050 CE and PE prices, underline on the 24200 CE IV cell, arrow from the 24050 row to the journal's "Implied move" field. Ravi's cursor types "±304", then "₹10,000 (1% of book)". The window's "What I can see" updates; KiKi asks one question. | Window: "KiKi · Stage 1 of 3 · Action 2 of 3 · Snapshot"<br>NOW: "24050 straddle से implied move निकालिए"<br>NEXT: "Event budget से max loss लिखिए"<br>WHAT I CAN SEE: "Implied move ✓ · Max loss ✓ · Exit plan: अभी नहीं"<br>Caption: "Paper mode · historical replay · KiKi never places orders" | VO: "Then he practises the fix on a replay of that afternoon. KiKi points; Ravi does the work."<br>KiKi (Hindi): "Exit plan अभी नहीं लिखा। आप कब निकलेंगे?" |
| TR-09 | 0:45–0:53 | Evidence | Learner scorecard page (Hindi labels, terms in English): four dimension bars in the four colours with filled, half-filled or outlined state; five tutor metrics below; a "Next" card. Then the organisation strip slides up (English, the desk's language): a stacked bar in the four colours and one line. | Bars: Concept ◐ partial · Words ● ok · Expression ● ok · Practice ◐ partial<br>Metrics: Market sentiment ● · Pattern पहचानना ◐ · Risk और sizing ● · सही trade तक का समय ◐ (1 hint) · बात साफ़ कहना ●<br>Next: "IV before events: एक और उदाहरण" · "Replay में pre-event note: exit plan"<br>Strip: "Desk view · Illustrative cohort · 20 trainees · Event-day options · Concept 11 · Words 3 · Expression 4 · Practice 2"<br>Line: **"11 of 20 trainees misread event-day IV: a concept gap, not a language gap."** | VO: "Ravi sees where his gap is. The desk sees it across the cohort, never his screens." |
| TR-10 | 0:53–0:58 | End | Off-white page, KiKi wordmark with its four-dot mark, three workspace chips with Trading outlined in ink. | **"Same KiKi. Different sector."**<br>Chips: "Engineering · Trading · Streaming"<br>Small: "Prototype · illustrative" | VO: "Same KiKi. Different sector." |

English VO is about 90 words; KiKi's Hindi audio is about 9 s in total.

## Learn placard (TR-03)

Placard kind `concept`, step 2 of 4, module "Event days", source tag EV-2. Hindi is a machine draft.

> **Event से पहले IV क्यों बढ़ता है**
> Scheduled event से पहले कोई नहीं जानता कि नतीजा क्या होगा। इस अनिश्चितता की कीमत option के **IV** में जुड़ जाती है, इसलिए **premium** महँगा हो जाता है। Event के बाद अनिश्चितता खत्म होती है और IV गिरता है: इसे **IV crush** कहते हैं। Weekly option में **theta** भी हर दिन premium घटाता है।

*EN gloss:* Before a scheduled event nobody knows the outcome. The price of that uncertainty goes into the option's IV, so the premium gets expensive. After the event the uncertainty is gone and IV falls: that's IV crush. In a weekly option, theta also takes premium every day.

**Cue track** ([contract §2](../../05-contracts-v0.md#2-cue-track-shared-by-the-ece-sync-and-pack-lessons) shape; `ex-iv-line` is a generic `line` scene the factory would fill with example values; times are estimates until per-sentence TTS gives exact ones):

```json
[
  { "t": 0.0, "sentence": 0, "scene": { "id": "ex-iv-line", "state": "into-event", "highlight": ["iv"] } },
  { "t": 1.8, "scene": { "highlight": ["mk-event"] } },
  { "t": 3.1, "sentence": 1, "scene": { "state": "after-event", "annotate": [
    { "id": "a-crush", "kind": "label", "target": "mk-event", "text": { "en": "IV crush", "hi": "IV crush" }, "dim": "concept" } ] } }
]
```

For the video, the example line can borrow the shape of `ivSeries.byBar` in scenario.json (17.1% → 17.5% across D-1, 19.2% just before the 10:00 announcement, 12.5% straight after, 11.0% by the close), labelled "Example".

## Tutor screen layout (TR-04 to TR-07)

- 12-column grid at 1920 × 1080, 96 px outer margins.
- **Canvas**, columns 1–7: dark plot panel `#131914`, grid `#354638`, labels `#d4e5d6`. Candles: up = hollow body, down = filled body, both `#d4e5d6` (dimension colours are kept for marks). Lines and the "after" payoff curve: `#79df95`. The "before" payoff curve is a 50% ghost of `#d4e5d6`. Annotation marks use the dimension colour (concept green `#34a853` in Reflect).
- **Conversation**, columns 8–12: white paper card, 2 px ink border, 4 px hard shadow. KiKi's lines are short, set in ink with the four-dot mark; Ravi's replies right-aligned in a light surface bubble `#f6f7f2`. Evidence chips are small pills with a 5 px left border in the metric's dimension colour, like the app's feedback cards.
- **Decision-graph map**, bottom of the conversation card (about 300 × 110 px): 8 nodes at the positions in `meta.mapLayout`. Probe = circle, show = square, conclusion = double ring. Visited = ink fill; current = ink fill with a 6 px pulsing ring; misconception edge = dashed ink with a tiny "misconception" label; hint used = small tick on the node.
- Case card collapsed to one line at the top of the conversation card, with the disclaimer.

## Do screen (TR-08): generic terminal

- Dark neutral UI (`#16181b` background, `#2a2e33` rules, `#e6e6e6` text), invented layout, **no product name, logo or real broker UI**. Top bar: "INDEX (illustrative) · Paper mode · Historical replay · D-1 15:25".
- Left 55%: 30-minute candles for D-1 with a dashed "Policy · D0 10:00" marker ahead of the last bar.
- Right 45%: option chain, strikes 23950–24350 visible, columns `OI | IV | LTP || Strike || LTP | IV | OI`, ATM row 24050 shaded. Values from `optionChainSnapshot` (e.g. 24050: CE ₹153.55, PE ₹150.75; 24200 CE ₹90.25 at IV 17.5%, call OI 1,12,600).
- Bottom right: Ravi's "Pre-trade note" panel with fields Thesis · IV · Implied move · Max loss · Exit plan.
- KiKi's floating window copies the real app's lab window: dark `#1f1f1f` rounded panel, four-dot mark, "Current step" pill, NOW in large white text, NEXT, "WHAT I CAN SEE · Checked 2 s ago", buttons "Pause guidance" and "Open tracker". Its status reads **"Snapshot · looked when you asked"**, not "reading screen": in the build, lab-lite is an annotated snapshot, not a live overlay ([04 §8](../../04-judge-story.md#8-honesty-boundaries-non-negotiable-on-stage)). KiKi's own window is the only KiKi UI on this screen.
- Marks are practice blue `#4285f4`, 3 px, drawn on with a 250 ms stroke. KiKi never moves the cursor; Ravi does.

## Build notes

- 1920 × 1080, 30 fps, 58 s. Cuts on beats; inside a shot, use 200–300 ms ease-out moves only. Respect reduced motion in any interactive version.
- Type: Space Grotesk for Latin text (the app's font) and Noto Sans Devanagari for Hindi. Ink `#111`, paper `#fff`, muted `#555a53`, rule `#d9ded6`.
- Dimension colours: concept `#34a853`, words `#ea4335`, expression `#fbbc05`, practice `#4285f4`. They mark skills only. **P&L is never red or green**: show the sign and the number in ink.
- All numbers come from scenario.json and tutor-flow.json; don't retype them by hand.
- Audio: the English VO by a neutral voice; KiKi's lines from the same Hindi TTS voice the pack uses. No music under KiKi's Hindi lines.

## Click-through variant

The same `scriptedPath` can drive a click-through in the real tutor UI: each click advances one turn, applies `canvasCue` and lights `graphMap`. Turns with `video.show: false` (turn 1) still play in the click-through, which runs about 90 seconds.

## Check before recording

- A native Hindi speaker reviews every Hindi line on screen and in audio.
- A practising trader confirms the scenario looks plausible (see the questions in [persona.md](persona.md)).
- The disclaimer is visible on every trade frame; nothing on screen reads as a recommendation.
