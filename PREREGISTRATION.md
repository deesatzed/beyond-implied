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
- Retrospective seasons: Nasdaq's past calendar has no timing flag, so timing is inferred from the
  larger overnight gap (close D−1 → open D vs close D → open D+1) and flagged `inferred`. The rule's
  accuracy is measured on forward events with recorded timing before it is used; inferred-timing
  events are reported separately.
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

## Sample size

From the simulation power analysis (`report/power.md`): target ≥ 2,000 usable events over
≥ 140 announcement dates (80% power for a 5% effect). The achieved count is reported; if it falls
short, H1 is still run and reported with its power at the achieved size.

## Prediction bounds

Adaptive conformal upper bound on each move (`metrics/conformal.py`), α = 0.10; γ and calibration
window fixed here in Phase 3. Static conformal is reported as the comparison.

## Gate constraints

No regime (chaos/entropy) feature drives a gate in v1. Gate rules are frozen with this file.

## Multiple comparisons

Feature list fixed before Phase 5 (at most 6 features). H1 is the only confirmatory test.

## After v1

Changes follow champion–challenger (BUILD.md, Phase 9): pre-registered before an unseen season,
promoted only if they beat the frozen champion on it.
