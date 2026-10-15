# GOAL — metrics

## Purpose

Score forecasts by order: is the size right (second order), is the shape right and does the model
know its own uncertainty (third order), and what does it do to a decision (decision level).
The encompassing regression is the core claim test; everything else characterizes it.

## Inputs

Per event: realized move, implied move, baseline and scaffold forecasts, gate decision, confidence,
and (for third-order tests) predictive quantiles or PIT values.

## Outputs

Tables and figures for `report/`; headline numbers written to the ledger in Phase 5.

## Built in the scaffold

| Order | Function | What it answers |
| --- | --- | --- |
| 2nd | `qlike` | Variance-forecast loss that ranks correctly with a noisy proxy; punishes under-prediction |
| 2nd | `mincer_zarnowitz` | Is the forecast unbiased (intercept 0, slope 1)? Wald test |
| 2nd | `encompassing` | Does the model add information beyond the benchmark? Clustered or HAC errors |
| 3rd | `pit_uniformity` | Is the predictive distribution calibrated? KS test plus decile counts |
| 3rd | `kupiec`, `christoffersen` | Do tail breaches happen at the stated rate and not cluster? |
| 3rd | `conformal_upper` (static, or adaptive with γ > 0) | An upper bound on each move whose coverage adapts when regimes rotate (Gibbs & Candès ACI) |
| Decision | `risk_coverage`, `aurc`, `risk_at_coverage` | Loss when committing only to the most confident cases |
| Decision | `straddle_pnl`, `pnl_shape` | Hypothetical straddle P&L judged by skew, expected shortfall, drawdown |

## Build steps

1. Phase 4: run every second-order metric on baselines (training seasons).
2. Phase 4: add the Model Confidence Set (the `arch` package has one) for multi-forecast comparison.
3. Phase 5: produce adaptive conformal upper bounds (γ and window fixed in the pre-registration)
   and, optionally, quantile-regression quantiles for PIT; evaluate held-out seasons once.
   Simulation (`report/power.md`): under a ±0.30 premium flip, ACI recovered about half the coverage
   static conformal lost within a season.
4. Phase 5: risk-coverage curves for scaffold vs best baseline; straddle P&L net of half-spread.

## Done when

- [ ] Every metric has a unit test against a known answer.
- [ ] Encompassing regression on held-out seasons reported with clustered errors and cluster count.
- [ ] Risk-coverage figure and P&L-shape table in the report.

## Pitfalls

- QLIKE needs variances, not moves: square the moves consistently on both sides.
- Clustering by date: report the number of clusters; with few clusters, use wild cluster bootstrap.
- Hypothetical P&L at expiry ignores residual time value when expiry is after the post date; state it.
