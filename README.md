# Beyond Implied

**Does a forecast add information beyond what the options market already priced?**

Beyond Implied tests one claim in public: a forecasting scaffold can carry statistically significant
information about the *size* of stock moves beyond the option market's own forecast (implied volatility),
and it can tell when to abstain. It predicts variance, not direction, and every prediction is written
to a hash-chained ledger before its outcome exists.

> **Status: scaffold.** No results yet. The data test (BUILD.md, Phase 2) decides whether this gets built further.
> This is a forecasting study. It places no trades and is not investment advice.

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
bi ledger verify ledger/predictions.jsonl
```

## Data sources

Cboe daily index history and delayed option chains (unofficial public endpoints; check terms),
ThetaData end-of-day option history (free tier: one year; retail license is individual use, so this
repo publishes derived statistics only, never raw vendor data), and an earnings calendar with a
before-open/after-close flag on every event. See `docs/risks-and-data.md`.

## License

MIT for the code. Data belongs to its providers and is not redistributed here.
