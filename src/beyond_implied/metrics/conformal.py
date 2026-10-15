"""Upper prediction bounds for move size: static online conformal vs adaptive conformal (ACI).

Score: s = realized / forecast. Bound for an event: forecast * q, where q is a quantile of past
scores. ACI (Gibbs & Candès, 2021) adjusts the quantile level after each announcement date:
alpha_{t+1} = alpha_t + gamma * (alpha - breach_rate_t), so coverage recovers after a regime shift.
Breaches (moves above the bound) feed the Kupiec/Christoffersen tests in third_order.py.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _quantile(scores: np.ndarray, level: float) -> float:
    if level >= 1.0:
        return np.inf
    if level <= 0.0:
        return 0.0
    return float(np.quantile(scores, level, method="higher"))


def conformal_upper(y, f, groups, alpha: float = 0.10, gamma: float = 0.0,
                    warmup: int = 100, window: int | None = None) -> pd.DataFrame:
    """Online upper bounds, updated after each group (announcement date).

    gamma = 0 gives static online conformal; gamma > 0 gives ACI.
    Events before `warmup` past scores exist get no bound (NaN) and are excluded from coverage.
    `window` limits the calibration set to the most recent scores.
    """
    y = np.asarray(y, dtype=float)
    f = np.asarray(f, dtype=float)
    g = np.asarray(groups)
    if np.any(np.diff(pd.factorize(g, sort=False)[0]) < 0):
        raise ValueError("rows must be ordered by group (date)")
    bound = np.full(y.size, np.nan)
    alpha_t = np.full(y.size, np.nan)
    a = alpha
    history: list[float] = []
    for key in pd.unique(g):
        idx = np.flatnonzero(g == key)
        calib = np.asarray(history[-window:] if window else history)
        if calib.size >= warmup:
            q = _quantile(calib, 1.0 - a)
            bound[idx] = f[idx] * q
            alpha_t[idx] = a
            breach_rate = float(np.mean(y[idx] > bound[idx]))
            a = a + gamma * (alpha - breach_rate)
        history.extend((y[idx] / f[idx]).tolist())
    out = pd.DataFrame({"bound": bound, "alpha_t": alpha_t})
    out["scored"] = ~np.isnan(bound)
    out["breach"] = np.where(out["scored"], y > np.nan_to_num(bound, nan=np.inf), False)
    return out


def coverage(result: pd.DataFrame) -> float:
    s = result[result["scored"]]
    return float(1.0 - s["breach"].mean()) if len(s) else float("nan")
