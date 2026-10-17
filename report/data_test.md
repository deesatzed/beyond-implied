# Phase 2 data test

Run 2026-10-16/17 on the Mac Mini: `bi timing-iv --names 500`, then `bi phase2 --names 500`
(2023-07-01 to 2026-10-14). Universe: the 500 largest names with ≥ 8 announcements since mid-2023.
Raw vendor data stays local; this file holds derived statistics. Tables: `report/data_test/seasons.csv`,
`report/data_test/real_params.json`. The 100-name run of 2026-10-16 is kept in
`report/data_test/100names/`.

## Decision (2026-10-17): go, with the claim limited to liquid optionable events

| Gate (GOAL.md / BUILD.md) | Result at 500 names | Status |
| --- | --- | --- |
| Calendar complete | 850 of 850 trading days | Pass |
| Outcome-free timing | 484 of 500 names have events built; 338 with recorded or habitual timing, 146 timed by the IV rule only. 349 of 6,390 announcements (5.5%) left untimed | Pass |
| IV timing rule holds at scale | 93.8% agreement, 85.1% coverage (96.1% and 94.5% at 100 names) | Pass |
| Unusable share ≤ 10–15% | **35.1%** (2,242 of 6,390); data-quality failures 5.9% | **Fail as unusable share; pass as data quality.** Resolved by limiting the population (below) |
| Season averages vs ORATS | Direction matches on ORATS's window; size does not (+3% vs +45%); ORATS method unpublished | Replaced by a direction check plus internal checks ([orats_check.md](orats_check.md)) |
| Path to ~2,000 usable events | 4,148 usable over 556 announcement dates | Pass |

### Why 35.1% are unusable

| Reason (an event can have several) | Events |
| --- | --- |
| No outcome-free timing | 349 |
| Pipeline failure (no event or stock data) | 31 |
| Straddle spread > 25% of premium | 1,588 (1,156 for this reason alone) |
| Option volume < 300 contracts | 624 (244 alone; 377 together with a wide spread) |
| Zero bid on a straddle leg | 106 |
| Price < $10 | 103 |
| Invariant errors | 0 |

Label-quality failures (no timing, pipeline errors, invariant errors) are 380 events, **5.9%**. The
rest, about 29%, are excluded by the pre-registered liquidity rules: wide spreads and thin volume.
Exclusion rises steeply as companies get smaller. By market-cap quintile, from largest to smallest:
12%, 26%, 32%, 36%, 46%.

**What this means.** The criterion was written to protect label quality, and on that reading it
passes. But it is stated as a plain unusable share, and on that reading it fails by a wide margin. I
have not redefined it. Three ways forward, for a decision before the Phase 3 freeze:

1. **Define the study population as liquid optionable events.** Keep the 25% spread and 300-contract
   rules, report the 35.1% openly, and limit every claim to that population. These rules use only
   pre-event information, so they do not select on the outcome. They do tilt the sample toward larger
   names.
2. **Shrink the universe** to the largest ~300 names, where exclusion is lower, and accept fewer events.
3. **Stop**, as GOAL.md's stop rule reads literally.

Option 1 keeps the most power and does not move a threshold. But it reinterprets a stop criterion,
so if chosen it must be written into PREREGISTRATION.md as a change, with this table as the reason.

**Chosen 2026-10-17: option 1**, together with walk-forward evaluation over all seasons. Both are
recorded in PREREGISTRATION.md (Study population; Evaluation design).

## Timing sources

| Source | Events built |
| --- | --- |
| Company's habitual timing | 4,279 |
| IV-collapse rule | 1,637 |
| Recorded on the calendar | 94 |
| No timing (excluded) | 349 |

Habitual timing matched recorded timing on 74 of 74 checks. The outcome-based gap rule (diagnostic
only, never used) agreed with the timing used on 75.0% of events.

## By season (usable events)

| Season | Built | Usable | Implied (event) | Realized | Realized / implied | Win rate | Straddle 1-day (mid) | Straddle 1-day (exec) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023Q3 | 449 | 364 | 4.5% | 4.7% | 0.95 | 42% | +3.2% | −7.2% |
| 2023Q4 | 457 | 362 | 4.7% | 4.6% | 0.88 | 40% | +3.5% | −7.2% |
| 2024Q1 | 449 | 379 | 5.4% | 5.5% | 0.98 | 43% | +7.7% | −6.9% |
| 2024Q2 | 460 | 377 | 5.6% | 5.0% | 0.85 | 36% | −2.7% | −18.1% |
| 2024Q3 | 463 | 351 | 6.0% | 5.8% | 0.93 | 42% | +4.5% | −12.3% |
| 2024Q4 | 469 | 353 | 5.8% | 6.1% | 0.98 | 40% | +4.4% | −9.6% |
| 2025Q1 | 460 | 304 | 6.2% | 5.5% | 0.87 | 38% | −3.1% | −18.4% |
| 2025Q2 | 451 | 244 | 6.0% | 4.8% | 0.73 | 28% | −13.4% | −27.0% |
| 2025Q3 | 470 | 259 | 6.2% | 6.4% | 0.99 | 39% | +4.3% | −7.8% |
| 2025Q4 | 467 | 286 | 6.2% | 5.2% | 0.78 | 32% | −7.4% | −21.3% |
| 2026Q1 | 468 | 296 | 6.2% | 5.7% | 0.87 | 40% | −1.9% | −17.2% |
| 2026Q2 | 471 | 306 | 6.4% | 6.4% | 0.95 | 40% | +5.2% | −10.6% |
| 2026Q3 | 460 | 254 | 6.8% | 6.0% | 0.81 | 33% | −4.1% | −19.1% |
| 2026Q4 (partial) | 16 | 13 | 4.0% | 3.9% | 0.97 | 46% | −2.6% | −15.7% |

Implied (event) strips base volatility using two expiries. Win = realized move above the event-implied
move. Straddle returns hold the pre-event ATM straddle for one day: mid to mid, and pre-event ask to
post-event bid. With 10% as the spread cut for P&L, the executable return is negative in 13 of 14
seasons; the exception is 2026Q2 (+1.7%, 102 events).

**Reading it:** at 500 names, realized moves fell short of implied moves in every season
(0.73–0.99), unlike the top 100 names, which averaged close to 1.0. Win rates are 28–46%, and an
executable one-day straddle lost money in every season. This is descriptive only; nothing has been
tested. 2,018 events carry the I4 warning: the first expiry is far from the event, which is common for
names with only monthly options. That makes the simple implied move overstate the event move. The
two-expiry event estimate is meant to correct for this. H1 uses the event estimate, and results will
be reported split by this warning.

**ORATS check: resolved 2026-10-17** ([orats_check.md](orats_check.md)). The earlier comparison used
the wrong window. On ORATS's own four weeks, January 14 to February 11, 2026, straddles did better
than this pipeline's historical average under every definition: one-day mid +3.4% vs +0.7%, hold to
expiry +3.2% vs +1.6%. So the direction agrees with ORATS. The size does not: ORATS reports +45%, and
its post does not give enough of its method to reproduce that figure. The gate is replaced by a
direction check plus internal checks.

## Real-data parameters (for `bi power-real`)

4,148 usable events over 556 announcement dates (median 4 per date). Dispersion of log implied moves
0.50; median implied move 5.5%; realized/implied median 0.76, 90th percentile 1.94, 99th 3.40.
Date effect 0.46. Power is re-run with these parameters: `report/power.md`.
