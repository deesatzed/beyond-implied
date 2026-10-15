# Plan — Second-Order Forecasting Lab

*Source: "Second-Order Forecasting Lab" Claude Doc, 2026-10-15.*

## The reframe

Predict the size and shape of moves, not their direction, and grade the forecast's distribution and the
decision it drives rather than a point estimate. "2nd and 3rd principles" is read as second- and
third-order quantities.

Direction (first order) is close to efficient, so a direction model competes with everyone. **Variance is
predictable.** Volatility clustering and long memory are among the most robust regularities in finance,
and direction has nothing comparable. The benchmark is built in, because the options market publishes its
own forecast: implied volatility.

A straddle is a pure bet on one thing. A delta-hedged straddle's P&L is roughly gamma times the gap between
realized and implied variance. So "will this straddle pay?" means "will realized variance exceed what the
market priced?" That is a second-order prediction against a threshold the market sets.

| Order | What you predict | The market's own forecast (benchmark) | Instrument | Resolves in |
| --- | --- | --- | --- | --- |
| 1st | Direction, level | Price, forward | Stock, futures | Skip |
| 2nd | Magnitude, variance | Implied vol: VIX, earnings implied move | Straddle, variance swap | 1 day (earnings) to 30 days (index) |
| 2nd of 2nd | Variability of variance | VVIX | VIX options | 30 days |
| 3rd | Asymmetry, tails | Cboe SKEW, put skew | Risk reversal, OTM puts | Rare; needs proper scoring rules |

## Two arenas

**Earnings straddles (flagship).** The implied move is the at-the-money straddle price the day before the
report; the realized move arrives the next day. Each season has hundreds of liquid names, events are mostly
independent, and ground truth comes in 24 hours.

**Index variance (retrospective, control).** Free daily Cboe history for VIX, VIX3M, VVIX and SKEW plus SPX
OHLC. Forecast 30-day realized variance against VIX and HAR-RV. Black swans with known dates: 2008,
August 2015, February 2018, March 2020, August 2024. Daily 30-day forecasts overlap, so the effective N is a
few hundred months; use HAC standard errors.

## Where the five pieces fit

- **Time series:** HAR-RV, GARCH-family models, range estimators (Garman–Klass).
- **Chaos/entropy:** permutation entropy, Hurst exponent, recurrence rate as regime features. Hypothesis:
  a loss of complexity precedes variance expansion.
- **Game theory:** implied vol is an equilibrium price between hedgers buying insurance and sellers
  collecting premium, which is why implied usually exceeds realized. Straddles pay when that equilibrium
  breaks. Proxies: VIX/VIX3M inversion, VVIX level. Target: the sign of the premium.
- **Expert system:** a rule layer with the event calendar and regime gates that decides commit or abstain,
  frozen before evaluation.
- **Decision model:** commit or abstain, scored on risk at coverage.

## Metrics by order

**Second order:** QLIKE; Mincer–Zarnowitz; encompassing regression (the core claim); Model Confidence Set.

**Third order:** PIT histograms and CRPS/log score; Christoffersen conditional coverage at 1% and 5%;
predicted vol-of-vol against realized error dispersion.

**Decision level:** hypothetical straddle P&L net of realistic spreads, judged by distribution shape
(skew, worst 1%, max drawdown), not mean or Sharpe.

## Why this answers the fairness objection

The model needs statistically significant information beyond an incumbent forecast that is itself biased
and wrong every day. That is the same question as whether a clinical model adds information beyond the
clinician, shown here on thousands of cases with one-day feedback.

## Cautions

- Forecasting study only; no live trades; not financial advice.
- Treat the third-order layer as tail calibration, not crash prediction.
