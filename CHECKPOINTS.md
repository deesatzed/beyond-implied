# Checkpoints

Newest first. Each checkpoint has a matching git tag `checkpoint-YYYY-MM-DD`.

---

## 2026-10-17 — 500-name pull: one gate criterion clearly missed

- Overnight run (Fri 16:35 to Sat 02:51 ET): 6,390 announcements, 6,010 events built, **4,148 usable**
  over 556 dates. That is about twice the power target.
- Timing scales: 484 of 500 names covered; IV rule 93.8% agreement (96.1% at 100 names).
- **Unusable share 35.1%, failing the 10–15% criterion.** Label-quality failures are only 5.9%; the
  rest is the pre-registered liquidity rules (spread > 25%, volume < 300), concentrated in smaller
  names. Not redefined; three options are set out in `report/data_test.md` for a decision before the
  freeze.
- At 500 names, realized moves fell short of implied in every season (0.73–0.99), and the executable
  one-day straddle lost money in every season.
- ORATS Jan–Feb 2026 mismatch persists at 500 names (−1.9% vs ≈ +45%); likely a definitional
  difference, not yet confirmed.
- Daily snapshot Fri: 13 of 14 names (PAC has no Cboe chain). Dashboard refresh moved into this
  session after the scheduled-task version failed silently.

- Real-data power at 500 names: 87% at a 5% effect over 13 seasons (false positives 3%); about 40%
  over 4 seasons. The earlier 93% assumed 5× the events per date. A first rerun repeated that
  scaling by mistake; it was caught and discarded.

**Decisions needed before Phase 3:** the population definition (option 1, 2 or 3); the held-out
design (rolling-origin over all seasons, or a small held-out set with low power); how the ORATS gap
is resolved.

---

## 2026-10-16 (morning) — Timing fixed; 100-name rebuild; C1 and G8 added

- IV-collapse timing validated (96.1% agreement on 763 reference events, 94.5% classified; flat
  across thresholds) and pre-registered as the fallback timing source.
- Rebuild: 99 of 100 names timed outcome-free; 1,233 events built, 1,086 usable. Unusable share
  16.9% (74 untimed, 140 spread > 25%): a marginal miss of the 10–15% criterion, recorded, not
  redefined. Sample is ~5× the power target when projected to 500 names.
- Findings unchanged with twice the events: large-cap implied moves close to fair over 13 seasons;
  executable one-day straddles lose in most seasons; regimes rotate (0.70–1.23).
- Gate G8 (FOMC/CPI in the event window; dates from the Fed and BLS) added; 110 events affected.
- Phase 9 challenger C1 (AI-elicited probabilistic network) specified: GOAL.md, spec format,
  validator. Not part of v1.
- Process fix: commits now gate on pytest's real exit code (one failing test slipped into 4d211dc;
  fixed in e87f8ee).

**Next:** daily snapshot check 16:35; 500-name pull overnight (timing, then events); Saturday review;
Phase 3 freeze early next week.

---

## 2026-10-16 — Phase 2 data test: conditional GO

- Full run: 100 names, 13 seasons, 850 calendar days complete, 1,307 announcements.
- First run failed the gate and exposed a real bias: timing chosen by the larger overnight gap selects
  on the outcome (wrong on ~21% of events). Replaced with each company's habitual BMO/AMC (10/10 on
  recorded checks). Spread cut for the forecasting sample relaxed to 25% (P&L keeps 10%).
- With outcome-free timing: 665 of 763 events usable (12.8% unusable). Large-cap implied moves are
  close to fair over 13 seasons (realized/implied ≈ 1.0); executable one-day straddles lose in most
  seasons; seasons swing 0.73–1.23.
- Real-data power (500 names, 13 seasons, trailing control): 93% at a 5% effect; false positives 2–3%.
- Blocker for Phase 3: timing covers 59/100 names. Plan: daily recording + an implied-volatility-
  collapse timing rule, validated on covered names; freeze when ≥ 85% of names are covered.
- Pipeline fixes: ThetaData 365-day limit and future dates, Nasdaq rate limits with backoff, cache
  sidecar bug, mixed timestamp formats.

**Next actions**
1. Implement and validate the IV-collapse timing rule; rebuild.
2. Expand the universe toward 500 names (overnight pulls).
3. Re-check ORATS once smaller names are included; then Phase 3 freeze.

---

## 2026-10-15 (late) — ThetaData connected; secrets locked down

- `.env` (ThetaData and OpenRouter keys) is gitignored, untracked, never committed, and set to
  owner-only permissions on the Mac. `.env.example` lists the names.
- ThetaData adapter works through the official Python library (no Terminal, no Java). Probe on
  AAPL 2026-07-30: 1,442 contracts; ATM straddle to the Jul 31 expiry implied a 3.79% move at a
  5.9% relative spread.
- Free history reaches back to mid-2023 (2023-10-26 served; 2022-10-27 refused). About 13 seasons
  are available, so the ~2,000-event power target is reachable without a paid tier.
- OpenRouter key: not used in v1. Possible Phase 9 challenger (an LLM forecast tested under the
  same encompassing rules).

**Next:** Phase 2 event-table pipeline, then the 100-name data test, running overnight on the Mac.

---

## 2026-10-15 (night) — Daily collection live; prior art done (Phase 1)

**State:** 56 tests passing. Forward data collection running on the Mac Mini.

**Daily collection**
- `bi daily` + launchd job `com.deesatzed.beyond-implied.daily`, 16:25 New York, Mon–Fri, from
  `~/Projects/beyond-implied` on the Mac Mini. Each run pulls the latest code first.
- External drive rejected: macOS blocks background jobs from reading `/Volumes/WS4TB` without a
  Full Disk Access grant. A clone remains at `/Volumes/WS4TB/beyond-implied` (unused).
- First day, 2026-10-15: 27 of 27 selected names captured (pre/post-event closes, ≥ $2B), via a
  launchd-triggered run that exited 0. Raw data and logs stay out of git.

**Prior art (`docs/prior-art.md`, 13 entries)**
- H1 narrowed: trailing earnings moves are already known to add information beyond the implied
  move, so the benchmark is now implied move + trailing move (`encompassing(..., controls=)`).
- The option market is reported to forecast event magnitude well; a null on H1 is plausible.
- Literature-backed features proposed for the 6-slot budget: past-move kurtosis/jump frequency,
  analyst count, market cap, VIX/VIX3M, plus at most one regime feature.
- Nasdaq's past calendar has dates, EPS, surprise and analyst count but no timing flag; timing for
  retrospective seasons will be inferred from overnight gaps and validated on forward events.

**Next actions, in order**
1. Watch the first unattended run (Fri 2026-10-16, 16:25) and its log.
2. Phase 2: install the ThetaData Terminal on the Mac Mini (needs your account); data test.
3. Re-run `bi power` with the three-regressor benchmark and real-data parameters.

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
