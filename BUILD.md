# BUILD — ordered phases with gates

Each phase lists its steps, the command that proves it, and a gate. Do not start a phase until the
previous gate passes. Sections referenced below each have their own `GOAL.md`.

Target: v1 by December 1, 2026.

---

## Phase 0 — Scaffold (done)

- [x] Repo, package layout, section GOAL.md files, config files
- [x] Working core: ledger, event math, metrics, baselines, regime features, gate engine
- [x] Tests pass: `make test`

**Gate:** `make test` green.

---

## Phase 1 — Prior-art pass (1 day)

Sections: `docs/`, `PREREGISTRATION.md`

1. [x] Read the earnings-move predictability literature and the HAR-IV literature. Record each paper's
   baseline, data, and finding in `docs/prior-art.md` (one row per paper). 13 entries, 2026-10-15.
2. [x] Fix the baseline set in `PREREGISTRATION.md`: implied move, trailing 12-event mean absolute move,
   trailing/implied ratio, HAR-IV (index arena).
3. [x] Note any existing public result that already answers H1; if one does, narrow the claim.
   Done: trailing moves already known to add information, so H1's benchmark now includes the
   trailing move. Re-run `bi power` with the three-regressor benchmark in Phase 2.

**Gate:** passed 2026-10-15.

---

## Phase 1b — Simulation and power (done 2026-10-15)

Section: `sim/`

- [x] Planted-signal simulator; null size check; power grid; stress scenarios (premium flips,
  catastrophic move); static vs adaptive conformal under a regime flip. `bi power`.
- [x] Look-ahead canary (`assert_no_lookahead`).
- [x] Result (`report/power.md`): H1 needs ~2,000 usable events over ~140 announcement dates for
  80% power at a 5% effect. ~400 events is badly underpowered.

**Gate:** passed. Consequence: the H1 dataset is planned at ~500 optionable names per season
(or more seasons), not 100 names.

---

## Phase 2 — Data test (2 days)

Sections: `data/`, `events/`

1. `bi indices VIX VIX3M VVIX SKEW` — download index history; run quality checks (gaps, outliers,
   the 2003 VIX methodology break).
2. [x] ThetaData adapter via the official Python library (no Terminal needed); live on the Mac
   Mini. The free account serves option EOD history from mid-2023 (refused for 2022 and earlier),
   about 13 seasons. Pull end-of-day chains for ~100 liquid names for the quality test. The H1
   dataset (~500 names per season) fits inside the free history; no paid tier needed for v1.
3. Load an earnings calendar with a before-open/after-close flag (`data/calendar.py`; Nasdaq's
   calendar carries the flag and is free).
4. Build the event table (`events/`): timing alignment, implied move (simple and term-structure
   event variance), realized move, quality flags.
5. Run the admissibility invariants (`events/invariants.py`) on every row; errors exclude, warnings
   are reported. Count both by check ID.
6. Write `report/data_test.md`: events per season, failures by check ID, season-average implied vs
   realized moves next to ORATS's published figures, and the projected usable events per season
   against the ~2,000-event power target.
7. Re-run `bi power` with dispersion, tail shape and date-shock size estimated from the real events.

**In parallel, start now:** run `bi daily` after the close on every trading day (launchd on the
Mac Mini). It snapshots each name on its pre-event and post-event close. Snapshots cannot be
collected after the fact; analysis waits for Phase 3.

**Gate (stop criteria from GOAL.md):** season averages roughly match ORATS; unusable events ≤ 10–15%;
a path to ~2,000 usable events exists. If any fails, stop and write up why.

**Result 2026-10-16: conditional GO** (`report/data_test.md`). Quality (12.8% unusable among events
with known timing), volume and power (93% at a 5% effect, 13 seasons, 500 names) pass. Outcome-free
timing covers 59 of 100 names; Phase 3 waits until coverage reaches ≥ 85% of names via daily
recording plus an implied-volatility-collapse timing rule validated on covered names. ORATS matches
over twelve quarters but not for the Jan–Feb 2026 season (large-cap universe, one-day hold).

**Update 2026-10-16: GO.** IV-collapse timing (96.1% validated) brings outcome-free timing to 99 of
100 names; the timing blocker is cleared. Unusable share 16.9% is a recorded marginal miss (wide
spreads), not a label-quality failure.

**Update 2026-10-17 (500 names): gate criterion failed, decision pending.** 4,148 usable events
(power target met), but the unusable share is 35.1%. Label-quality failures are 5.9%; the rest is the
liquidity rules, concentrated in smaller names. Phase 3 waits on the population decision
(`report/data_test.md`) and the ORATS check.

**Resolved 2026-10-17:** population limited to liquid optionable events; walk-forward evaluation;
ORATS replaced by a direction check plus internal checks (`report/orats_check.md`). Phase 2 gate
passed on those terms.

---

## Phase 3 — Freeze the pre-registration (half day)

1. Finalize `PREREGISTRATION.md`: hypotheses, metrics, study population (liquid optionable events,
   decided 2026-10-17), walk-forward evaluation design (decided 2026-10-17), gate rules in
   `config/gates.toml`, and the feature list (at most 6).
   - Try to extend earnings dates and stock closes before mid-2023, for the trailing-move baseline
     only. Record how many seasons can be scored.
   - Simulate power for that exact number of scored seasons and record it.
   - Commit and hash the walk-forward evaluation code before the freeze.
2. `bi ledger prereg PREREGISTRATION.md config/gates.toml config/universe.toml` — writes the SHA-256
   of each file as the ledger's first records.
3. `git tag prereg-v1 && git push --tags`.
4. Landing page (decided 2026-10-16: built after the freeze, not before): the question, the frozen
   pre-registration with its ledger hashes, the data test, and what will be evaluated when.

**Gate:** tag exists; ledger verifies; no evaluation has touched held-out seasons.

---

## Phase 4 — Baselines and metrics on training seasons

Sections: `forecasters/`, `metrics/`

1. Compute baseline forecasts per event without look-ahead (trailing windows end before the event).
2. Score with QLIKE, Mincer–Zarnowitz, and the encompassing regression (clustered by date).
3. Reproduce the 2023 finding that the trailing/implied ratio predicts straddle outcomes. If it does
   not reproduce, debug the data before going further.

**Gate:** baseline results reproduce the known ratio effect in direction.

---

## Phase 5 — Scaffold features and gates; held-out evaluation

Sections: `regime/`, `premium/`, `gates/`, `metrics/`

1. Add regime features (permutation entropy, DFA Hurst, recurrence rate) and premium features
   (VIX/VIX3M slope, VVIX level, implied/trailing ratio). Every feature passes the look-ahead canary.
   Regime features may enter the forecast but never a gate in v1 (a test enforces this).
2. Fit the scaffold forecast inside the walk-forward loop only (never on the season being predicted).
3. Apply the frozen gate rules; log every commit/abstain decision with the rule IDs that fired.
4. Produce adaptive conformal upper bounds (`metrics/conformal.py`, γ and window fixed in the
   pre-registration). Breaches feed Kupiec/Christoffersen; static conformal is the comparison.
5. Run the frozen walk-forward evaluation once: each season predicted by a fit on earlier seasons
   only. Report encompassing (pooled, date-clustered), risk-at-coverage curve, PIT, Christoffersen,
   hypothetical straddle P&L shape net of spreads, and the pre-registered robustness splits.

**Gate:** the walk-forward evaluation is run exactly once after the freeze; numbers written to the ledger.

---

## Phase 6 — Forward-live season

Sections: `data/`, `ledger/`

1. For each snapshot taken in Phase 2, write the prediction to the ledger before the announcement.
2. After each announcement, append the outcome record linked by prediction ID.
3. `bi ledger verify` must pass at every step.

**Gate:** every forward prediction's timestamp precedes its event; ledger verifies end to end.

---

## Phase 7 — Index control arena (can run in parallel with 4–6)

Sections: `data/`, `forecasters/`, `metrics/`

1. Realized variance from SPX daily OHLC (Garman–Klass) over 21-day windows.
2. HAR-RV and HAR-IV with and without scaffold features; non-overlapping monthly evaluation,
   HAC standard errors.

**Gate:** results reported whatever their sign.

---

## Phase 8 — Report and post

Section: `report/`

1. Writeup: question, method, pre-registration link, results, failures, limitations.
2. Figures: risk-at-coverage curve; implied vs realized by season; P&L distribution shape.
3. README updated with results and how to verify the ledger.
4. Post, then send directly to named contacts.

**Gate:** a stranger can clone, run `make test` and `bi ledger verify`, and read the result in 15 minutes.

---

## Phase 9 — After v1: champion–challenger

Sections: `forecasters/`, `gates/`, `ledger/`

1. The v1 model and gate rules become the frozen champion (tagged).
2. Any change (new feature, new rule, new threshold) is a challenger, pre-registered before the next
   season starts, with its hash written to the ledger.
3. After that season resolves, the challenger replaces the champion only if it beats it on the
   pre-registered metric (encompassing over the champion, or lower AURC at matched coverage).
4. Every promotion and rejection is a ledger record with the evidence.

**Gate:** no change reaches the champion without a season it never saw.

**First challenger (C1): open-world AI-elicited expert system** (revised 2026-10-17). For each
instrument and origin, an LLM names any factors it judges to drive volatility: company, sector,
supply chain, macro, policy, weather, geopolitical, strategic. Each factor gets a state and effect
distribution, and numerical inference combines them into a predictive distribution of move size.
Ablations test whether outside-the-market factors and the network structure add value. C1 is frozen
with v1 and logs forward from the freeze, on earnings events plus a weekly ETF panel. It is scored
forward only. Spec: `src/beyond_implied/challengers/elicited_net/GOAL.md`.

**Second challenger (C2): time-series foundation-model ensemble** (added 2026-10-18). TTM,
Chronos-2, TimesFM 2.5, TiRex and a small Toto 2.0, run zero-shot, plus Log-HAR and implied volatility,
combined equal-weight and with a walk-forward meta-learner. It runs on the ETF panel and the index
arena, not on one-day earnings moves, and serves as a control for C1's panel forecasts. Spec:
`src/beyond_implied/challengers/tsfm_ensemble/GOAL.md`.
