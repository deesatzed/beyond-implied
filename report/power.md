# Power analysis for H1 (simulation)

Run: `bi power --sims 500` on 2026-10-15. Raw tables: `report/power/*.csv`.
Simulator: `src/beyond_implied/sim/generate.py` (assumptions in its docstring).

## Bottom line

- **The test is honest.** With no planted signal, it flags "adds information" in 2–4% of studies
  (nominal 2.5% for a one-sided call at p < 0.05), including under premium regime flips and a single
  10× catastrophic move.
- **v1 needs about 2,000 usable events over ~140 announcement dates** to detect a model that holds
  5% of the variation in expected move size that the market misses, with 80% power.
- **~100 names is not enough for H1.** 100 names × 4 seasons ≈ 400 events; at that size power for a
  5% effect is roughly 25–35%. Use 100 names for the Phase 2 *quality* test only, and plan the H1
  dataset at ~500 optionable names per season, or more seasons.
- **Effects below ~2% are out of reach** at any size this project can assemble (27% power at
  2,100 events). Expect a null unless the real effect is ≥ 5%.

## Power by sample size and planted effect

Effect = private information's share of the variance of the true log expected move.
Rate = share of 500 simulated studies where the model was found to add information (b > 0, p < 0.05,
standard errors clustered by announcement date).

| Seasons | Events per date | Events | Dates | 0% (size) | 2% | 5% | 10% |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 8 | 280 | 35 | 4.2% | 13.0% | 24.4% | 46.8% |
| 1 | 15 | 525 | 35 | 2.6% | 12.8% | 36.6% | 69.0% |
| 2 | 8 | 560 | 70 | 3.0% | 15.0% | 38.0% | 71.6% |
| 2 | 15 | 1,050 | 70 | 2.6% | 16.6% | 55.8% | 90.8% |
| 4 | 8 | 1,120 | 140 | 3.6% | 16.6% | 61.2% | 94.0% |
| 4 | 15 | 2,100 | 140 | 3.0% | 27.2% | 80.8% | 99.4% |

## Stress scenarios (4 seasons, 15 events per date, 2,100 events)

| Scenario | Rejection rate |
| --- | --- |
| Null, date-clustered errors | 2.0% |
| Null, ignoring same-day correlation | 2.0% |
| Null, premium flips sign each season | 3.2% |
| Null, one 10× catastrophic move | 2.0% |
| 5% private info, baseline | 83.8% |
| 5% private info, premium flips each season | 82.8% |
| 5% private info, one 10× move | 81.4% |

Ignoring same-day correlation did not inflate false positives here because the planted information
is event-level. Market-wide features (VIX/VIX3M, VVIX) are date-level, and for them clustering will
matter; keep clustering by date.

## Upper-bound coverage under a premium flip (target 90%)

Bound on each event's move = implied move × conformal quantile of past realized/implied ratios.
Premium ±0.30 in log terms, alternating by season.

| Season | Static conformal | Adaptive conformal (γ = 0.05) |
| --- | --- | --- |
| 0 | 90.8% | 91.4% |
| 1 (implied underprices) | 78.3% | 86.5% |
| 2 (implied overprices) | 97.0% | 94.9% |
| 3 (implied underprices) | 80.6% | 84.4% |

Adaptive conformal recovers about half of the coverage lost to a regime flip within a season.
It helps; it does not solve it. Fix γ and the calibration window in the pre-registration.

## Limits of this simulation

- Realized moves are half-normal around their expectation; real earnings moves are fatter-tailed,
  which lowers power. Treat these numbers as an upper bound.
- The effect-size scale is a modeling choice. What matters is the ordering: sample size beyond
  ~2,000 events buys little for large effects and cannot rescue small ones.

## Real-data power at 500 names (2026-10-17)

`bi power-real --names 500 --target-names 500`, using parameters and the realized/implied move shape
estimated from the 4,148 usable events (`report/data_test/real_params.json`): about 7 usable events
per announcement date, 43 dates per season. 300 simulations per cell. The trailing move is included
as a control.

| Planted effect | 4 seasons (1,204 events) | 8 seasons (2,408) | 13 seasons (3,913) |
| --- | --- | --- | --- |
| None (false-positive rate) | 3.0% | 3.0% | 3.0% |
| 2% | 10% | 24% | 28% |
| 5% | 39% | 65% | 87% |
| 10% | 82% | 98% | 100% |

The earlier figure (93% at a 5% effect) assumed 500 names would give five times the 100-name event
count per date. The real 500-name table has fewer usable events per name, because smaller names fail
the liquidity rules more often. A first run on 2026-10-17 repeated that ×5 scaling by mistake and was
discarded; `--names` now defaults to 500.

**Design consequence for Phase 3.** The 87% figure needs all 13 seasons scored out of sample. With a
held-out set of only the last two retrospective seasons plus the forward season (about 3–4 seasons),
power at a 5% effect is about 40%. The split must be settled before the freeze. One option is a
rolling-origin evaluation: each season predicted by a model fit only on earlier seasons, so every
scored season is out of sample. The other is to accept low power on a small held-out set and say so.
