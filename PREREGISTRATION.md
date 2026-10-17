# PRE-REGISTRATION — DRAFT

**Status: DRAFT. Not frozen.** This file is frozen in Phase 3 by recording its SHA-256 in the ledger
and tagging `prereg-v1`. Any change after that is a new version with its own tag and a stated reason.

## Hypotheses

- **H1 (primary, earnings arena).** In the regression
  `|r_i| = a + b_model · F_model,i + b_imp · IM_i + b_tr · F_trailing,i + e_i`,
  where `|r_i|` is the realized absolute move, `F_model` the scaffold forecast, `IM` the implied move
  and `F_trailing` the trailing mean absolute move, `b_model > 0` at the 5% level with standard
  errors clustered by announcement date, on walk-forward out-of-sample forecasts (Evaluation design).
  *Narrowed 2026-10-15 (docs/prior-art.md):* that trailing moves add information beyond the implied
  move is already published, so the benchmark includes both.
- **H2 (secondary).** Area under the risk-coverage curve (QLIKE loss) for the scaffold with gates is lower
  than for the best baseline, on the same walk-forward forecasts.
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

## Study population (config/universe.toml)

*Decided 2026-10-17 (option 1A in `report/data_test.md`).* Every claim is limited to **earnings events
with liquid listed options** among the 500 largest names with ≥ 8 announcements since mid-2023. An
event is in the population when, at the pre-event close:

- Underlying price ≥ $10; option volume ≥ 300 contracts on the pre-event day.
- Straddle relative spread ≤ 25% of premium, and no zero bid on either leg. P&L statistics use the
  stricter ≤ 10% spread subset. *Changed 2026-10-15 (draft):* the median ATM spread rose from about
  5.5% (2023) to 11–15% (2026) as nearer expiries appeared, and a 10% cut removed 39% of events.
- Outcome-free timing exists (recorded, habitual or IV-collapse; see Event definition).

All of these use only pre-event information. At 500 names they exclude 35.1% of announcements:
5.9% for data-quality reasons (no timing, missing data) and about 29% for liquidity. The exclusion
falls more on smaller companies (12% of the largest market-cap quintile, 46% of the smallest), so the
population leans toward larger names. Results are not claimed for illiquid events.

**Stop-criterion clarification (recorded, not hidden).** GOAL.md's stop criterion reads "more than
about 10–15% of events fail data-quality checks"; BUILD.md paraphrased it as "unusable events". At
5.9% the data-quality reading passes and the unusable reading fails. This clarification was made
after seeing the 500-name data. It is recorded here, with `report/data_test.md` as the evidence,
instead of being presented as the original intent.

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

## Evaluation design: walk-forward over all seasons

*Decided 2026-10-17 (option 2B), replacing a single small held-out set, which had about 40% power at a
5% effect (`report/power.md`).*

- Seasons are calendar quarters of the announcement date (2023Q3 to 2026Q3, 13 complete seasons).
- For each scored season *s*, every quantity the model learns (coefficients, gate thresholds that
  are fit, calibration constants) is estimated only from events in seasons before *s*. Season *s*
  is then predicted once. Nothing estimated on season *s* or later is ever used to predict *s*.
- Minimum training history: 2 seasons. Scored seasons: from 2024Q1 to 2026Q3 (11 seasons), subject
  to the trailing-move requirement below.
- The trailing-move baseline needs ≥ 4 prior events per name. Earnings dates and stock closes before
  mid-2023 are needed only for it (no option data). If they are obtainable, they are used, and all
  11 seasons are scored. If not, scoring starts at the first season where ≥ 80% of population events
  have a trailing value, and the number of scored seasons is reported.
- H1 is one encompassing regression pooled over all scored seasons' out-of-sample forecasts, with
  standard errors clustered by announcement date. Per-season coefficients are reported as
  descriptive only.
- The model specification, the feature list (at most 6), the gate rules, the walk-forward
  procedure and the minimum-history rule are frozen at `prereg-v1`. The walk-forward evaluation is
  run once after the freeze. Its code is committed and hashed before it runs.
- The forward-live season (predictions written to the ledger before each announcement, from
  2026-10-15) is scored separately as a confirmatory check. It cannot be revised.

## Sample size

4,148 usable events over 556 announcement dates at 500 names (`report/data_test.md`). Real-data power
(`report/power.md`) at a 5% effect: 87% with 13 scored seasons, 65% with 8. Before the freeze, power
is simulated for the exact number of scored seasons and recorded here. If the result is null, it is
reported with that power.

## Robustness reported with H1 (not separate tests)

- By timing source (recorded, habitual, IV-collapse). Also excluding the events where habitual and
  IV-collapse timing disagree: about 4% of habitually timed events. Those events show more very
  small moves, consistent with occasional wrong-day measurement.
- By I4 warning (first expiry far from the event) and by market-cap tercile.
- Excluding events with an FOMC or CPI release in the window (gate G8).

## Outside benchmark check (ORATS)

*Changed 2026-10-17.* GOAL.md's criterion "season averages roughly match ORATS" cannot be applied as
written, because ORATS's post does not publish its holding period, pricing convention, universe size
or averaging method. It is replaced with a direction check plus internal checks; the details are in
`report/orats_check.md`.

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
