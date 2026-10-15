# GOAL — Beyond Implied

## The question

Does a forecasting scaffold carry statistically significant information about realized earnings moves
beyond the option market's implied move, and does it know when to abstain?

## The claim, stated so it can fail

1. **Encompassing (primary).** Regressing realized absolute earnings moves on both the scaffold's forecast
   and the implied move, the scaffold's coefficient is significantly different from zero, with standard
   errors clustered by announcement date, on seasons the model never saw.
2. **Risk at coverage (secondary).** Committing only where the gate layer allows, the scaffold's loss at
   matched coverage is lower than the best baseline's (implied move, trailing move, their ratio).
3. **Control arena.** On S&P 500 30-day variance, HAR-IV with the scaffold's features is compared with
   HAR-IV alone. A null result here is expected and will be reported.

## Success looks like

- A pre-registered result on held-out seasons, positive or null, with the ledger publicly verifiable.
- One writeup, one figure set, one repository a stranger can run in under 15 minutes.

## Stop criteria (checked at the end of Phase 2)

- Season-average implied and realized moves do not roughly match published ORATS season figures.
- More than about 10–15% of events fail data-quality checks.
- The trailing-move / implied ratio already explains the variation and the scaffold adds nothing in-sample.

## Non-goals

- Predicting direction (first order).
- Live trading, position sizing for real money, or any trade recommendation.
- Redistributing vendor data.
- Beating foundation models on raw accuracy.

## Deadline

v1 shipped by **December 1, 2026**: earnings arena only, three or four seasons retrospective plus
forward-live Q3 2026, three predictors against the ratio baseline, one writeup.
