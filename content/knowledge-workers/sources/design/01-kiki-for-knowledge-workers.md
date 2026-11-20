# KiKi for knowledge workers

v0.2 · 20 Nov 2026 · Status: **Proposed**, for the team to confirm (D4 agreed) · Event: Google Startup Buildathon, 24-hour build (09:00 Fri → 09:00 Sat IST)

This widens KiKi from a bilingual learning app for Odia-medium engineering students into an **active multilingual learning companion for knowledge workers**, sold to organisations. It keeps what made KiKi distinct. It changes who KiKi serves, whose knowledge it teaches, and who pays.

Read with: [02 build plan](02-build-plan-24h.md) · [03 clarity map](03-clarity-map.md) · [04 judge story](04-judge-story.md) · [MISSION](MISSION.md)

## 1. The one-paragraph version

People starting a new role, or moving into a different one, lose performance to two things that are not ability: **the language the work happens in**, and **the knowledge the organisation never wrote down**. KiKi turns an organisation's own material into short lessons in the language each person thinks in. It coaches them inside the real tools they work in, and talks problems through with them until their reasoning is clear. It measures four things separately: understanding, the domain's words, explaining it to peers, and doing it in the real tool. A manager can then see where each person's gap actually is.

## 2. Why KiKi existed, and what carries over

KiKi started from one observation: an Odia-medium student who understands a circuit can still lose marks because the question and the answer are in English. The design answered with a small set of ideas. Every one of them carries over to knowledge work.

| Original idea (Oct 2026) | What it meant for the student | What it means for a knowledge worker |
|---|---|---|
| Marks lost to language, not intelligence | Correct understanding hidden by English exams | Performance lost to the working language and the trade's jargon, not ability |
| Language as scaffolding; English terms stay stable | Odia explanation, English term chips | Explain in the person's language. The trade's canonical terms (theta, IV, CCV, retention) stay as they are |
| Four separate mastery dimensions | Concept, words, academic English, practical | Concept, words, **expression** (explain it to peers), **practice** (do it in the real tool) |
| Diagnosis drives the next step | Concept gap → prerequisite; language gap → words | Same, plus gap patterns across an onboarding cohort |
| Theory to practice in the real tool | MATLAB/Simulink lab with live checks | The person's real work tool: a trading terminal, a streaming dashboard |
| The student's own material comes first | Notes and syllabus | **The organisation's tribal knowledge comes first**: playbooks, SOPs, recorded reviews |
| Kiki acts, not chats; the hint ladder | Points, highlights, asks short questions | Same. Tutor mode is structured dialogue on a decision graph, not open chat |
| Adaptive fade-out | Less Odia, fewer hints as mastery grows | Same. The goal is independence, not permanent support |
| Honest evidence | Rings fill only on evidence | Same, and the organisation gets evidence instead of completion rates |
| Two agents: Learning Orchestrator and Practical Copilot (architecture doc, 9 Oct) | Picks the next lesson action; guides the lab | **Tutor mode** is the orchestrator on a decision graph. **Lab mode** is the copilot |

The widening is not a pivot. The architecture was always two agents over a content compiler, and the data model was always subject-agnostic (`data-model/subject-profiles.json`: "Add a subject by adding a profile; no code changes"). The seven backend directions of 12 October already specified most of the new ledger:

| New ledger item | Already specified as |
|---|---|
| Tribal knowledge builder: modularise, multilingual, canvas factory | Prototype 1 (grounded lesson compiler), 2 (mixed-language speech), 3 (graphics engine) |
| Canvas in sync with narration | Prototype 4 (annotated teaching canvas: `LessonTimeline`, audio clock as master) |
| Tutor mode: state-aware agent on a decision graph | Prototype 5 (learner graph + `learning-policy` returning typed actions), 6 (diagnostic assessment) |
| Lab mode: screen reading, writing and annotation | Prototype 7 (live screen annotation: `ScreenObservation`, `ScreenAnchor`, expiring `GuidanceCue`) |

Source: `docs/prototypes/backend-prototype-directions.md`, `AI_Builder_Cup_Technical_Architecture.docx`.

## 3. The promise

**For the person:** Learn the job in the language you think in. Practise it in the tools you use. Talk it through until it's clear.

**For the organisation:** Turn what your best people know into onboarding everyone can follow, in their own language. See exactly where each person's gap is.

**What "active" means:** the person does the work. They build the model, read the chart, run the stream review, and reach the conclusion. KiKi explains, points, asks and checks. That is the difference from a video course or a chatbot.

## 4. Principles

### Kept as they are

1. **Language is scaffolding, not a replacement.** Canonical terms keep their form in every language.
2. **Four dimensions, separate evidence.** A strong explanation in Hindi with a weak English one keeps the concept credit.
3. **Diagnosis drives the next step.**
4. **KiKi acts more than it chats.** Short questions, visuals and pointing, not long paragraphs.
5. **The hint ladder:** question, nudge, worked step, then the answer. Each rung used is evidence.
6. **The learner controls the language dial.** KiKi may suggest; it never moves it.
7. **Honest evidence.** Nothing fills, lights up or celebrates without evidence. "Not yet", never "wrong".
8. **Every feature is a template.** Each domain is a worked example.

### Extended

- **Source of truth.** The organisation's material comes first. Generated content carries a review state (draft, reviewed, published) and a source tag.
- **Language.** Any language the pipeline supports, not only Odia. A language counts as supported only after a native speaker has reviewed it. Until then it is labelled a machine draft.

### New

- **The user drives; KiKi nudges.** In lab mode KiKi never clicks, trades, streams or edits for the user.
- **Process, not picks.** In high-stakes domains such as trading, KiKi reviews the decision process on past or paper trades. It never recommends a live trade.
- **Conclusions are earned in conversation.** In tutor mode KiKi asks and shows; the user reasons. The decision graph keeps the conversation on the organisation's playbook and makes every conclusion traceable.
- **Domains are data.** A new domain is a domain pack (profile, modules, tutor graphs, lab tasks), not new code.
- **The organisation sees gaps, not screens.** Managers see dimension-level evidence. Screen captures and conversations stay private to the learner by default.

## 5. The four dimensions for knowledge workers

The colours and data-model keys stay. Only the labels and examples widen. In the current data model the keys are `concept`, `words`, `english` and `lab`. Keep the keys for now and change the display labels. Rename the keys after the buildathon.

| Colour | Key | Student meaning | Knowledge-worker meaning | ECE student | F&O trader | Streamer |
|---|---|---|---|---|---|---|
| Green | `concept` | I understand it | I understand the idea behind the work | Why carrier phase error shrinks the recovered message | Why option premium can fall even when direction was right | Why viewers leave when a stream loses its hook |
| Red | `words` | I know what it's called | I know the trade's words | Carrier, sideband, coherent detection | Theta, vega, IV, OI, PCR | CCV, retention, raid, VOD |
| Yellow | `english` → label **Expression** | I can explain it in English | I can explain it clearly to peers in the team's working language | Explains the result in a viva | Writes a trade rationale the desk accepts | Pitches the next stream plan to the agency |
| Blue | `lab` → label **Practice** | I can make it work | I can do it in the real tool | Builds the DSB-SC model in Simulink | Reads the option chain and sets risk in the terminal | Reads the analytics dashboard and restructures segments |

**What the user called "clarity of thought and intent"** is not a fifth dimension. It is what tutor mode produces: a conclusion the person reached and can explain. It shows up as concept evidence (the reasoning was sound) and expression evidence (they could say it clearly).

## 6. Three modes, one loop

```text
  Organisation's material ──► Tribal knowledge builder ──► Domain pack
                                                              │
        ┌─────────────────────────────────────────────────────┘
        ▼
     LEARN  ──────►  DO  ──────►  REFLECT  ──────►  EVIDENCE  ──► next step
   lesson with     lab mode in     tutor mode on     four dimensions,
   synced canvas   the real tool   a decision graph  learner + cohort view
```

| Mode | The user's question | What KiKi does | User outcome it serves | What the organisation gets |
|---|---|---|---|---|
| **Learn** (content from the tribal knowledge builder) | "What is this, in words I follow?" | Short placards in the dial language, terms kept, narration with the canvas moving in step | Understanding | Its playbook taught in every language, consistently |
| **Do** (lab mode) | "Am I doing this right, in my actual tool?" | Reads the shared screen, checks visible work, points or annotates, waits for the user to act | *Get better at a specific skill* | Practice evidence from real work |
| **Reflect** (tutor mode) | "Why did this go wrong, and what would I do differently?" | Walks a decision graph with the user, asks, shows visuals on the canvas, reaches a conclusion with them | *Clarity of thought and intent*, and *sharing ideas with peers* | Reasoning and expression evidence, aligned to the playbook |

Every mode writes evidence to the same four dimensions. That shared evidence model is what makes three modes one product rather than three features.

## 7. Three personas: laws, odds, audiences

The personas were chosen to sample three different *kinds* of knowledge work, not three markets.

**For the buildathon (Arpan, 20 Nov):** the student route is the working, deep build. The trader and streamer are visual prototypes, mainly short videos. They show that the same formats and modes re-target to other sectors while staying deep and personalised for each. The table describes the product vision for all three.

- **Laws:** knowledge that is formal and verifiable. There is a right answer and a formula.
- **Odds:** knowledge that is probabilistic. A good decision can lose money; a bad one can win.
- **Audiences:** knowledge that is social and creative. The feedback is real-time and comes from people.

If one engine can coach all three, it can coach most knowledge work between them.

| | ECE student (built) | F&O trader (new) | Twitch streamer, GTA 6 content (new) |
|---|---|---|---|
| Name | Bikash | *placeholder:* Ravi | *placeholder:* Meera |
| Kind of knowledge | Laws | Odds | Audiences |
| Transition | College to first engineering job; regional medium to English medium | Retail or junior desk trader to disciplined process | Hobby streamer to signed creator; switching to a launch title |
| Language (proposed) | Odia | Hindi, with English market terms (how Indian traders already talk) | To decide: Hindi, or a third script such as Tamil if a reviewer exists |
| Real tool for lab mode | MATLAB/Simulink Online (built) | Chart and option chain on a trading terminal (paper or historical) | Stream analytics dashboard; OBS scenes |
| Tutor problem | A medium-difficulty question, e.g. recovered amplitude at 60° phase error | "Why was this a bad call?" | "Why did engagement fall at minute 40?" |
| Tutor metrics (from the brief) | Conceptual understanding, calculation accuracy | Market sentiment, analysis and pattern recognition, time to the right trade | Engagement diagnosis, content structure, audience reading |
| Canvas visuals | Phase-recovery scope (built), waveforms | Candles with event marker, payoff diagram before and after, IV line | Viewer and retention curve with segments, chat activity |
| Organisation that pays (hypothesis) | Employers hiring regional-medium engineers; college placement cells | Prop desks and trading academies onboarding traders; brokers' investor-education programmes | Creator agencies, esports organisations, platform creator programmes |
| What only this persona proves | Correctness, and guidance in a real professional tool | Reasoning coaching where the outcome is probabilistic and money is at stake, without giving advice | Coaching for creative work against live metrics; the buildathon theme's home ground |

**Sectors the three corners stand for**

| Corner | Sectors it generalises to |
|---|---|
| Laws | Engineering, manufacturing, field service, clinical procedures, compliance |
| Odds | Finance, insurance, sales forecasting, operations, risk |
| Audiences | Media, marketing, sales, customer success, design, community |

## 8. B2B positioning (hypotheses, not findings)

None of this has been tested with a buyer yet. Treat every row as a hypothesis with the evidence that would confirm it.

**Who buys.** The owner of onboarding or L&D in organisations that hire people from many language backgrounds into tool-heavy roles.

**When they buy.** At two moments where a skill gap is visible and expensive:
1. **Onboarding:** the first 90 days in a role.
2. **Transitions:** a role change, a new tool, a new product line, a regulatory change.

**What they buy.**
1. **The tribal knowledge builder:** their playbooks, SOPs and recorded reviews compiled into modules in every language their people use, with a review step.
2. **Learner seats:** Learn, Do and Reflect for each new joiner.
3. **Gap analytics:** a cohort view of where each person's gap sits (concept, words, expression or practice), per skill.

**Why now.** Gemini makes multilingual generation, speech and screen understanding cheap enough to run per person. Most organisations' training content exists only in English. India's workforce does not work only in English.

**Pricing hypothesis.** Per seat per month during onboarding, plus a one-off setup fee per domain pack. Model cost per session can be estimated from token use. The October plan's assumption put one ten-minute lab session at about US$0.32 of screen analysis; tutor sessions should cost cents. Measure both during the build.

**Beachhead options**

| Option | Pain | Language gap central? | Budget | KiKi fit | Evidence needed |
|---|---|---|---|---|---|
| Employers hiring regional-medium engineers (electronics, semiconductor, telecom) | Long ramp to productivity on tool-heavy work | Yes | L&D budgets exist | Lab mode on real tools is the differentiator | 3 conversations with L&D or plant HR heads |
| Brokers' investor education (B2B2C) | Regulator pressure on retail losses; most users outside English-first metros | Yes | Large user bases | Tutor mode post-trade reviews, no advice | 1 conversation with a broker's education or compliance team |
| Prop desks and trading academies | Juniors lose desk capital while learning | Partly | Moderate | Tutor + lab on paper trades | 2 conversations |
| Creator agencies and esports organisations | Roster growth and retention | Partly (Hindi and regional streaming) | Smaller, fragmented | Lab-lite on analytics + tutor | 2 conversations |
| Colleges (placement, regional-medium transition) | Placement outcomes | Yes | Low, slow | Existing ECE depth | Existing pilot plan in the UX doc |

**The likely judge question: "Who pays for the streamer?"** Answer honestly: creator agencies and esports organisations onboarding talent. Say plainly that the streamer persona is the proof of generality and the theme fit, not the first market.

**Competitive frame (to verify before saying it on stage).** Learning platforms deliver content and track completion. AI tutors and chatbots answer questions in open chat. Digital adoption platforms guide clicks inside specific enterprise apps using authored flows. KiKi's claimed position is the intersection: multilingual learning, plus a copilot that reads any real tool visually, plus a reasoning coach, plus evidence split four ways. Do not claim a named competitor lacks a feature without a current check.

## 9. What KiKi will not do

- Give live trading recommendations or signals, or place orders.
- Take control of the user's tools.
- Claim mastery without evidence, or fill a ring to make someone feel good.
- Show managers raw screens or conversation transcripts by default.
- Call a language supported before native review. Unreviewed output is labelled as a machine draft.
- Use a game publisher's logos or artwork. The streamer persona refers to the game by name only.

## 10. Decisions for the team

| # | Decision | Recommendation | Status |
|---|---|---|---|
| D1 | Positioning line | "Active multilingual learning companion for knowledge workers" for the pitch; the one-paragraph version above for the product page | Proposed |
| D2 | Dimension labels | Keep colours and keys; relabel `english` as Expression and `lab` as Practice in the UI | Proposed |
| D3 | Persona languages | ECE in Odia and English (built); trader in Hindi and streamer in Hinglish in the prototype videos, labelled machine draft | Proposed |
| D4 | What gets built for real | The student route, deep: narration-synced canvas, tutor mode, a builder slice, an organisation view. The trader and streamer are visual prototypes (videos) in the same formats and look | **Agreed** (Arpan, 20 Nov) |
| D5 | Beachhead to name on stage | Pick one after the GTM session reports; keep the other personas as proofs of generality | Open |
| D6 | Trading compliance line | "Process, not picks": past and paper trades only, no recommendations | Proposed |
| D7 | Persona names | Ravi and Meera are placeholders | Open |
