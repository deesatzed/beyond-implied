# Beyond Implied

**Does a forecast add information beyond what the options market already priced?**

Beyond Implied tests one claim in public: a forecasting scaffold can carry statistically significant
information about the *size* of stock moves beyond the option market's own forecast (implied volatility),
and it can tell when to abstain. It predicts variance, not direction, and every prediction is written
to a hash-chained ledger before its outcome exists.

> **Status (2026-10-16): data test passed; pre-registration not yet frozen.** No forecast has been
> evaluated. What exists so far is the data pipeline, a data-quality check, and a power analysis.
> This is a forecasting study. It places no trades and is not investment advice.

## Where it stands

| | |
| --- | --- |
| Phase 2 data test | **Go**, with one criterion marginally missed ([report/data_test.md](report/data_test.md)) |
| Events (100 large-cap names, 13 seasons since mid-2023) | 1,307 announcements; 1,086 usable |
| Report timing without looking at the outcome | 99 of 100 names; the implied-volatility-collapse rule agrees with known timing on 96.1% of events ([report/timing_iv.md](report/timing_iv.md)) |
| Unusable share | 16.9% against a 15% criterion, mostly straddle spreads wider than 25%; recorded as a miss, not redefined |
| Power for the primary test | 93% at a 5% effect with 500 names × 13 seasons ([report/power.md](report/power.md)) |
| Forward collection | Option snapshots every trading day after the close since 2026-10-15 |

Early descriptive picture, not a test of anything: large-cap implied moves were close to fair on
average (realized/implied ≈ 1.0), seasons swung between 0.70 and 1.23, and a one-day straddle bought
at the ask and sold at the bid lost money in most seasons.

**Next:** expand to ~500 names, freeze the pre-registration (tag `prereg-v1`), then run baselines on
training seasons and evaluate once on held-out seasons. Target for v1: 2026-12-01.
Progress is logged in [CHECKPOINTS.md](CHECKPOINTS.md); the plan with gates is [BUILD.md](BUILD.md).

## Why this question

The option market publishes a forecast every day: the at-the-money straddle before an earnings report
prices an expected move. That forecast is biased and wrong daily, yet it is the accepted incumbent.
The fair test of any model is not "is it right?" but "does it add information the incumbent didn't have?"
That is the encompassing test, and it is the same question as whether a clinical model adds information
beyond the clinician.

Earnings events make the test practical: hundreds of mostly independent events per season, and ground
truth within a day.

## Two arenas

| Arena | Role | Benchmark | Resolves in |
| --- | --- | --- | --- |
| Earnings moves | Primary | Implied move from the pre-event straddle; trailing-move / implied ratio | 1 day |
| Index variance (S&P 500) | Control | VIX and HAR-IV | 30 days |

## Layout

```
GOAL.md               the claim, success and stop criteria
BUILD.md              ordered build phases with gates
PREREGISTRATION.md    hypotheses, metrics, splits (frozen before evaluation)
config/               universe filters and expert-system gate rules
src/beyond_implied/
  data/         sources: Cboe index history, option chains, earnings calendar, quality flags
  events/       earnings event table: timing, implied move, realized move
  forecasters/  baselines and model forecasts (trailing move, ratio, HAR)
  regime/       chaos/entropy features (permutation entropy, DFA Hurst, recurrence)
  premium/      game-theory features: sign of the variance risk premium
  gates/        expert-system rule layer: commit or abstain, with rule IDs logged
  metrics/      second-order, third-order and decision-level scoring
  ledger/       append-only, hash-chained prediction ledger
  sim/          planted-signal simulations, power analysis, look-ahead canary
  challengers/  Phase 9 challengers (C1: AI-elicited probabilistic network, spec only)
report/         power analysis, figures and the writeup
docs/           plan and risk analysis
tests/
```

Each section has its own `GOAL.md` with purpose, inputs, outputs, build steps and a "done when" list.

## Quick start

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
make test
bi indices VIX VIX3M VVIX SKEW        # download Cboe daily index history
bi snapshot AAPL MSFT                 # save today's delayed option chains (raw JSON + hash)
bi daily                              # after the close: chains for names with a pre/post-event close today
bi calendar 2026-10-16                # earnings calendar for a date (Nasdaq)
bi theta-probe AAPL 2026-07-30        # ThetaData smoke test (needs THETA_DATA_API_KEY in .env)
bi timing-iv --names 100              # IV-collapse report timing, validated against known timing
bi phase2 --names 100                 # build the event table and report/data_test.md
bi power                              # simulation power analysis for the primary test
bi power-real                         # power using parameters estimated from the real events
bi status                             # run status for the monitoring dashboard
bi ledger verify ledger/predictions.jsonl
```

## Data sources

Cboe daily index history and delayed option chains (unofficial public endpoints; check terms),
ThetaData end-of-day option history (free tier, back to mid-2023; the license is for individual use, so
this repo publishes derived statistics only, never raw vendor data), the Nasdaq earnings calendar
(past dates carry no before-open/after-close flag, hence the timing rules above), and FOMC and CPI
dates from the Federal Reserve and BLS. See `docs/risks-and-data.md`.

## License

MIT for the code. Data belongs to its providers and is not redistributed here.
