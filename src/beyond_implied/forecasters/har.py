"""HAR-RV / HAR-IV for the index control arena (Corsi 2009)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


def garman_klass_variance(ohlc: pd.DataFrame) -> pd.Series:
    """Daily Garman–Klass variance from open/high/low/close columns."""
    hl = np.log(ohlc["high"] / ohlc["low"])
    co = np.log(ohlc["close"] / ohlc["open"])
    return 0.5 * hl**2 - (2.0 * np.log(2.0) - 1.0) * co**2


def har_design(rv: pd.Series, extra: pd.DataFrame | None = None) -> pd.DataFrame:
    """Daily, weekly (5) and monthly (22) averages of past realized variance, plus extras."""
    x = pd.DataFrame({
        "rv_d": rv,
        "rv_w": rv.rolling(5).mean(),
        "rv_m": rv.rolling(22).mean(),
    })
    if extra is not None:
        x = x.join(extra, how="left")
    return x


def har_target(rv: pd.Series, horizon: int = 21) -> pd.Series:
    """Mean realized variance over the next `horizon` days (t+1 .. t+horizon)."""
    return rv.rolling(horizon).mean().shift(-horizon)


def fit_har(rv: pd.Series, horizon: int = 21, extra: pd.DataFrame | None = None,
            step: int | None = None):
    """OLS fit with HAC errors. `step=horizon` uses non-overlapping observations."""
    x = har_design(rv, extra)
    y = har_target(rv, horizon).rename("target")
    df = x.join(y).dropna()
    if step:
        df = df.iloc[::step]
    model = sm.OLS(df["target"], sm.add_constant(df.drop(columns="target")))
    lags = 0 if step and step >= horizon else horizon
    return model.fit(cov_type="HAC", cov_kwds={"maxlags": lags}) if lags else model.fit(cov_type="HC1")
