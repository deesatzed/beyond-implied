# PRE-REGISTRATION — DRAFT

**Status: DRAFT. Not frozen.** This file is frozen in Phase 3 by recording its SHA-256 in the ledger
and tagging `prereg-v1`. Any change after that is a new version with its own tag and a stated reason.

## Hypotheses

- **H1 (primary, earnings arena).** In the regression
  `|r_i| = a + b_model · F_model,i + b_imp · IM_i + b_tr · F_trailing,i + e_i`,
  where `|r_i|` is the realized absolute move, `F_model` the scaffold forecast, `IM` the implied move
  and `F_trailing` the trailing mean absolute move, `b_model > 0` at the 5% level with standard
  errors clustered by announcement date, on held-out seasons.
  *Narrowed 2026-10-15 (docs/prior-art.md):* that trailing moves add information beyond the implied
  move is already published, so the benchmark includes both.
- **H2 (secondary).** Area under the risk-coverage curve (QLIKE loss) for the scaffold with gates is lower
  than for the best baseline, on held-out seasons.
- **H3 (exploratory, control arena).** Scaffold features add information to HAR-IV for S&P 500
  21-day realized variance. Reported whatever the result; no claim rests on it.

## Event definition

- Before-open announcement on day D: pre-event close = close of D−1; post-event close = close of D.
- After-close announcement on day D: pre-event close = close of D; post-event close = close of D+1.
- Unknown or unconfirmed timing: excluded and counted.
- Retrospective seasons: Nasdaq's past calendar has no timing flag. Timing is the company's
  habitual timing (all recorded BMO/AMC values for that company agree, including upcoming dates);
  companies with mixed timing have unrecorded events excluded. *Changed 2026-10-15:* the earlier
  overnight-gap rule chose the window with the larger move, which selects on the outcome and
  inflates realized moves; it is kept only as a diagnostic.
- Fallback when no recorded or habitual timing exists: the IV-collapse rule (`events/timing_iv.py`),
  which dates the report by the close at which front-expiry ATM implied volatility drops, with a
  minimum collapse of 2 vol points and a larger-to-smaller drop ratio ≥ 1.5. Validated 2026-10-16 on
  763 events with reference timing: 94.5% classified, 96.1% agreement (`report/timing_iv.md`).
  Results are reported separately for IV-timed events.
- Realized move: `|post / pre − 1|`.
- Implied move: at-the-money straddle mid / spot at the pre-event close, using the first expiry after
  the event; secondary definition strips residual time value using two expiries (`events/` GOAL.md).

## Universe filters (config/universe.toml)

- Underlying price ≥ $10; option volume ≥ 300 contracts on the pre-event day.
- Straddle relative spread ≤ 25% of premium for the forecasting sample; ≤ 10% for any P&L
  statistic; zero bids excluded. *Changed 2026-10-15 (draft):* the median ATM spread rose from
  ~5.5% (2023) to 11–15% (2026) as nearer expiries appeared; a 10% cut removed 39% of events.

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

## Sample size

From the simulation power analysis (`report/power.md`): target ≥ 2,000 usable events over
≥ 140 announcement dates (80% power for a 5% effect). The achieved count is reported; if it falls
short, H1 is still run and reported with its power at the achieved size.

## Prediction bounds

Adaptive conformal upper bound on each move (`metrics/conformal.py`), α = 0.10; γ and calibration
window fixed here in Phase 3. Static conformal is reported as the comparison.

## Gate constraints

Gate G8 abstains when an FOMC statement or CPI release falls on the post-event date (dates in
`config/macro_events.toml`, sourced from the Federal Reserve and BLS). Hashed with the gates at the freeze.

No regime (chaos/entropy) feature drives a gate in v1. Gate rules are frozen with this file.

## Multiple comparisons

Feature list fixed before Phase 5 (at most 6 features). H1 is the only confirmatory test.

## After v1

Changes follow champion–challenger (BUILD.md, Phase 9): pre-registered before an unseen season,
promoted only if they beat the frozen champion on it.
