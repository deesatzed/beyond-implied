# Phase 2 data test

Rebuilt 2026-10-16 on the Mac Mini with `bi phase2 --start 2023-07-01 --end 2026-10-14 --names 100`,
after adding the IV-collapse timing fallback (`report/timing_iv.md`). Universe: the 100 largest names
with ≥ 8 announcements since mid-2023. Raw vendor data stays local; this file holds derived statistics.
Tables: `report/data_test/seasons.csv`, `report/data_test/real_params.json`.

## Decision: GO, with one criterion marginally missed

| Gate (GOAL.md / BUILD.md) | Result | Status |
| --- | --- | --- |
| Calendar complete | 850 of 850 trading days | Pass |
| Outcome-free timing coverage ≥ 85% of names | 99 of 100 names; 1,233 of 1,307 announcements | Pass |
| Unusable share ≤ 10–15% | 16.9% (221 of 1,307): 74 with no timing (5.7%), 147 failing filters (11.2%) | **Marginal miss** |
| Season averages vs ORATS | 12-quarter pattern matches; Jan–Feb 2026 does not | Partial |
| Path to ~2,000 usable events | 1,086 usable from 100 names; ~5,400 projected at 500 names | Pass |

**On the 16.9%:** 140 of the 147 filtered events fail only the ≤ 25% straddle-spread rule, and
they cluster in 2025–2026 as spreads widened. These events are excluded by an explicit rule, not
mislabeled, so the criterion's purpose (trustworthy labels) holds; the cost is sample size, and the
sample remains far above the power target. I am not relaxing the spread rule a second time. The
miss is recorded here and in the pre-registration rather than redefined away.

## Timing sources

| Source | Events | Unusable after filters |
| --- | --- | --- |
| Recorded on the calendar | 13 | 15.4% |
| Company's habitual timing | 750 | 12.8% |
| IV-collapse rule (validated 96.1%) | 470 | 10.4% |
| No timing (excluded) | 74 | — |

The outcome-based gap rule (diagnostic only, never used) agreed with the timing used on 76.2% of
events, consistent with it selecting on the larger move.

## By season (usable events)

| Season | Built | Usable | Implied (event) | Realized | Realized / implied | Win rate | Straddle 1-day (mid) | Straddle 1-day (exec) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023Q3 | 92 | 89 | 4.3% | 4.7% | 1.07 | 48% | +10.9% | +2.8% |
| 2023Q4 | 92 | 89 | 4.2% | 4.9% | 1.15 | 49% | +14.5% | +5.4% |
| 2024Q1 | 88 | 86 | 5.2% | 6.3% | 1.23 | 49% | +12.8% | +1.7% |
| 2024Q2 | 95 | 92 | 5.2% | 5.0% | 0.95 | 49% | −4.2% | −16.3% |
| 2024Q3 | 97 | 92 | 5.3% | 5.2% | 0.95 | 47% | +0.2% | −14.2% |
| 2024Q4 | 95 | 86 | 5.2% | 5.5% | 1.04 | 41% | +2.7% | −9.0% |
| 2025Q1 | 96 | 78 | 5.4% | 5.0% | 0.92 | 45% | −4.8% | −16.2% |
| 2025Q2 | 90 | 70 | 5.4% | 3.9% | 0.70 | 23% | −22.3% | −32.2% |
| 2025Q3 | 96 | 80 | 5.0% | 5.7% | 1.13 | 43% | +7.7% | −2.3% |
| 2025Q4 | 96 | 83 | 5.1% | 4.1% | 0.77 | 33% | −13.7% | −23.7% |
| 2026Q1 | 97 | 76 | 5.1% | 5.2% | 1.02 | 47% | −2.6% | −14.4% |
| 2026Q2 | 96 | 82 | 5.5% | 6.0% | 1.07 | 46% | +6.7% | −5.3% |
| 2026Q3 | 93 | 74 | 5.8% | 6.2% | 1.02 | 45% | +5.3% | −6.6% |
| 2026Q4 (partial) | 10 | 9 | 3.4% | 3.0% | 0.89 | 44% | −2.7% | −14.8% |

Implied (event) strips base volatility using two expiries. Win = realized move above the event-implied
move. Straddle returns hold the pre-event ATM straddle for one day: mid to mid, and pre-event ask to
post-event bid.

**Reading it:** with nearly twice the events, the picture from the 59-name run holds. Large-cap
implied moves are close to fair (realized/implied ≈ 1.0 over 13 seasons), executable one-day
straddles lose in most seasons, and seasons rotate between regimes (0.70 to 1.23). 110 events
(about 9%) have an FOMC statement or CPI release in the event window; gate G8 will abstain on them.

**ORATS check:** unchanged. The 12-quarter average is close to ORATS's ≈ −2%; the Jan–Feb 2026 season
(+45% at ORATS) shows −2.6% here. Re-checked with the 500-name universe.

## Real-data parameters (for `bi power-real`)

1,086 usable events over 382 announcement dates. Dispersion of log implied moves 0.47; median implied
move 4.5%; realized/implied median 0.88, 90th percentile 2.00, 99th 3.53. Date effect 0.29 (now
estimable with more same-day events). The power grid is re-run after the 500-name pull.
