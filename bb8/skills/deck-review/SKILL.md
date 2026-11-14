---
name: deck-review
description: Review an existing startup pitch deck from the investor's or viewer's seat. Simulate what the reader thinks slide by slide, find the slide where interest turns into doubt, and return prioritised (P0–P3) next steps grouped by the investor question they answer and by the deck-craft step that fixes them. Grounded in published YC and a16z guidance for product startups from pre-seed to Series A. Use when the user has a pitch, fundraising, or investor deck (file, slides, outline, or text) and wants feedback before sending or presenting it. Do not use to build a deck from scratch (use the deck-craft skill) or to critique non-fundraising slides (use $design-critique).
---

# Deck Review

A deck is read by someone looking for a reason to stop, until something makes
them want the next meeting. This skill sits in that reader's seat. It tracks
what they understand, believe, and still doubt at every slide, finds the moment
the read turns sceptical, and turns that into a short, ordered fix plan.

Read [the investor lens](references/investor-lens.md) before every review. Read
[the metric tripwires](references/metric-tripwires.md) whenever the deck shows
numbers. Write the result with [the report template](references/report-template.md).

## 1. Get the whole deck

- Accept a .pptx, PDF, images, a Slides artifact, a link the host can open, an
  outline, or pasted text. Use the host's file tools (for example the pptx or
  pdf skill) to read every slide, including speaker notes and appendix.
- Number the slides as the reader sees them. If any slide cannot be read
  (an image without text, a broken export), say so; don't guess its content.
- Review what exists. Do not rewrite the deck unless asked.

## 2. Set the lens

Three facts change the verdict. Infer them from the deck when you can. Ask only
for those you can't infer, in one short question, otherwise state the assumption
and proceed:

1. **Stage:** pre-seed, seed, Series A, or later. This sets the evidence bar.
2. **Mode:** **sent** (read alone, must stand on its own) or **presented**
   (live; sparse slides, the founder narrates). Several rules flip between them.
3. **Business model:** SaaS, marketplace, consumer, hardware, or AI or usage-based.
   This decides which metric tripwires apply.

Useful but optional: the round size and use of funds, the target investor, and
the founder's own one-sentence pitch.

## 3. Cold read (the triage pass)

Read only the cover, the first two slides, and the slide headlines, the way a
busy partner skims. Then write:

- **Retell:** the one sentence the investor would use to describe this company
  to a colleague, written from what is on the slides, not what the founder meant.
- **Gap:** how that sentence differs from the founder's intended pitch, if known.

If you cannot write the retell sentence, that is already a P0.

## 4. Reader walk-through

Go slide by slide in order. For each slide record:

- **Monologue:** one or two first-person lines of what the reader thinks
  ("OK, dentists. But why can't they just use their PMS?").
- **Belief state:** Interested, Neutral, Sceptical, or Gone.
- **Questions:** questions this slide opens, and earlier ones it answers.

Keep a running **open-question ledger** across slides. This is what makes the
review an investor simulation rather than a slide checklist:

- A question opened and never answered is a finding.
- A question opened early and only answered much later is an order finding.
- A slide that answers a question nobody has asked yet may be in the wrong place.

Mark the **flip slide**: the first slide where the belief state drops and
stays down. Investors who like a company start adding ideas ("yes, and…");
investors who don't start looking for problems ("but what about…"). Everything after the flip
is read in the second mode, so the cause of the flip matters most.

Base each monologue line on something visible in the deck or on a principle
in the investor lens. Don't invent personal investor taste.

## 5. Run the checks

Using the investor lens, test each of the six investor questions:

1. **Comprehension:** what you do, for whom, today, in plain words.
2. **Trust:** numbers correctly defined, consistent across slides, no tripwires.
3. **Market and why now:** bottom-up size, a timing reason, a specific insight.
4. **Proof for this stage:** progress relative to time spent, meeting the stage bar.
5. **Team:** why these people, with specific and relevant facts.
6. **Ask:** an amount tied to milestones and a believable plan.

Then run the exit tests: the retell sentence, the 3–4 points a reader would
remember, and the swap test (would this pitch still make sense from a
different team? Ideally it would not).

Check consistency across slides: the same metric with different values, a TAM
that doesn't match the price × customers shown elsewhere, or runway that
doesn't match the ask and burn.

## 6. Prioritise

Rank each finding by what it does to the investor's decision, not by how
much work the fix takes.

| Level | In the investor's head | Typical findings |
|---|---|---|
| **P0: stops the read or breaks trust** | "I'm out" / "I don't trust these numbers" | can't retell what the company does after slides 1–2; any metric tripwire; numbers that contradict across slides; no ask; an exaggeration that can be checked |
| **P1: blocks conviction** | "Interesting, but I can't say yes" | no why-now or insight; top-down TAM; evidence below the stage bar; team slide without fit; ask not tied to milestones; product shown as roadmap rather than today; a ledger question never answered |
| **P2: adds friction** | "Hard work to follow" | jargon; more than one idea per slide; the strongest fact buried; topic headlines instead of claims; charts that need decoding; order that answers questions too late |
| **P3: polish** | barely noticed | legibility, contrast, consistency, branding noise, animation, typos |

Q&A preparation that doesn't belong in the deck goes in a separate
**Prepare (off-deck)** list: cohort tables, paid CAC by channel, gross and net churn,
COGS breakdown, ARR bridge, pipeline detail.

Tie-breakers:

- If unsure, ask: would the reader stop or distrust what follows? Then P0.
  Would they finish but not take the meeting? Then P1. Would they take the meeting
  but find the deck tiring? Then P2.
- The stage moves severity. A missing traction chart is P1 at Series A and
  usually not a finding at pre-seed. Weak team evidence is P0–P1 at pre-seed.
- The mode moves severity. Seven-plus words per slide is P2 for a presented
  deck and fine for a sent one. A sent deck that only makes sense with narration is P1.
- Merge findings that share one root cause into one finding that lists the affected slides.

## 7. Group and order the fix plan

Present the fixes in the order the user should do them:

1. **All P0s first, even small ones.** One trust break colours every later
   slide, because a reader who is no longer convinced reads the rest looking for problems.
2. **Then P1s, in the deck's reading order.** An early conviction gap lowers
   how every later slide is judged.
3. **Then P2s, then P3s.** Batch the P3s; they are usually one design pass.

Within each level, group findings by the investor question (Comprehension,
Trust, Market and why now, Proof, Team, Ask). Tag each finding with the
**deck-craft step** that fixes it, so the hand-off is direct:

- **Storyline** (deck-craft §2): comprehension, order, headlines, retell, the points the reader remembers.
- **Evidence** (deck-craft §3): tripwires, market sizing, traction, ask, consistency.
- **Visual** (deck-craft §4–7): legibility, chart form, one idea per slide, polish.

Each finding states: slides affected, the investor's thought, why it matters
(the principle and source key from the investor lens), a concrete fix, and the
effort (S, M, or L).

## 8. Close

- Name up to three **strengths to preserve** in revision, only real ones.
- Give the **single next action**, usually the first P0.
- Offer to apply the fixes with the deck-craft skill, starting with the Storyline
  and Evidence groups.

## Guardrails

- **Honest framing only.** Never help disguise a weak metric (for example by
  switching to a cumulative chart or relabelling GMV as revenue). Recommend
  honest framing, such as a smaller true number with a clear trend.
- **No invented benchmarks or market data.** Use the principles in the investor lens.
  When a current benchmark, valuation, or market claim matters, mark it
  "needs current verification" and offer $deep-research.
- **Don't optimise for imagined taste.** The goal is that this company's real
  story is clear and credible, not that it sounds like what someone thinks an
  investor wants.
- **Separate observation from inference.** "Slide 6 has no y-axis label" is an
  observation. "The investor will suspect padding" is the simulation. Keep them
  visibly distinct.
- **Stay proportionate.** A 6-slide teaser gets a short report. Don't pad the list.
- Defer pure slide-design critique to the deck-craft checklist, or to
  $design-critique for non-fundraising decks.
