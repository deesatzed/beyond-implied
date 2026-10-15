"""Second-order metrics: is the forecast of move size (variance) right, and does it add information?"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


def qlike(proxy_var, forecast_var, normalized: bool = False) -> float:
    """QLIKE loss (Patton 2011), robust to a noisy variance proxy.

    Default form log(f) + r/f tolerates zero proxies (e.g., a 0% move) and ranks forecasts
    identically to the normalized form r/f - log(r/f) - 1, which needs r > 0.
    """
    r = np.asarray(proxy_var, dtype=float)
    f = np.asarray(forecast_var, dtype=float)
    if np.any(f <= 0):
        raise ValueError("forecast variances must be positive")
    if normalized:
        if np.any(r <= 0):
            raise ValueError("normalized QLIKE needs positive proxies")
        q = r / f
        return float(np.mean(q - np.log(q) - 1.0))
    return float(np.mean(np.log(f) + r / f))


def _ols(y, regressors: dict, cluster=None, hac_lags: int | None = None):
    df = pd.DataFrame({"y": np.asarray(y, dtype=float)})
    for k, v in regressors.items():
        df[k] = np.asarray(v, dtype=float)
    if cluster is not None:
        df["_g"] = np.asarray(cluster)
    df = df.dropna()
    x = sm.add_constant(df[list(regressors)], has_constant="add")
    model = sm.OLS(df["y"], x)
    n_clusters = None
    if cluster is not None:
        groups = pd.factorize(df["_g"])[0]
        res = model.fit(cov_type="cluster", cov_kwds={"groups": groups})
        n_clusters = int(df["_g"].nunique())
    elif hac_lags:
        res = model.fit(cov_type="HAC", cov_kwds={"maxlags": hac_lags})
    else:
        res = model.fit(cov_type="HC1")
    return res, len(df), n_clusters


def mincer_zarnowitz(y, f, cluster=None, hac_lags: int | None = None) -> dict:
    """Regress outcome on forecast; unbiased means intercept 0 and slope 1 (joint Wald test)."""
    res, n, nc = _ols(y, {"f": f}, cluster, hac_lags)
    wald = res.wald_test((np.eye(2), np.array([0.0, 1.0])), use_f=False, scalar=True)
    return {
        "intercept": float(res.params["const"]),
        "slope": float(res.params["f"]),
        "se_intercept": float(res.bse["const"]),
        "se_slope": float(res.bse["f"]),
        "wald_p": float(np.squeeze(wald.pvalue)),
        "r2": float(res.rsquared),
        "n": n,
        "n_clusters": nc,
    }


def encompassing(y, f_model, f_benchmark, cluster=None, hac_lags: int | None = None,
                 alpha: float = 0.05) -> dict:
    """y = a + b_model * f_model + b_bench * f_benchmark + e.

    The model adds information beyond the benchmark if b_model is significantly nonzero.
    """
    res, n, nc = _ols(y, {"model": f_model, "benchmark": f_benchmark}, cluster, hac_lags)
    return {
        "b_model": float(res.params["model"]),
        "se_model": float(res.bse["model"]),
        "p_model": float(res.pvalues["model"]),
        "b_benchmark": float(res.params["benchmark"]),
        "se_benchmark": float(res.bse["benchmark"]),
        "p_benchmark": float(res.pvalues["benchmark"]),
        "adds_information": bool(res.pvalues["model"] < alpha),
        "r2": float(res.rsquared),
        "n": n,
        "n_clusters": nc,
    }
