# Ravi: F&O trader persona

Draft v0.1 · 20 Nov 2026 · Prototype · illustrative · Owner: S5 (persona studio)

> **Placeholder persona.** Ravi is not a real person, user or testimonial (decision D7 is still open). The desk, its playbook and the trade are invented for the breadth prototype. Hindi text in this folder is a **machine draft that needs native review**, and the trading content needs a practising trader's review.

Files in this folder: [playbook excerpt](playbook-excerpt.md) · [scenario.json](scenario.json) · [tutor-flow.json](tutor-flow.json) · [storyboard](storyboard.md)

## Persona card

| | |
|---|---|
| **Name** | Ravi (placeholder) |
| **Kind of knowledge** | Odds: a good decision can lose money and a bad one can win, so the outcome is not the answer |
| **Role** | Trainee index-options trader, week 2 of a 12-week onboarding. Trades a ₹10,00,000 paper book before the desk gives him a live limit |
| **Background** | B.Com from Indore. Two years of self-taught retail F&O trading on his own account, mostly buying weekly options. Learned from Hindi videos and Telegram groups |
| **Organisation that pays** | An illustrative proprietary trading desk in Mumbai. Its head of training buys KiKi seats for each trainee intake, plus one domain pack built from the desk's own *Options desk playbook: event days*. The same pack could be licensed by a broker's investor-education programme (B2B2C) that reviews customers' past trades, never live ones |
| **Transition** | Retail habits to desk process: from buying cheap options on a hunch, sizing by conviction and keeping no journal, to event budgets, defined risk, pre-trade notes and process reviews. Also from learning in Hindi to working on a desk where the playbook, risk reports and morning meeting are in English |
| **Language** | Hindi in Devanagari for explanations. English market terms stay as they are: IV, theta, vega, premium, strike, OI, PCR, straddle, lot. Dial: *Hindi + English terms* (2 of 5) |
| **Real tool** | A trading terminal's chart and option chain, in paper mode or historical replay. The prototype draws a **generic, unbranded** terminal |
| **KiKi modes he uses** | Learn (desk playbook lessons), Reflect ("Why was this a bad call?"), Do (pre-event note on a terminal replay) |

**In his words** (illustrative; Hindi is a machine draft):
"Direction तो सही था, फिर पैसे कहाँ गए?"
*"My direction was right, so where did the money go?"*

## Goals

1. Pass the desk's gate from the paper book to a live limit. The gate (illustrative): four weeks of rule-compliant trades, each with a complete journal entry.
2. Explain a trade in the morning meeting without freezing, in the desk's English.
3. Stop losing on event days when his call on direction is right.

## Pains

- He can't see why a right call lost money. "Greeks" feel like formulas, not intuition.
- The playbook and the risk reports are long and in English. He reads the terms fluently but reasons best in Hindi.
- What the seniors know lives in their heads and in quick desk chat, not in the playbook.
- Desk reviews feel like a verdict on P&L, not a review of his process.
- Old habits: tips from Telegram groups, buying options because they are "cheap", sizing by how sure he feels.

## The four dimensions for Ravi

Colours and data keys follow [01 §5](../../01-kiki-for-knowledge-workers.md#5-the-four-dimensions-for-knowledge-workers). Colours mark skills, never outcomes: no red for loss or green for profit anywhere in the prototype.

| Colour | Dimension (key) | What it means for Ravi | Sector example | Where the prototype shows it |
|---|---|---|---|---|
| Green | Concept (`concept`) | Understands why a long option can lose although direction was right | In his trade the move added ₹40 per unit, but the IV fall took ₹48 and one day of theta took ₹23 | Reflect: payoff before and after the event |
| Red | Words (`words`) | Uses the desk's terms correctly | Knows IV, theta, implied move, straddle, OI and PCR; today he mixes up IV and vega | Words evidence from the terms he uses in his replies |
| Yellow | Expression (`english`) | Explains a decision clearly to the desk | Writes a two-line rationale the desk lead accepts: priced versus actual move, the sizing breach, the fix | Reflect: the rationale node |
| Blue | Practice (`lab`) | Does it in the real tool | Reads IV and the ATM straddle in the option chain and writes max loss inside the event budget before a paper order | Do: pre-event note on a terminal replay |

## The scenario in one paragraph

The day before a scheduled policy announcement, Ravi bought 4 lots (300 units) of the weekly 24200 CE at ₹90.25, with spot at 24,040, IV at 17.5% and 3 days to expiry. The outcome was as expected. The index closed the next day at 24,150 (+110), but IV fell to 11.0% and a day passed, so he sold at ₹59.55: **−₹9,210 (−34%) on the paper book**. Before the event the 24050 straddle priced a move of about ±304 points. His premium at risk, ₹27,075, was 2.7 times the desk's ₹10,000 event budget. A Black–Scholes check confirms the numbers ([scenario.json](scenario.json), `bsCheck`).

## What KiKi does, and won't do, for Ravi

| KiKi does | KiKi won't |
|---|---|
| Reviews the **process** behind a past or paper trade against the desk's playbook | Recommend a trade, give a signal or say "buy" or "sell" |
| Asks short questions and shows the payoff, the candles and the priced move | Place, modify or suggest an order, or take over the terminal |
| Records evidence in four dimensions; "not yet", never "wrong" | Show the desk his screens or conversation transcripts (the desk sees dimension-level evidence only) |
| Shows the disclaimer on every case card: *"Education on a past, illustrative trade. Not investment advice."* | Call the Hindi supported before a native reviewer signs it off |

## Language notes (machine draft)

- KiKi speaks Devanagari Hindi with English terms in Latin script, the way many Indian traders talk: "IV गिरा, इसलिए premium गिरा।"
- Terms kept in English and shown as chips: IV, IV crush, theta, vega, premium, strike, OI, PCR, straddle, lot, implied move, defined-risk, budget.
- Numbers, ₹ amounts and strikes keep one form everywhere (₹90.25, 24200 CE, ±304).
- Ravi's replies in the prototype are Devanagari Hindi with English terms. Real users will often type romanised Hinglish; the routing test set (S5 deliverable 5) should include both.

## Questions for the domain reviewer

1. Is a ~6.5-point IV drop (17.5% to 11%) plausible for a weekly index option across a scheduled policy event? The numbers are illustrative but should not look wrong to a trader.
2. Is a flat IV across strikes acceptable for teaching, or should the chain show a skew?
3. Does "time to the right trade" mean what we use it for (turns and hints Ravi needs to reach the playbook's process for a past situation)?
4. Prop desk or broker education: which should the video name as the paying organisation?
