# Metric Tripwires

Ways a deck's numbers make an investor stop trusting it. Every tripwire is a
**P0** when it appears on a slide, because the reader can no longer trust the
numbers that follow. Sources: a16z "16 Startup Metrics" (2015-08-21) and "16
More Startup Metrics" (2015-09-23), plus YC where noted (source keys as in
[the investor lens](investor-lens.md)). The definitions still
hold; the 2015 benchmark values need current verification.

For each: **what you see** → **what the investor thinks** → **honest fix**.

## Charts (all business models)

- **Cumulative chart** (total users, revenue, or bookings to date) →
  "Cumulative charts always go up and to the right, even when the business is
  shrinking" [a16z-16 #14]; they "always cause immediate suspicion that there is
  no real growth" [Ralston-DD]. → Show per-period values (new users per month,
  monthly revenue). Revenue, new users, and bookings should never be cumulative
  [a16z-16more #16].
- **Unlabelled or truncated y-axis, stretched scale** → "They're
  exaggerating" [a16z-16 #15; a16z-16more #15]. → Start at zero, label the axis
  and units.
- **Percentages without absolute numbers** ("+400% MoM") → "Off what base?"
  Percentages "can sound impressive off a small base" [a16z-16 #15]. → Show the
  absolute numbers next to the percentage.
- **Growth averaged across months** → it overstates. → Use compounded monthly
  growth (CMGR) = (last month ÷ first month)^(1/months) − 1 [a16z-16 #10].
- **Growth shown without size** → the reader wants size first (revenue, GMV,
  bookings), then growth [a16z-16 #16]. → Give the current size next to the growth rate.

## Revenue labels

- **Bookings, LOIs, or verbal commitments called revenue** → bookings are a
  contract to pay; revenue is recognised as the service is delivered; LOIs are
  neither [a16z-16 #1]. → Label each clearly and keep them separate.
- **ARR = one month × 12**, or ARR that includes one-time, setup, services, or
  usage fees → ARR means annual *recurring* revenue, "NOT annual run rate"
  [a16z-16 #2; a16z-16more #2]. → Use recurring revenue only; call anything else
  "run rate" and say how it was calculated.
- **TCV shown as if it were annual** → use ACV (12-month value) for
  recurring fees [a16z-16 #4].
- **GMV called revenue (marketplaces)** → "GMV does not equal revenue!"
  [a16z-16 #6]. → Show GMV, net revenue, and the take rate.
- **Flat revenue with no billings or deferred revenue** (subscriptions
  billed upfront) → revenue can look stable while billings fall [a16z-16 #7].
  → Show billings in the appendix.

## Users and engagement (consumer, social, product-led)

- **Downloads or registered users presented as users** → a vanity metric,
  "one of those dreaded cumulative metrics", and often gamed [a16z-16 #13;
  a16z-16more #11]. → Show active users with retention.
- **"Active" not defined**, or defined differently over time → [a16z-16 #9;
  a16z-16more #12]. → Write down the event that counts as active, and keep it fixed.
- **MAU only for a daily-use product** → add DAU/MAU [a16z-16more #12].
- **One retention curve, or only the best cohort** → investors look for
  cohorts that level off after 6–12 months and newer cohorts doing better
  [a16z-16more #10]. → Put the full cohort table in the appendix.
- **NPS with no sample or distribution** → small or skewed samples
  [a16z-16more #9]. → Give n, the method, and the trend.
- **"Network effects" or "viral" asserted without numbers** → "entrepreneurs
  assert … network effects without providing any supporting evidence"
  [a16z-16more #6]. Virality is not a network effect [#7]. → Show the k-factor
  (below 1 is not viral) or the supporting network metrics, or drop the claim.

## Unit economics (SaaS, marketplaces, e-commerce)

- **Only blended CAC**, or CAC without credits, referral fees, or discounts →
  investors weight paid CAC more heavily; CAC rises as you scale [a16z-16 #8]. →
  Show paid CAC by channel, and say how it changes at the next spend level.
- **LTV based on revenue or gross margin**, or lifetime = 1/churn from a few
  months of data → it overstates how much you can spend to acquire a customer
  [a16z-16 #5]. → Use a contribution-margin LTV, or observed 12- and 24-month
  value.
- **Net churn or net retention without gross churn** → upsells hide losses
  [a16z-16 #11]. → Show both, monthly.
- **Gross margin without saying what is in COGS** (hosting, support,
  inference, payments) → [a16z-16 #3; a16z-16more #4]. → Break down COGS. For
  AI products, include inference cost explicitly. Software has historically run
  around 80–90% gross margin (2015 figure; verify current norms).
- **Large customer concentration not shown** → [a16z-16more #14]. → Give the
  top customer's share of revenue.

## Cash and the ask

- **Gross burn presented as burn**, or uncollected receivables counted as
  income → [a16z-16 #12]. → Give net burn and runway = cash ÷ net burn.
- **Runway, ask, and burn that don't reconcile across slides** → a
  consistency P0. → Make one set of numbers that is used everywhere.
- **Later stage:** the burn multiple (cash burned ÷ net new ARR) and Rule of 40
  (revenue growth % + profit margin %) are what investors check
  [a16z-cmd]. Show their trend over time, not one good quarter.

## Market

- **Top-down TAM** ("1% of a $50B market") → "why that share?"; it overstates
  and ignores distribution [a16z-16more #1; Ralston-Seed]. → Build it bottom-up:
  number of target customers × price, and say how you'll reach them.
- **TAM that doesn't match pricing shown elsewhere in the deck** → consistency P0.
