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

1. Read the earnings-move predictability literature and the HAR-IV literature. Record each paper's
   baseline, data, and finding in `docs/prior-art.md` (one row per paper).
2. Fix the baseline set in `PREREGISTRATION.md`: implied move, trailing 12-event mean absolute move,
   trailing/implied ratio, HAR-IV (index arena).
3. Note any existing public result that already answers H1; if one does, narrow the claim.

**Gate:** `docs/prior-art.md` exists with at least 8 entries; baselines named in the pre-registration.

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
2. Install the ThetaData Terminal on the Mac Mini (free tier) and implement `data/thetadata.py`
   against its documented endpoints. Pull one year of end-of-day chains for ~100 liquid names
   for the quality test. (The H1 dataset needs ~500 names per season; see Phase 1b. If the free
   year cannot supply that, the $80/month Standard tier reaches back to 2016.)
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

**In parallel, start now:** run `bi snapshot` daily after the close for the names reporting in the next
10 trading days. Snapshots cannot be collected after the fact; analysis waits for Phase 3.

**Gate (stop criteria from GOAL.md):** season averages roughly match ORATS; unusable events ≤ 10–15%;
a path to ~2,000 usable events exists. If any fails, stop and write up why.

---

## Phase 3 — Freeze the pre-registration (half day)

1. Finalize `PREREGISTRATION.md`: hypotheses, metrics, universe filters, train/held-out season split,
   gate rules in `config/gates.toml`, and the feature list (keep it short).
2. `bi ledger prereg PREREGISTRATION.md config/gates.toml config/universe.toml` — writes the SHA-256
   of each file as the ledger's first records.
3. `git tag prereg-v1 && git push --tags`.

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
2. Fit the scaffold forecast on training seasons only.
3. Apply the frozen gate rules; log every commit/abstain decision with the rule IDs that fired.
4. Produce adaptive conformal upper bounds (`metrics/conformal.py`, γ and window fixed in the
   pre-registration). Breaches feed Kupiec/Christoffersen; static conformal is the comparison.
5. Evaluate once on held-out seasons: encompassing, risk-at-coverage curve, PIT, Christoffersen,
   hypothetical straddle P&L shape net of spreads.

**Gate:** results computed exactly once on held-out data; numbers written to the ledger.

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
