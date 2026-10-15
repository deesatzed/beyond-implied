# GOAL — sim (planted signals, power, and canaries)

## Purpose

Know what the study can and cannot detect before spending real data, and prove the pipeline does not
leak the future. Adapted from the adversarial test battery in the ARC-GATE review.

## Built

- `generate.py`: synthetic earnings seasons with a planted amount of information the market misses,
  date-level shocks (clustering), optional premium sign flips by season, and an optional 10×
  catastrophic move. The model forecast uses only observable inputs plus the planted signal.
- `power.py`: size and power of the H1 encompassing test across sample sizes and effect sizes;
  stress scenarios; static vs adaptive conformal coverage under a regime flip. `bi power` writes
  `report/power/*.csv`; interpretation in `report/power.md`.
- `canary.py`: `assert_no_lookahead(feature_fn, events)` perturbs outcomes on/after a cut date and
  fails if any feature for events on that date changes.

## Findings (2026-10-15)

- Size holds at 2–4% under clustering, regime flips and a catastrophic outlier.
- ~2,000 events over ~140 announcement dates gives 81% power for a 5% effect; ~400 events gives
  roughly 25–35%. Plan the H1 dataset accordingly.

## Build steps

1. Re-run `bi power` after Phase 2 with parameters fitted to real data (dispersion of log implied
   moves, tail shape of realized/implied, date-shock size). Replace half-normal noise with the
   empirical distribution of realized/implied ratios.
2. Add a date-level planted signal (like a VIX feature) to show when clustering matters.
3. Every feature function added in Phases 4–5 must pass `assert_no_lookahead` in the test suite.

## Done when

- [x] Null size and planted power verified.
- [ ] Power re-run with parameters estimated from real events.
- [ ] Canary applied to every production feature.
