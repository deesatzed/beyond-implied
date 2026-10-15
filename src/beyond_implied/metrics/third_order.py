"""Third-order metrics: calibration of the whole predictive distribution and of its tails."""

from __future__ import annotations

import numpy as np
from scipy import stats
from scipy.special import xlogy


def pit_uniformity(pit, bins: int = 10) -> dict:
    """Probability integral transform values should be Uniform(0, 1) if the forecast is calibrated."""
    u = np.asarray(pit, dtype=float)
    u = u[~np.isnan(u)]
    ks = stats.kstest(u, "uniform")
    counts, _ = np.histogram(u, bins=bins, range=(0.0, 1.0))
    return {"ks_stat": float(ks.statistic), "ks_p": float(ks.pvalue), "counts": counts.tolist(),
            "n": int(u.size)}


def kupiec(hits, alpha: float) -> dict:
    """Unconditional coverage: do breaches occur at rate alpha? (LR, chi-square 1 df)."""
    h = np.asarray(hits, dtype=bool)
    n, x = h.size, int(h.sum())
    ll_null = xlogy(n - x, 1 - alpha) + xlogy(x, alpha)
    ll_alt = xlogy(n - x, 1 - x / n) + xlogy(x, x / n)
    lr = -2.0 * (ll_null - ll_alt)
    return {"lr_uc": float(lr), "p_uc": float(stats.chi2.sf(lr, 1)), "breaches": x, "n": n,
            "rate": x / n if n else float("nan")}


def christoffersen(hits, alpha: float) -> dict:
    """Conditional coverage = unconditional coverage + independence of consecutive breaches."""
    h = np.asarray(hits, dtype=int)
    uc = kupiec(h.astype(bool), alpha)
    prev, curr = h[:-1], h[1:]
    n00 = int(((prev == 0) & (curr == 0)).sum())
    n01 = int(((prev == 0) & (curr == 1)).sum())
    n10 = int(((prev == 1) & (curr == 0)).sum())
    n11 = int(((prev == 1) & (curr == 1)).sum())
    pi01 = n01 / (n00 + n01) if (n00 + n01) else 0.0
    pi11 = n11 / (n10 + n11) if (n10 + n11) else 0.0
    pi = (n01 + n11) / (n00 + n01 + n10 + n11) if (n00 + n01 + n10 + n11) else 0.0
    ll_null = xlogy(n00 + n10, 1 - pi) + xlogy(n01 + n11, pi)
    ll_alt = xlogy(n00, 1 - pi01) + xlogy(n01, pi01) + xlogy(n10, 1 - pi11) + xlogy(n11, pi11)
    lr_ind = float(-2.0 * (ll_null - ll_alt))
    lr_cc = uc["lr_uc"] + lr_ind
    return {**uc, "lr_ind": lr_ind, "p_ind": float(stats.chi2.sf(lr_ind, 1)),
            "lr_cc": lr_cc, "p_cc": float(stats.chi2.sf(lr_cc, 2))}
