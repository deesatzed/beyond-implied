# Checkpoints

Newest first. Each checkpoint has a matching git tag `checkpoint-YYYY-MM-DD`.

---

## 2026-10-15 (evening) — Review items adopted; power analysis done (Phase 1b)

**State:** 52 tests passing, ruff clean. Still no results on real events.

**From the ARC-GATE review: adopted**
- Planted-signal simulator, power analysis, stress scenarios, look-ahead canary (`sim/`).
- Adaptive conformal upper bounds alongside static conformal (`metrics/conformal.py`).
- Admissibility invariants I1–I11 on the event table (`events/invariants.py`).
- Champion–challenger promotion after v1 (BUILD.md, Phase 9).
- Rule: no regime feature drives a gate in v1 (enforced by a test).

**Declined:** methods marketplace, RL and recursive self-improvement, domain pivots (earthquakes,
reservoirs, electricity, flu), performative prediction, Lyapunov gating. Reason: scope; v1 is due
2026-12-01.

**Findings (`report/power.md`)**
- The H1 test keeps its false-positive rate at 2–4% under clustering, premium flips, and a 10× outlier.
- ~2,000 usable events over ~140 dates → 81% power for a 5% effect. ~400 events → ~25–35%.
- **Plan change:** 100 names is for the quality test only; the H1 dataset targets ~500 optionable
  names per season (or more seasons via ThetaData Standard back to 2016).
- Adaptive conformal recovered about half the coverage lost to a regime flip within a season.

**Next actions, in order**
1. Daily forward snapshots of names reporting in the next 10 trading days (Nasdaq calendar).
2. Phase 1: prior-art pass → `docs/prior-art.md`.
3. Phase 2: install the ThetaData Terminal; data test; go/stop.

---

## 2026-10-15 — Scaffold complete (Phase 0 done)

**State:** public repo, 2 commits, 43 tests passing, ruff clean. No results yet.

**Decisions made**
- Name: Beyond Implied. Public from day one.
- Question: does a forecast add information about earnings-move *size* beyond the implied move?
  Primary test is encompassing with date-clustered errors on held-out seasons.
- Earnings arena is primary; S&P 500 variance is the control arena (a null is expected there).
- Predict variance, not direction. No trading; forecasting study only.
- v1 scope: earnings only, 3–4 seasons retrospective plus forward Q3 2026, three predictors against
  the trailing/implied ratio baseline, one writeup, by **2026-12-01**.
- Baseline to beat: the trailing/implied ratio (2023 weekly-options study), not the raw implied move.
- Interpretable regression over black boxes; at most 6 features.

**Built**
- Ledger (hash chain; rejects edits, orphan outcomes, predictions written after the event).
- Event math (BMO/AMC alignment, simple and two-expiry implied moves, realized move).
- Metrics (QLIKE, Mincer–Zarnowitz, encompassing, PIT, Kupiec/Christoffersen, risk-coverage,
  P&L shape). Baselines, HAR, regime features, premium features, TOML gate engine.
- CLI: `bi indices`, `bi snapshot`, `bi ledger verify|prereg`.

**Verified against live data**
- VIX history 1990-01-02 to 2026-10-14 (9,294 rows); one flagged jump, 2018-02-05 (real event).
- VVIX: suspicious 2006-03-15 value and 6 gaps; plan to start VVIX in 2007.
- Cboe AAPL chain: 3,508 contracts; per-contract IV is decimal; ATM straddle to the Oct 30 expiry
  implied a 3.8% move at a 5.8% relative spread.

**Not done / open**
- Daily forward snapshots are not yet scheduled (time-sensitive: Q3 season is live).
- ThetaData adapter is an interface stub (needs the Terminal installed on the Mac Mini).
- No CI workflow yet.
- Pre-registration is a draft; freezes in Phase 3.

**Next actions, in order**
1. Start daily `bi snapshot` after the close for names reporting in the next 10 trading days.
2. Phase 1: prior-art pass → `docs/prior-art.md` (≥ 8 entries).
3. Phase 2: data test; go/stop decision against the GOAL.md stop criteria.
