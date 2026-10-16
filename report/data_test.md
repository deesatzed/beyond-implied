# Phase 2 data test

Run 2026-10-15/16 on the Mac Mini with `bi phase2 --start 2023-07-01 --end 2026-10-14 --names 100`.
Universe: the 100 largest names with ≥ 8 announcements since mid-2023. Raw vendor data stays local;
this file holds derived statistics only. Tables: `report/data_test/seasons.csv`; power:
`report/power/power_real.csv`.

## Decision: conditional GO

Data quality, volume and power pass. Timing coverage does not yet, and it is the one thing that blocks
freezing the pre-registration.

| Gate (GOAL.md / BUILD.md) | Result | Status |
| --- | --- | --- |
| Calendar complete | 850 of 850 trading days, 0 missing after retries | Pass |
| Unusable share ≤ 10–15% (events with known timing) | 98 of 763 unusable (12.8%) | Pass |
| Timing coverage | 59 of 100 names have outcome-free timing; 544 of 1,307 events have none | **Fail (fixable)** |
| Season averages vs ORATS | 12-quarter pattern matches; the Jan–Feb 2026 season does not (see below) | Partial |
| Path to ~2,000 usable events | ~665 usable from 59 names over 13 seasons; ~3,300 projected at 500 names with current coverage | Pass |
| Power for H1 (narrowed, real move shapes) | 93% at a 5% effect with 13 seasons at 500 names; size 2–3% | Pass |

## What the first full run got wrong, and what changed

1. **Timing selected on the outcome.** The first run chose before-open vs after-close by the larger
   overnight gap, which picks the bigger move. Against the timing now used, that rule was wrong on
   21% of events. Timing now comes from each company's habitual BMO/AMC (recorded calendar values,
   including upcoming dates), which matched recorded timing on 10 of 10 checks. The gap rule is kept
   as a diagnostic only.
2. **Spread cut too tight for near-dated straddles.** Median ATM straddle spread rose from ~5.5% of
   premium (2023) to 11–15% (2026). The forecasting sample now allows ≤ 25%; P&L statistics keep ≤ 10%.
3. Pipeline fixes found along the way: ThetaData's 365-day limit per stock request, rejection of
   future dates, Nasdaq rate limits (now 2 s pacing with backoff), cached `.meta.json` sidecars, and
   mixed timestamp formats in cached files. Each has a test.

## By season (usable events, outcome-free timing)

| Season | Built | Usable | Implied (event) | Realized | Realized / implied | Win rate | Straddle 1-day (mid) | Straddle 1-day (exec) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023Q3 | 57 | 54 | 4.4% | 4.4% | 0.98 | 44% | +7.6% | +0.1% |
| 2023Q4 | 58 | 56 | 4.2% | 5.0% | 1.19 | 57% | +20.8% | +10.9% |
| 2024Q1 | 58 | 57 | 4.7% | 5.9% | 1.23 | 47% | +10.3% | −0.7% |
| 2024Q2 | 59 | 57 | 5.1% | 4.6% | 0.89 | 47% | −8.2% | −20.0% |
| 2024Q3 | 59 | 56 | 5.3% | 5.3% | 0.96 | 45% | +0.8% | −15.0% |
| 2024Q4 | 59 | 55 | 5.1% | 5.3% | 1.02 | 42% | +1.9% | −11.5% |
| 2025Q1 | 59 | 47 | 5.4% | 5.1% | 0.94 | 51% | +0.7% | −11.7% |
| 2025Q2 | 59 | 44 | 5.5% | 4.1% | 0.73 | 20% | −22.7% | −32.7% |
| 2025Q3 | 59 | 49 | 5.0% | 5.8% | 1.13 | 41% | +8.1% | −2.8% |
| 2025Q4 | 59 | 49 | 5.1% | 4.1% | 0.78 | 31% | −13.5% | −24.2% |
| 2026Q1 | 59 | 46 | 5.1% | 5.3% | 1.03 | 46% | −1.6% | −13.9% |
| 2026Q2 | 59 | 51 | 5.5% | 6.3% | 1.12 | 49% | +10.8% | −2.7% |
| 2026Q3 | 59 | 44 | 6.0% | 6.4% | 1.03 | 45% | +7.8% | −5.1% |

Implied (event) strips the base volatility using two expiries. Win = realized move above the event-implied
move. Straddle returns hold the pre-event ATM straddle for one day: mid to mid, and pre-event ask to
post-event bid.

**Reading it:** across 13 seasons the large-cap implied move is close to fair (realized/implied
averages ≈ 1.0, win rate ≈ 45%), and buying the straddle at executable prices loses in most seasons.
Seasons swing between regimes (0.73 to 1.23), as ORATS describes.

**ORATS check:** ORATS reported ≈ −2% average straddle returns over twelve quarters, close to our
roughly flat mid-to-mid average. ORATS reported ≈ +45% for the season ending February 2026; our
2026Q1 large-cap row shows −1.6% (mid). Likely reasons: ORATS's broader universe (smaller names are
where underpricing is strongest, per Xing & Zhang), and holding to expiry rather than one day. Not
resolved; re-checked once the universe reaches 500 names.

## Timing coverage plan (blocks the pre-registration freeze)

- 16 names reported before the upcoming-dates window (banks, TSM, ASML and others); 28 have upcoming
  dates Nasdaq has not yet tagged. The daily job records timing as dates are tagged, so coverage grows
  through the Q3 season without any extra work.
- Add an outcome-free second source: the date the front-expiry implied volatility collapses (event
  variance leaves the options whether the stock moves or not). Validate it against habitual timing on
  the 59 covered names before using it on the rest.
- Gate for Phase 3: outcome-free timing for ≥ 85% of universe names.

## Power with real-data parameters

Move shapes resampled from the 665 usable events (realized/implied: median 0.88, 90th percentile 2.03,
99th 3.62), cross-sectional dispersion of log implied moves 0.48, date effect estimated ≈ 0 after
separating event-level noise. Projected to 500 names (~14 events per announcement date). Narrowed H1:
trailing move included as a control.

| Seasons | Events | 0% (false positives) | 2% | 5% | 10% |
| --- | --- | --- | --- | --- | --- |
| 4 | 1,008 | 2.0% | 15% | 54% | 88% |
| 8 | 2,016 | 3.3% | 30% | 78% | 100% |
| 13 | 3,276 | 2.3% | 48% | 93% | 100% |

Use all 13 seasons. A 2% effect remains out of reach; a null at 13 seasons would rule out effects of
about 5% or more.
