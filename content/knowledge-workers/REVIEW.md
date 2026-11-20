# Trader and streamer lesson review

Draft source content · 20 November 2026 · all people, organisations and case data are illustrative.
English lesson sources; Hindi/Hinglish glosses and unchanged tutor lines are machine drafts. Domain and native review are pending.

Eight concepts, 32 placards, 80 source sentences and 64 checks. Practice predictions do not establish observed tool performance.

Generated from packet sources by `scripts/build-persona-content.py`; edit the packets and regenerate.

## Event days

Target: hi · Working language: en

### TR-IV-EVENT — Direction is only one price driver

Diagnose the illustrative option loss using price drivers and the desk comparison rule.

[Authoritative packet](packets/trading-fno/TR-IV-EVENT.packet.json) · Prerequisites: external basics only

**Definition**

The premium of a bought option reflects more than the direction of the index. The implied volatility is inferred from the option price through a pricing model.

**Concept**

In this illustrative case, implied volatility fell from 17.5% to 11% after the announcement. That IV crush and elapsed time outweighed the favourable index move; direction alone did not protect the premium. The desk uses the straddle as a rough implied move guide, not a guaranteed range or a profit threshold.

**Application**

The case straddle costs 153.55 plus 150.75, giving an implied move guide of 304.30 points. The desk rule EV-2.1 asks a historical note to compare its expected move with the implied move. In the replay, record the premium drivers and the missing comparison before assessing the decision.

**Recap**

The premium can fall even when the index moves favourably. Keep the desk implied move heuristic separate from the model price and the realised outcome.

**Worked question**

The case ATM call costs 153.55 and put 150.75. A historical note expects 150 points. Apply EV-2.1 without recommending a trade.

1. Add the two prices: 153.55 + 150.75 = 304.30 points as the desk guide.
2. The note expects 150 points, below that guide; it does not justify the comparison required by EV-2.1.
3. Record the missing justification. This heuristic does not by itself predict profit or loss.

**Concept checks — reviewer answer key**

| Question | Key | Why |
|---|---|---|
| The index rose while the case option lost value. Which explanation fits the case? | Volatility fell and time passed | The case keeps the strike fixed and separates the favourable spot effect from volatility and time costs. |
| Under EV-2.1, what is missing from a direction-only historical note? | Expected move versus the priced move | The desk asks for a move comparison using entry-time information; confidence language does not replace it. |
| Which interpretation of the straddle guide is appropriate? | A desk planning heuristic | The playbook uses a rough comparison; model price, time and volatility still determine the option value. |
| What is the case straddle price, using 153.55 and 150.75? | 304.30 points | Add both legs for the straddle guide; subtracting them measures a different quantity. |
| Which case component was the largest negative model contribution per unit? | IV at about minus 48 | The rounded attribution assigns the largest drag to IV; the positive spot component did not offset both costs. |

Wrong-option explanations and dimension-specific rubrics are in the packet.

**Expression:** Explain in two lines why the case option lost despite a rising index, and distinguish the desk heuristic from a profit guarantee. Working language: English.

**Practice exercise:** In the historical chain, identify the case call and put prices, add them, and annotate the old note with the missing EV-2.1 comparison.

**Sources:** Options desk playbook: event days (illustrative) — content/knowledge-workers/sources/design/personas/trader/playbook-excerpt.md; §2, EV-2.1; scenario marketBefore, marketAfter, impliedMove, decomposition; Historical paper option case (illustrative) — content/knowledge-workers/sources/design/personas/trader/scenario.json; Options Industry Council: Volatility and the Greeks — Opened 2026-11-20; model sensitivities and assumptions

### TR-THETA — Separate waiting from the IV change

Use a controlled repricing comparison to identify the cost of waiting in the case.

[Authoritative packet](packets/trading-fno/TR-THETA.packet.json) · Prerequisites: TR-IV-EVENT

**Definition**

The theta of an option describes model sensitivity to a day passing with other inputs fixed. The time value is the premium above intrinsic value.

**Concept**

A fall in implied volatility and the passage of time are different drivers of premium. The case attribution assigns about 23 rupees per unit to time, with separate volatility and spot contributions. The theta is a local sensitivity, so multiplying its entry value by several days need not give an exact repricing.

**Application**

The desk rule EV-3.1 asks for a one-day-later premium at the same spot before a historical overnight hold. Keep implied volatility and the other model inputs fixed to isolate waiting in that comparison. Save the replay inputs beside the premium comparison so a reviewer can reproduce the reasoning.

**Recap**

A change in premium across a night is not automatically all theta. Label a controlled time-only comparison separately from a full-case attribution.

**Worked question**

A historical review calls the full 30.70-per-unit loss theta. The case attributes about minus 23 to time and minus 48 to IV. Correct the note.

1. The full loss combines the favourable spot effect, volatility and time.
2. The rounded time component is about minus 23 per unit; it is not the full minus 30.70 fill-based loss.
3. For EV-3.1, compare next-day and original model values with spot, volatility and other inputs held fixed.

**Concept checks — reviewer answer key**

| Question | Key | Why |
|---|---|---|
| What must a controlled EV-3.1 comparison keep fixed? | Spot, volatility and other inputs | Moving several inputs at once cannot isolate time; the comparison changes the time remaining alone. |
| Why is the entire overnight loss not theta in this case? | Spot and IV changed as well | The observed change mixes drivers, whereas theta describes sensitivity to time with other inputs fixed. |
| Which note is most reproducible? | Both input sets plus model values | Input sets let a reviewer reproduce the controlled comparison; a result alone cannot explain the assumptions. |
| The rounded case time attribution is minus 23 per unit. For 300 units, what is that rounded component? | Minus 6900 rupees | Multiply the rounded per-unit component by quantity. Rounded components need not equal the exact fill-based loss. |
| Why is entry theta times three not necessarily an exact three-day value change? | Theta changes as model inputs evolve | Theta is a local model sensitivity that can change; a finite-period comparison requires repricing. |

Wrong-option explanations and dimension-specific rubrics are in the packet.

**Expression:** Explain to the desk why the observed overnight loss mixes drivers and which inputs isolate the cost of waiting. Working language: English.

**Practice exercise:** In a historical pricing replay, hold spot and IV fixed, reduce time remaining by one day, and save both model values; do not submit an order.

**Sources:** Options desk playbook: event days (illustrative) — content/knowledge-workers/sources/design/personas/trader/playbook-excerpt.md; §3, EV-3.1; scenario bsCheck and decomposition; Historical paper option case (illustrative) — content/knowledge-workers/sources/design/personas/trader/scenario.json; Options Industry Council: Theta — Opened 2026-11-20; model sensitivities and assumptions

### TR-EVENT-RISK — Size the risk before judging the result

Calculate the illustrative budget and evaluate the old position against its maximum loss.

[Authoritative packet](packets/trading-fno/TR-EVENT-RISK.packet.json) · Prerequisites: TR-IV-EVENT

**Definition**

The event budget is the illustrative desk limit on max loss for an event trade. A defined risk structure still needs sizing; a bounded loss can exceed the event budget.

**Concept**

Under the desk rule EV-4.1, the event budget is 1% of the 1000000-rupee paper book, or 10000 rupees. The case long option puts the full premium at risk before fees, with no claim about current exchange specifications. The realised loss was 9210 rupees, but the max loss at entry was 27075 rupees, so sizing breached the rule.

**Application**

At the case premium of 90.25 and 75 units per lot, max loss per lot is 6768.75 rupees before charges. The desk rule EV-4.2 rounds the budget divided by max loss per lot down to whole lots. The replay calculation permits 1 such lot before costs, rather than the historical 4; record the breach without placing an order.

**Recap**

Judge the event budget against max loss at entry, separately from the eventual outcome. Document defined risk, position size and stress assumptions in the historical review.

**Worked question**

Using only the illustrative case, compute the budget, maximum loss per lot and whole-lot limit before charges. Review the old four-lot position.

1. Budget: 1000000 times 0.01 = 10000 rupees.
2. Maximum loss per lot: 90.25 times 75 = 6768.75 rupees before charges.
3. Floor of 10000 divided by 6768.75 is 1 lot; four lots risked 27075, exceeding the budget by 17075.

**Concept checks — reviewer answer key**

| Question | Key | Why |
|---|---|---|
| Under EV-4.1, which amount is compared with the event budget at entry? | Maximum loss under the assumptions | The rule constrains risk taken before the outcome; later luck does not change the original exposure. |
| The case lost 9210 against a 10000 budget. Why was sizing still a breach? | Entry maximum loss was 27075 | The realised loss was inside budget, but the position could lose the full premium of 27075 before charges. |
| Which statement correctly describes defined risk? | Its bounded loss still needs sizing | A bounded loss is not necessarily an affordable loss; the desk sizing rules still apply. |
| What is the case maximum loss per long-option lot before charges? | 6768.75 rupees | Multiply premium per unit, 90.25, by the illustrative 75 units in a lot. |
| Budget divided by maximum loss per lot is about 1.48. What does EV-4.2 require in this exercise? | Round down to one whole lot | Rounding up exceeds the stated budget; conviction and the realised outcome do not replace entry-time sizing. |

Wrong-option explanations and dimension-specific rubrics are in the packet.

**Expression:** Explain why an inside-budget realised loss does not erase an entry-time sizing breach. Working language: English.

**Practice exercise:** On the paper case, write budget, quantity, maximum loss and charges allowance in the saved risk note; make no order.

**Sources:** Options desk playbook: event days (illustrative) — content/knowledge-workers/sources/design/personas/trader/playbook-excerpt.md; §4, EV-4.1 to EV-4.5; scenario context and sizing; Historical paper option case (illustrative) — content/knowledge-workers/sources/design/personas/trader/scenario.json; Options Industry Council: Volatility and the Greeks — Opened 2026-11-20; model sensitivities and assumptions

### TR-PRETRADE — Review the decision separately from its P&L

Write an auditable historical note and separate process quality from the result.

[Authoritative packet](packets/trading-fno/TR-PRETRADE.packet.json) · Prerequisites: TR-IV-EVENT, TR-THETA, TR-EVENT-RISK

**Definition**

A pre-trade note records the thesis, priced move, structure, max loss, exit plan and invalidation before the paper order. The outcome bias appears when a result replaces a review of the original reasoning.

**Concept**

The desk rule EV-6.1 requires process and outcome to be tagged separately. A profitable result does not repair a missing pre-trade note or an event budget breach. The case note named direction but omitted the implied move, max loss and exit plan.

**Application**

For the historical review, reconstruct what the pre-trade note lacked and mark reconstructed fields as hindsight. Use the original information to explain the move comparison and the event budget breach. Write a short process finding and a separate outcome line; do not fabricate an exit plan that never existed.

**Recap**

A pre-trade note is an entry-time record, not a story rewritten after the outcome. Counter outcome bias by naming the rule and evidence before describing the profit or loss.

**Worked question**

The case note says only that the policy will be positive and the index will rise. Write a two-line historical review under EV-6.1.

1. Process: the note lacks the expected-versus-priced move comparison, maximum loss and exit plan; entry risk also exceeded EV-4.1.
2. Outcome: the paper trade lost 9210 rupees before charges despite a favourable index move.
3. Any completed note written now is a labelled hindsight exercise, not evidence that an entry-time plan existed.

**Concept checks — reviewer answer key**

| Question | Key | Why |
|---|---|---|
| What should a retrospective completion of the old note be labelled? | Hindsight reconstruction | A reconstruction is useful for learning but must not be misrepresented as a note written before entry. |
| Which missing field matters in the direction-only case note? | An exit plan and invalidation | The playbook requires exit and invalidation information before entry; a direction statement does not provide it. |
| A winner had no note and breached sizing. Which EV-6.1 review is appropriate? | Bad process, good outcome | The profitable outcome is separate from the missing record and sizing breach, which remain process defects. |
| Which pair of review lines best fits the desk rule? | Rule compliance, then outcome | Process findings must use recorded evidence; the outcome is a separate description rather than its justification. |
| A complete, compliant paper note leads to a loss. What can the review conclude? | Process may be sound despite the loss | The desk separates decision quality from noisy outcomes; a loss alone does not establish a process failure. |

Wrong-option explanations and dimension-specific rubrics are in the packet.

**Expression:** Give the desk two lines: the evidenced process finding and the separate illustrative outcome. Working language: English.

**Practice exercise:** Open the saved historical note, mark absent fields, and write a labelled reconstruction beside it without overwriting the original.

**Sources:** Options desk playbook: event days (illustrative) — content/knowledge-workers/sources/design/personas/trader/playbook-excerpt.md; §6, EV-6.1; trainee checklist; scenario trade.preTradeNote; Historical paper option case (illustrative) — content/knowledge-workers/sources/design/personas/trader/scenario.json; Options Industry Council: Volatility and the Greeks — Opened 2026-11-20; model sensitivities and assumptions

## Launch-week streams

Target: hi-Latn · Working language: hi-Latn

### ST-HOOKS — Give every slow segment a reason to stay

Restructure the illustrative grind using the agency segment rules.

[Authoritative packet](packets/streaming-gta/ST-HOOKS.packet.json) · Prerequisites: external basics only

**Definition**

A hook states why an audience should keep watching the current segment. A run-of-show names each segment, its goal and its target duration.

**Concept**

In the illustrative case, the silent grind segment ran from minute 38 to minute 60 with no stated goal or chat interaction. The agency rule LW-5.2 limits a grind segment to 10 minutes with a stated goal and audience participation. The weak hook and missing participation are review hypotheses; the chart alone does not prove why each viewer left.

**Application**

Review the VOD around the transition before diagnosing the segment. Draft a shorter grind segment with a stated goal and a poll, following the agency playbook. Save the revised run-of-show for the manager instead of changing the live stream automatically.

**Recap**

A slow segment needs a hook and a plan under this agency playbook. Treat the duration and silence limits as agency rules, not universal platform statistics.

**Worked question**

The case grind runs from minute 38 to 60 without a goal or chat participation. Diagnose it under LW-5.2 and draft a replacement.

1. The duration is 22 minutes, exceeding the agency ten-minute cap. The stated goal and participation are also absent.
2. Draft a grind of at most ten minutes, say the goal before the transition, and attach a poll or other chat mechanic.
3. Save a review plan and test it; this is not a claim that every grind loses viewers.

**Concept checks — reviewer answer key**

| Question | Key | Why |
|---|---|---|
| What is the most defensible planning gap in the case grind? | No stated goal or participation | The case notes establish missing structure; they do not establish every viewer motivation or a universal ban. |
| Under LW-5.2, which draft fits the agency rule? | Ten minutes, stated goal and poll | The agency requires duration, goal and participation together; music or a title alone does not satisfy the rule. |
| How should the agency silence limit be described? | This agency rule of thumb | The source is an illustrative agency playbook, not a platform study or published legal requirement. |
| How long was the case grind from minute 38 up to minute 60? | 22 minutes | Subtract the start from the exclusive end of the segment; that gives twenty-two minutes. |
| What should the learner do before making a causal claim from the drop? | Review the transition in the VOD | The VOD adds context to the timing; a line chart by itself does not establish a causal explanation. |

Wrong-option explanations and dimension-specific rubrics are in the packet.

**Expression:** Pitch the segment diagnosis and the revised goal-led block to the agency in two clear lines. Working language: Hinglish; canonical terms stay unchanged.

**Practice exercise:** In the saved run-of-show, mark the 38-to-60 segment and draft a shorter goal-led version; the learner makes the edit.

**Sources:** Launch-week streaming playbook (illustrative) — content/knowledge-workers/sources/design/personas/streamer/playbook-excerpt.md; §2-3, LW-3.1; §5, LW-5.1 and LW-5.2; scenario segments; Launch-week stream case (illustrative) — content/knowledge-workers/sources/design/personas/streamer/scenario.json

### ST-CHAT — Read chat as an early warning, then verify

Compare the timing of chat and viewer changes without claiming causation from correlation.

[Authoritative packet](packets/streaming-gta/ST-CHAT.packet.json) · Prerequisites: ST-HOOKS

**Definition**

The chat rate is the number of messages per minute in this case. A chat mechanic gives viewers a planned way to participate, such as a poll.

**Concept**

The case chat rate fell from 87 messages at minute 37 to 15 at minute 41. The viewer line remained near its earlier level around minute 40 before declining. The agency treats chat rate as an early warning, but a quiet chat alone cannot identify a cause.

**Application**

Under the agency rule LW-4.1, every grind or loading stretch needs a chat mechanic. Compare chat rate with the segment transition, then inspect the VOD to check what changed. Record the warning and the proposed response in the next plan; do not infer a live audience preference from one signal.

**Recap**

Use chat rate with the viewer line and segment notes. Treat a missing chat mechanic as a playbook gap, while keeping the causal diagnosis provisional.

**Worked question**

Chat changes from 87 messages at minute 37 to 15 at minute 41, while viewers initially hold. What should the agency review?

1. The chat decline is 72 messages per minute, about 82.76 percent of the earlier rate.
2. Viewer stability does not erase the participation warning. Compare the transition and VOD with the chat trace.
3. Check whether the planned chat mechanic required by LW-4.1 was present; do not claim this alone proves a cause.

**Concept checks — reviewer answer key**

| Question | Key | Why |
|---|---|---|
| Which signal changed early in the case? | Chat rate near the transition | The case trace shows the early chat decline; the later raid cannot explain the earlier sequence. |
| What does LW-4.1 require during a grind? | A poll or participation mechanic | The agency requires a participation mechanism; KiKi coaches while the creator performs the work. |
| What follows from a quiet chat alone? | A warning that needs context | A warning guides a review; the trace alone cannot identify one cause or prove a platform action. |
| What is the decline from 87 to 15 chat messages per minute? | 72 messages | Subtract the later rate from the earlier one. The size of the decline is separate from its cause. |
| Which review best uses the early warning? | Compare both traces and inspect the VOD | Multiple traces and the VOD provide context; a single illustrative episode cannot establish a universal timing rule. |

Wrong-option explanations and dimension-specific rubrics are in the packet.

**Expression:** Explain the observed chat-first sequence and state what further evidence would support your diagnosis. Working language: Hinglish; canonical terms stay unchanged.

**Practice exercise:** On the saved analytics trace, locate minutes 37 to 43, compare chat with viewers, and note the transition for VOD review.

**Sources:** Launch-week streaming playbook (illustrative) — content/knowledge-workers/sources/design/personas/streamer/playbook-excerpt.md; §4, LW-4.1; scenario drop and series.chatPerMin; Launch-week stream case (illustrative) — content/knowledge-workers/sources/design/personas/streamer/scenario.json

### ST-RETENTION — Compare segments without mistaking counts for people

Compute the agency segment ratio and explain its limits.

[Authoritative packet](packets/streaming-gta/ST-RETENTION.packet.json) · Prerequisites: ST-HOOKS, ST-CHAT

**Definition**

The CCV measures concurrent viewers at a moment, rather than unique viewers across the whole stream. The agency defines segment retention as last-minute CCV divided by first-minute CCV.

**Concept**

The case grind segment uses minute 38 as its first sample and minute 59 as its last, with CCV of 556 and 348. The segment retention is about 0.626, rounded to 0.63, below the agency review threshold of 0.8. This ratio compares counts; it does not prove that the same 63% of viewers stayed throughout.

**Application**

The case vote segment has CCV of 351 at minute 60 and 477 at minute 91, giving a ratio near 1.36. A segment retention above 1 indicates net growth in concurrent counts, not impossible individual retention. Under the agency rule LW-6.1, flag the grind for VOD review and keep the later raid separate from this comparison.

**Recap**

Always state the CCV endpoint convention when reporting segment retention. Use the agency threshold to prioritise review, rather than to assert a causal explanation.

**Worked question**

Using grind endpoints 556 and 348, and vote endpoints 351 and 477, calculate the agency ratios and state one limitation.

1. Grind: 348 / 556 = 0.625899, about 0.63; this is below the agency threshold 0.8.
2. Vote: 477 / 351 = 1.358974, about 1.36; concurrent counts grew.
3. These ratios compare aggregate counts, not the same people; they do not by themselves establish causation.

**Concept checks — reviewer answer key**

| Question | Key | Why |
|---|---|---|
| Why can segment retention exceed one under LW-6.1? | Concurrent counts can grow | The agency ratio uses two concurrent counts, so arrivals can produce a value above one. |
| Which endpoints belong to the grind interval from minute 38 up to minute 60? | Minute 38 and minute 59 | The case uses an exclusive end boundary; minute sixty is the first sample of the next segment. |
| How should a ratio below 0.8 be used? | An agency flag for closer review | The agency threshold prioritises review; the VOD and surrounding signals are still needed for diagnosis. |
| What is 348 divided by 556, rounded to two decimals? | 0.63 | The endpoint count ratio is about 0.626. The roughly thirty-seven percent decline is a different representation. |
| What is unsupported by a count ratio of 0.63? | Exactly 63 percent of the same people stayed | Concurrent count endpoints do not identify individual viewers; arrivals and departures may both occur. |

Wrong-option explanations and dimension-specific rubrics are in the packet.

**Expression:** Report the two ratios with their endpoint conventions and explain why they are not individual-viewer retention. Working language: Hinglish; canonical terms stay unchanged.

**Practice exercise:** Select the grind interval on the saved dashboard, read minutes 38 and 59, compute the ratio, then inspect the VOD around the transition.

**Sources:** Launch-week streaming playbook (illustrative) — content/knowledge-workers/sources/design/personas/streamer/playbook-excerpt.md; §6, LW-6.1; scenario segmentStats, series and drop; Launch-week stream case (illustrative) — content/knowledge-workers/sources/design/personas/streamer/scenario.json

### ST-EXPERIMENT — Propose one change and a measurable review

Write a single-change learning plan with a prediction, measure and attribution limits.

[Authoritative packet](packets/streaming-gta/ST-EXPERIMENT.packet.json) · Prerequisites: ST-HOOKS, ST-CHAT, ST-RETENTION

**Definition**

An experiment records a planned change, the expected effect and a measure for review. A confounder is another changing factor that makes attribution uncertain.

**Concept**

Under the agency rule LW-6.2, change one thing per stream and log the prediction, measure and result. The case recovery coincided with polls, talking and a new segment, so it cannot isolate one change. The incoming raid at minute 95 is another confounder when comparing later viewer counts.

**Application**

Draft one experiment that adds a poll to an otherwise comparable slow segment. Keep the goal and duration fixed, then compare segment retention and chat rate while logging audience-source differences. State a provisional review threshold before the next stream, send the plan to the manager, and record an inconclusive result honestly.

**Recap**

A useful experiment includes one change, a prediction, a measure and a review decision. A threshold guides review; a positive result does not remove every confounder or prove causation.

**Worked question**

Draft a one-change plan under LW-6.2. Include a measure, a provisional threshold and a reason the result may be inconclusive.

1. Change: add one poll to a comparable slow segment, keeping its stated goal and duration fixed.
2. Prediction and review: participation may improve; compare chat rate and agency segment retention, using 0.8 as a provisional review flag rather than a success guarantee.
3. Log raids, audience mix and execution differences; repeat or report inconclusive if they prevent attribution.

**Concept checks — reviewer answer key**

| Question | Key | Why |
|---|---|---|
| Which plan best fits LW-6.2? | One poll change with a prediction and measure | The rule asks for a traceable single change; several simultaneous changes make attribution harder. |
| Why can the case recovery not identify the effect of polls alone? | Talking and segment context also changed | Several things changed together, so the historical comparison does not isolate a poll effect. |
| What should happen when a raid makes the comparison unclear? | Log the confounder and qualify the result | The raid changes who is present; honest review retains the observation and qualifies attribution. |
| When should the prediction and review measure be written? | Before the planned experiment | Writing the measure beforehand reduces hindsight selection and makes the later review auditable. |
| What does meeting the provisional threshold establish? | Evidence to review with context | A threshold organises review. Context and confounders still matter, especially with one illustrative episode. |

Wrong-option explanations and dimension-specific rubrics are in the packet.

**Expression:** Pitch cause hypothesis, one change, measure and uncertainty to the manager in two lines. Working language: Hinglish; canonical terms stay unchanged.

**Practice exercise:** Draft tomorrow run-of-show yourself with one labelled experiment, its prediction and review measure; log any raid or concurrent change.

**Sources:** Launch-week streaming playbook (illustrative) — content/knowledge-workers/sources/design/personas/streamer/playbook-excerpt.md; §6, LW-6.2; §5, LW-5.1; scenario recovery and events; Launch-week stream case (illustrative) — content/knowledge-workers/sources/design/personas/streamer/scenario.json
