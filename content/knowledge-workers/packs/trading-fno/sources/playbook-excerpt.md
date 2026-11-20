# Options desk playbook: event days (excerpt)

> **Illustrative.** An invented prop desk's internal playbook, written as input for KiKi's tribal knowledge builder. It is not a real firm's document and not investment advice. It describes process for reviewing past and paper trades; it recommends no trade.

Desk: index options · Applies to: trainees on the paper book and juniors on live limits · Owner: head of training (illustrative) · Version 3 · Section IDs (EV-x.y) are the source tags KiKi's lessons cite.

## 1. What counts as an event day

A scheduled announcement that can move the index in one print: a monetary-policy decision, the Union Budget, a major inflation or growth release, election results, or results from the largest index constituents. The event calendar is pinned in the desk channel every Monday. **If an event falls before your option's expiry, you are trading the event, whether you meant to or not.**

## 2. IV before scheduled events

- Implied volatility (IV) climbs into a scheduled event, because the market is paying for an outcome nobody knows yet. Once the outcome is out, IV usually falls, often within minutes. The desk calls this the **IV crush**.
- An option bought the day before an event pays for that uncertainty. To make money you need a move **bigger than the one already priced**. Direction alone is not a thesis.
- Before any event-day trade, write down: (a) the strike's IV now and its usual level; (b) the **implied move**: the ATM straddle price is a good rough guide to the move the market expects by expiry; (c) your expected move, and why it is bigger or smaller than the implied move.
- **EV-2.1** If you cannot say why your expected move beats the implied move, do not buy premium into the event.

## 3. Theta near expiry

- Time value decays fastest in the last days before expiry. A weekly option held across an event pays twice: theta, and the IV fall.
- Overnight and weekend holds still cost time value.
- **EV-3.1** Quick check before you hold overnight: reprice the position one day later at the same spot. That loss is the price of waiting.

## 4. Position sizing and defined risk on event days

- **EV-4.1 Event budget.** Maximum premium at risk per event trade: 1% of book. All event trades together: 2%. On the trainee paper book (₹10,00,000) that is ₹10,000 per trade.
- **EV-4.2** Size from the loss you accept, not from conviction: lots = budget ÷ max loss per lot, rounded down. When you buy an option, the whole premium is the max loss.
- **EV-4.3** On event days trainees use defined-risk structures only: long options or debit spreads, sized inside the budget. No naked short options.
- **EV-4.4** Prefer structures where a short leg offsets part of the IV fall, such as a vertical spread, and say in the rationale what the structure does if IV falls.
- **EV-4.5 Stress test** before entry: reprice at spot ± the implied move with IV 5 points lower. If the worst case breaks the budget, cut size or skip.
- **"No trade" is a valid event-day position.** Waiting until after the announcement, when IV has reset, can be a cheaper way to express a view.

## 5. Reading the chain before the event (context, not signals)

- Note where open interest (OI) is concentrated. Large call OI above spot and large put OI below it show where option writers have positioned for the event. Treat this as context for the size of move the market expects, never as a signal on its own.
- The put-call ratio of OI (PCR) moves with hedging flows. Don't read it alone.

## 6. Journaling

**Pre-trade note** (before the order): thesis (direction *and* expected move) · IV and implied move · structure · max loss in ₹ and as % of book · exit plan (time and price) · what would prove you wrong.

**Post-trade review** (same day): tag the trade on process and outcome, separately:

| | Good outcome | Bad outcome |
|---|---|---|
| **Good process** | Repeat it | Repeat it; the loss was the cost of the odds |
| **Bad process** | Luck: fix the process anyway | Fix the process |

Name which rule held or broke, in one or two lines the desk lead can read in the morning meeting.

- **EV-6.1** The desk reviews process, not P&L. A losing trade with a complete note is a good day's work. A winning trade with no note is not.

## Trainee checklist: event day

- [ ] Event and time on the calendar
- [ ] Strike IV now versus its usual level
- [ ] Implied move from the ATM straddle
- [ ] My expected move, and why
- [ ] Defined-risk structure (EV-4.3)
- [ ] Max loss inside the event budget (EV-4.1)
- [ ] Stress test done (EV-4.5)
- [ ] Exit plan written
- [ ] Pre-trade note saved

---

*How KiKi would use this:* the builder splits it into one module ("Event days") with four concepts: IV before events (§2), theta near expiry (§3), event sizing and defined risk (§4), the pre-trade note (§6). It renders them in Hindi with the terms kept in English, tags each placard with its EV section, and marks every rendition `draft` until a desk reviewer approves it. The tutor graph's branches cite EV-2.1, EV-4.1 and EV-4.3.
