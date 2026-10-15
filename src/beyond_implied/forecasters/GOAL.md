# GOAL — forecasters

## Purpose

Produce, for every event (and every month in the index arena), a forecast of move size made only
from information available before the event. The baselines are the bar; the scaffold forecast must
beat them on held-out data.

## Inputs

- Event table (`events/`) with realized moves of past events.
- Implied moves at the pre-event close.
- Regime and premium features (`regime/`, `premium/`).
- For the index arena: SPX daily OHLC, VIX.

## Outputs

Per event: `f_implied`, `f_trailing`, `ratio`, `f_model`, and a confidence score used by `gates/`
and the risk-coverage curve. Per month (index arena): HAR-RV and HAR-IV forecasts of 21-day variance.

## Baselines (fixed in PREREGISTRATION.md)

1. Implied move (the incumbent).
2. Trailing mean absolute move over the previous 12 events of the same symbol (min 4).
3. Trailing / implied ratio, the known predictor from the 2023 weekly-options study.
4. HAR-RV and HAR-IV (index arena).

## Built in the scaffold

- `baselines.py`: `trailing_mean_abs_move` (strictly prior events only), `trailing_to_implied_ratio`.
- `har.py`: Garman–Klass daily variance, HAR design matrix, h-day target, OLS fit with HAC errors.

## Build steps

1. Phase 4: compute baselines on all events; verify no look-ahead with a test that shuffles future rows.
2. Phase 4: reproduce the ratio effect (direction only) before adding anything.
3. Phase 5: scaffold model = a small, interpretable regression of log realized move on
   log implied, log trailing, and at most 4 regime/premium features, fit on training seasons only.
   Prefer this over a black box: the claim is information content, not accuracy.
4. Phase 5: confidence score = predicted |log(f_model / f_implied)| or a calibrated interval width;
   fix the definition in the pre-registration.
5. Phase 7: HAR-RV and HAR-IV on non-overlapping 21-day windows.

## Done when

- [ ] Baselines computed with a passing no-look-ahead test.
- [ ] Ratio effect reproduced in direction on training seasons.
- [ ] Scaffold model fit once on training seasons; coefficients logged.

## Pitfalls

- Look-ahead through rolling windows that include the current event.
- Fitting anything on held-out seasons, even "just to check".
- Feature creep: each added feature spends statistical power.
