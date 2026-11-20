# Storyboard: "Meera, minute 40" (58 s breadth prototype)

Draft v0.1 · 20 Nov 2026 · Prototype · illustrative · For a motion designer or a HyperFrames build · Data: [scenario.json](scenario.json) · Turns: [tutor-flow.json](tutor-flow.json) `scriptedPath`

**What the video must prove in under a minute:** the same KiKi engine runs the full loop (Learn → Do → Reflect → Evidence) for a creator, in Hinglish, on her own stream, with no answer key. Order chosen for the story: Do before Reflect, because Meera first looks at her dashboard and asks why; the conversation follows from KiKi's question (the lab-lite hand-off in [contract §5](../../05-contracts-v0.md#5-lab-lite)).

**Persistent on every frame**
- Bottom-left, 14 px, muted ink `#555a53` at 70%: **Prototype · illustrative**
- Beside every block of Hinglish: a small outlined chip **Machine draft · native review pending**
- English subtitles under every Hinglish line, for jurors
- **IP:** GTA 6 appears as text only. No publisher logos, key art, characters, game footage or screenshots anywhere, including thumbnails. Every chart is ours.

On-screen KiKi lines in ST-05 to ST-09 are shortened for reading time. The full scripted lines, routes, canvas cues and evidence are in `scriptedPath` (turn → shot mapping in each turn's `video` field).

## Shot list

| # | Time | Mode | On screen (what to build) | On-screen text | Narration |
|---|---|---|---|---|---|
| ST-01 | 0:00–0:04 | Case | Off-white desk `#f6f7f2`. A white sketchbook stream card (2 px ink border, 4 px hard shadow) slides up. Right: a small dark plot panel with our own CCV sparkline for the 3 hours; the dip after 40:00 pulses once. No game imagery. | Header: "LAUNCH WEEK · DAY 2 · 3:00:00 · 20:00 IST"<br>Rows: "GTA 6 · Hinglish stream" · "Peak 682 CCV · Avg 509 · Target 550"<br>Headline: **"Minute 40 pe viewers kahan gaye?"** (EN: "Where did the viewers go at minute 40?")<br>Small: "GTA 6 is named only. Charts are our own." | VO (EN): "Meera lost 37% of her viewers after minute 40." |
| ST-02 | 0:04–0:07 | Learn | Push into a KiKi lesson page laid out like the real app's lesson screen: left rail of four numbered pages (page 2 active), placard card, language dial top-right. Chips across the top. | Rail title: "Chaar pages / ek idea"<br>Chips: "Draft content" · "Machine draft" · "Source: Agency playbook LW-3"<br>Dial: "Hinglish ⟷ English · 2 of 5 · Hinglish, terms English mein" | VO: "KiKi turns her agency's playbook into lessons in Hinglish." |
| ST-03 | 0:07–0:14 | Learn | Placard (red margin line, three punch holes, "STEP 2 OF 4", title, active **Listen** button with waveform). Term chips with the app's dotted red underline. Beside it, the dark plot panel shows an **example** stream (labelled "Example", not Meera's data): three bands "Mission", "Silent segment", "Chat poll". In step with the narration, the chat line dips first, the CCV line follows, then both climb in the poll band. Cue track below. | Placard text (see "Learn placard" below)<br>Chips: **CCV · chat rate · hook · retention** | KiKi (Hinglish TTS): "Segment mein goal ya chat loop nahi, toh pehle chat girta hai, phir CCV. Har 10–15 minute mein naya hook do."<br>Subtitle: "No goal or chat loop in a segment? Chat falls first, then CCV. Renew the hook every 10–15 minutes." |
| ST-04 | 0:14–0:24 | Do | Meera's stream analytics dashboard: generic and **unbranded** (spec below). Her cursor; she types into KiKi's ask box. KiKi's floating window appears top-right. Three blue marks draw on in order: circle on the CCV dip at 40:00; arrow from the low chat bars (40–60) to the dip; box around "38:00 Segment change" in the events list. NOW asks her to select a range; **her** cursor drags 38:00 to 60:00. The window's "What I can see" updates, and KiKi asks one question that hands off to Reflect. | Meera: "KiKi, yahan viewers kyun gire?"<br>Window: "KiKi · Snapshot · looked when you asked"<br>NOW: "38:00 se 60:00 tak range select karo"<br>NEXT: "Isi range ka chat rate dekho"<br>WHAT I CAN SEE: "CCV 556 → 348 (38:00–59:00) · Chat 87 → 15/min"<br>KiKi: "Drop se just pehle stream pe kya badla tha?" | VO: "On her own dashboard, KiKi marks the drop and the chat lull. Meera does the selecting; KiKi never touches her stream." |
| ST-05 | 0:24–0:28 | Reflect | Tutor screen (layout below). Canvas: CCV line 25:00–70:00 with the drop circled at 40:00. Graph map: n1 lights. Evidence chip pops (green left border). Turn 1. | KiKi: "40:00 ke just baad CCV girna shuru hota hai. Us waqt stream pe kya chal raha tha?"<br>Meera: "38 pe mission khatam karke cash grind shuru kiya tha… shayad wahi?"<br>Chip: "Engagement diagnosis · ok" | VO: "Then a short conversation, on a decision graph." |
| ST-06 | 0:28–0:32 | Reflect | Canvas: the chat line joins the CCV line, focus 30:00–50:00; a green arrow traces chat falling 87 → 15. Map: n2 lights. Turn 2. | KiKi: "Pehle kya gira: chat ya CCV?"<br>Meera: "Arre, chat toh 38 se hi dead ho gaya tha. CCV baad mein gira."<br>Canvas: "Chat 87 → 15/min"<br>Chip: "Audience ko padhna · ok" | VO: "She spots that chat fell first." |
| ST-07 | 0:32–0:38 | Reflect | Canvas: mission and grind bands labelled with chat rates. Meera overcorrects; a **dashed** misconception edge n3 → s2 lights (no red, no "wrong"). Canvas widens to 30:00–95:00 and boxes both mission-free segments side by side with their retention. Turns 3 and 4. | KiKi: "Grind segment mein kya missing tha jo mission mein tha?"<br>Meera: "Matlab grind content hi boring hai. Next time grind hi nahi karungi."<br>KiKi: "Dono mein mission nahi tha. Doosre mein chat polls the, aur CCV 351 se 477 pe pahuncha. Game same, structure alag."<br>Canvas: "Chat 86/min" · "Chat 18/min" · "Retention 0.63" · "Retention 1.36" | VO: "When she overcorrects, KiKi shows her the segment that worked." |
| ST-08 | 0:38–0:42 | Reflect | Canvas: the label on the grind band changes from "Next stream: ?" to her plan. Map: n4 lights. Turn 5. | KiKi: "Next stream ke liye ek change, aur kaise pata chalega ki kaam kiya?"<br>Meera: "Grind max 10 min, pehle goal bolungi, har 5 min ek poll. Chat 40/min se upar aur CCV drop 10% se kam, toh kaam kiya."<br>Canvas: "Next: ≤10 min · goal · poll har 5 min"<br>Chip: "Next stream ka experiment · ok" | VO: "One change, one measure." |
| ST-09 | 0:42–0:46 | Reflect | Her two lines appear in a "Pitch to agency" card. Two chips (yellow and red left borders). Map: n5 → c1 fills with a double ring; a small ink stamp "Conclusion". Turns 6 and 7. | KiKi: "Agency manager ke paas 30 second hain. Do line mein pitch karo."<br>Meera: "Mission ke baad 22 min ka silent grind: chat pehle gira, phir CCV 37%, segment retention 0.63. Next stream: grind 10 min, goal + har 5 min poll; target chat 40+/min, CCV drop 10% se kam."<br>Chips: "Apni baat clear bolna · ok" · "Words · ok" | VO: "And a pitch her manager can act on." |
| ST-10 | 0:46–0:53 | Evidence | Learner scorecard page (Hinglish labels, terms in English): four dimension bars in the four colours, filled or half-filled; five tutor metrics; a "Next" card. Then the organisation strip slides up (English, the agency's language): a stacked bar in the four colours and one line. | Bars: Concept ◐ partial · Words ● ok · Expression ● ok · Practice ● ok<br>Metrics: Engagement diagnosis ● · Audience ko padhna ● · Content structure ◐ · Next stream ka experiment ● · Apni baat clear bolna ●<br>Next: "Segment design: ek aur contrast" · "Kal ka run-of-show: grind ≤10 min + poll"<br>Strip: "Agency view · Illustrative cohort · 18 new creators · Reading your analytics · Concept 5 · Words 2 · Expression 4 · Practice 7"<br>Line: **"7 of 18 new creators can explain retention but don't yet act on it in the dashboard: a practice gap."** | VO: "Meera sees where her gap is. The agency sees the pattern across new creators, never her screens." |
| ST-11 | 0:53–0:58 | End | Off-white page, KiKi wordmark with its four-dot mark, three workspace chips with Streaming outlined in ink. | **"Same KiKi. Different sector."**<br>Chips: "Engineering · Trading · Streaming"<br>Small: "Prototype · illustrative · GTA 6 named only; no publisher assets" | VO: "Same KiKi. Different sector." |

English VO is about 95 words; KiKi's Hinglish audio is about 9 s in total.

## Learn placard (ST-03)

Placard kind `concept`, step 2 of 4, module "Launch-week streams", source tags LW-3 and LW-4. Hinglish is a machine draft.

> **Har segment ko ek hook chahiye**
> Launch week mein bahut saare naye viewers browse karte hue aate hain. Agar segment mein koi goal, koi stake ya **chat loop** nahi hai, toh pehle **chat rate** girta hai, phir **CCV**. Har 10–15 minute mein naya **hook** do: ek goal bolo, ek poll chalao, chat ko andar lao. Segment ki **retention** batati hai ki usne viewers ko roka ya nahi.

*EN gloss:* In launch week lots of new viewers arrive while browsing. If a segment has no goal, no stakes and no chat loop, chat rate falls first, then CCV. Renew the hook every 10–15 minutes: say a goal, run a poll, bring chat in. A segment's retention tells you whether it held viewers.

**Cue track** ([contract §2](../../05-contracts-v0.md#2-cue-track-shared-by-the-ece-sync-and-pack-lessons) shape; `ex-hook-line` is a generic `line` scene the factory would fill with example values; times are estimates until per-sentence TTS gives exact ones):

```json
[
  { "t": 0.0, "sentence": 0, "scene": { "id": "ex-hook-line", "state": "mission" } },
  { "t": 1.5, "scene": { "state": "silent", "highlight": ["chat"] } },
  { "t": 2.7, "scene": { "highlight": ["ccv"] } },
  { "t": 3.6, "sentence": 1, "scene": { "state": "hook-back", "annotate": [
    { "id": "a-hook", "kind": "label", "target": "band-poll", "text": { "en": "New hook", "hi-Latn": "Naya hook" }, "dim": "concept" } ] } }
]
```

## Do screen (ST-04): generic analytics dashboard

- Light neutral UI (`#fafafa` background, `#e3e3e3` rules, `#1d1d1f` text), invented layout. **No platform name, logo or real dashboard UI**, and no stream preview or game thumbnail.
- Header: "Stream summary · Launch week Day 2 · 3:00:00".
- KPI tiles: Peak CCV **682** · Avg CCV **509** · Follows **87** · Chat messages **14,165** · Hours watched **1,526**.
- Main chart: CCV per minute over 3 hours (`series.ccv`), a mid-grey line, with thin segment ticks along the top: Mission 12:00 · Grind 38:00 · Polls 60:00 · Collab 92:00 · Wind-down 150:00.
- Below it: chat messages per 5 minutes as bars (`per5min.chatTotal`): about 400–500 per bucket in the mission, 70–80 from 40:00 to 60:00, back to 400–530 from 60:00.
- Right column, events list: 12:00 Mission starts · 38:00 Segment change · 62:00 Poll 1 · 75:00 Poll 2 · 95:00 Raid in · 140 · 179:00 Raid out.
- KiKi's floating window copies the real app's lab window (dark `#1f1f1f` rounded panel, four-dot mark, "Current step" pill, NOW in large white text, NEXT, "WHAT I CAN SEE", buttons "Pause guidance" and "Open tracker"), but its status reads **"Snapshot · looked when you asked"**: in the build, lab-lite is an annotated snapshot, not a live overlay ([04 §8](../../04-judge-story.md#8-honesty-boundaries-non-negotiable-on-stage)).
- Marks are practice blue `#4285f4`, 3 px, drawn on with a 250 ms stroke. Meera's cursor makes the range selection; KiKi never moves it.

## Tutor screen layout (ST-05 to ST-09)

- Same layout as the trader video: canvas in columns 1–7 on the dark plot panel (`#131914`, grid `#354638`, labels `#d4e5d6`), conversation card in columns 8–12, decision-graph map at the bottom of the conversation card using `meta.mapLayout`.
- CCV line `#79df95`; chat line `#d4e5d6` dashed; segment bands as 8% white fills with labels at the top; the highlighted band at 16%. Annotation marks in concept green `#34a853`.
- Graph map: probe = circle, show = square, conclusion = double ring; visited = ink fill; current = ink fill with a pulsing ring; misconception edge dashed.

## Build notes

- 1920 × 1080, 30 fps, 58 s. Cuts on beats; inside a shot, 200–300 ms ease-out moves only.
- Type: Space Grotesk (the app's font). Hinglish is Latin script, so no second font is needed. Ink `#111`, paper `#fff`, muted `#555a53`, rule `#d9ded6`.
- Dimension colours mark skills only: concept `#34a853`, words `#ea4335`, expression `#fbbc05`, practice `#4285f4`. A drop in viewers is never shown in red.
- All numbers come from scenario.json and tutor-flow.json; don't retype them by hand.
- Audio: the same neutral English VO voice as the trader video; KiKi's lines from the Hinglish TTS voice the pack uses.

## Click-through variant

The same `scriptedPath` can drive a click-through in the real tutor UI: each click advances one turn, applies `canvasCue` and lights `graphMap`. The full path runs about 70 seconds.

## Check before recording

- A native Hinglish speaker, ideally a streamer, reviews every Hinglish line on screen and in audio.
- A practising streamer confirms the stream shape looks plausible (see the questions in [persona.md](persona.md)).
- No frame contains game footage, logos, key art, characters or a real platform's UI.
