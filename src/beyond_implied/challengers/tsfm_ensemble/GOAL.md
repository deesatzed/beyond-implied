# GOAL — Challenger C2: time-series foundation-model (TSFM) ensemble

Status: **specified, not built.** Added 2026-10-18. Runs on the non-earnings ETF panel (C1's secondary
unit) and the index control arena (BUILD.md, Phase 7). Not used for one-day earnings moves: a TSFM
forecasts a daily volatility series, while an earnings move is a scheduled jump that the series does
not contain.

## Question

Does a pool of zero-shot TSFMs, combined by a context-dependent meta-learner, forecast 21-day
realized volatility better than Log-HAR and the option market's implied volatility? And does C1's
open-world ESS add information beyond that pool?

## Why it belongs here

- **The ensembles are real and lead general benchmarks.** Toto 2.0 FnF ranks #1 on GIFT-Eval with
  per-window softmax weights; on average the Toto family takes 39% of the weight and Chronos-2 32%.
  CastStar pools Chronos-2, TimesFM-2.5, FlowState, TiRex, PatchTST-FM and Toto-2.0-2.5B. Synapse
  (TMLR 2026) weights TSFMs by recent, context-dependent performance.
- **GIFT-Eval wins do not transfer automatically to volatility.** In a 2026 study, zero-shot TSFMs
  were compared with eight econometric models on realized volatility for 50 assets (Brini, arXiv
  2607.05291). Only TTM beat Log-HAR at every horizon, by about 1.3–1.8%, and at the daily horizon
  that gain was mostly calibration. An equal-weight TTM + Log-HAR average was in the model
  confidence set for 98–100% of assets.

So the base case is a small gain at best, and the combination is the strongest candidate.

## Design

- **Target:** realized volatility over the next 21 trading days, from daily OHLC (Garman–Klass).
  This is a daily-range proxy, named as such and not compared with 5-minute-RV results.
- **Pool:**
  - TTM, Chronos-2, TimesFM 2.5, TiRex and a small Toto 2.0, all zero-shot, run locally on the Mac;
  - Log-HAR and HAR as the econometric members;
  - 30-day implied volatility as a member, not only as the benchmark.
- **Combinations, each pre-registered:**
  - equal-weight TTM + Log-HAR (the published strong baseline);
  - an FFORMA-style meta-learner: gradient boosting on series features (recent volatility level and
    trend, autocorrelation, implied/realized ratio, VIX regime) producing softmax weights.
- **Fitting:** the meta-learner is fit walk-forward only, on matured past forecasts.
- **Scoring:** QLIKE (primary), quantile loss where members give quantiles, Mincer–Zarnowitz, and
  Diebold–Mariano tests against Log-HAR and against implied volatility, clustered by week.
- **C1 link:** C1-open's panel forecasts are scored with the C2 ensemble as a control. The claim
  "outside-the-market factors add information" has to beat this pool, not only implied volatility.

## Contamination and licenses

- TSFM pretraining corpora may include 2023–2026 market series. Retrospective panel results are
  therefore exploratory; the confirmatory score is forward only, sealed in the ledger at each origin.
- Model checkpoints and versions are pinned and their licenses recorded. This is non-commercial
  public research. Some weights (TimesFM 3.0, some Moirai 2.0 releases) are non-commercial and would
  need re-checking for any other use.

## Build steps

1. Adapters that keep each model's full quantile output and report the actual model used on fallback.
2. Origin-indexed replay harness: the context ends at the origin, and the target starts the next
   session. Tested with the look-ahead canary.
3. Log-HAR and HAR baselines, plus the equal-weight combination.
4. Meta-learner, walk-forward.
5. Freeze with v1 and C1; seal weekly forecasts forward.

## Done when

- [ ] Pool, combination rules and panel list are frozen and hashed in the ledger.
- [ ] Weekly forecasts are sealed forward, each before its window opens.
- [ ] The result is published against Log-HAR and implied volatility, whatever it is.
