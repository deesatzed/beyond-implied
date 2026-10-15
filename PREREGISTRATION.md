# PRE-REGISTRATION — DRAFT

**Status: DRAFT. Not frozen.** This file is frozen in Phase 3 by recording its SHA-256 in the ledger
and tagging `prereg-v1`. Any change after that is a new version with its own tag and a stated reason.

## Hypotheses

- **H1 (primary, earnings arena).** In the regression
  `|r_i| = a + b_model · F_model,i + b_imp · IM_i + e_i`,
  where `|r_i|` is the realized absolute move, `F_model` the scaffold forecast and `IM` the implied move,
  `b_model ≠ 0` at the 5% level with standard errors clustered by announcement date, on held-out seasons.
- **H2 (secondary).** Area under the risk-coverage curve (QLIKE loss) for the scaffold with gates is lower
  than for the best baseline, on held-out seasons.
- **H3 (exploratory, control arena).** Scaffold features add information to HAR-IV for S&P 500
  21-day realized variance. Reported whatever the result; no claim rests on it.

## Event definition

- Before-open announcement on day D: pre-event close = close of D−1; post-event close = close of D.
- After-close announcement on day D: pre-event close = close of D; post-event close = close of D+1.
- Unknown or unconfirmed timing: excluded and counted.
- Realized move: `|post / pre − 1|`.
- Implied move: at-the-money straddle mid / spot at the pre-event close, using the first expiry after
  the event; secondary definition strips residual time value using two expiries (`events/` GOAL.md).

## Universe filters (config/universe.toml)

- Underlying price ≥ $10; option volume ≥ 300 contracts on the pre-event day.
- Straddle relative spread ≤ the configured maximum; zero bids excluded.

## Baselines

1. Implied move.
2. Trailing mean absolute move over the previous 12 events (ending before the event).
3. Trailing / implied ratio.
4. HAR-IV (control arena only).

## Metrics

- Second order: QLIKE, Mincer–Zarnowitz, encompassing regression, Model Confidence Set.
- Third order: PIT uniformity, Christoffersen conditional coverage at 5% and 1%.
- Decision: risk-at-coverage curve; hypothetical straddle P&L net of half-spread, judged by skew,
  expected shortfall (worst 1%), and max drawdown.

## Split

- Training seasons: TBD in Phase 3 (all but the last two retrospective seasons).
- Held-out: the last two retrospective seasons plus the forward-live season.
- Held-out data is evaluated exactly once.

## Multiple comparisons

Feature list fixed before Phase 5 (at most 6 features). H1 is the only confirmatory test.
