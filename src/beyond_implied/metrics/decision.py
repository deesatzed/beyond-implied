"""Decision-level metrics: risk at coverage, and the shape of hypothetical straddle P&L."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy import stats


def risk_coverage(confidence, loss) -> pd.DataFrame:
    """Mean loss over the k most confident cases, for k = 1..n."""
    c = np.asarray(confidence, dtype=float)
    l_ = np.asarray(loss, dtype=float)
    order = np.argsort(-c, kind="stable")
    k = np.arange(1, c.size + 1)
    return pd.DataFrame({"coverage": k / c.size, "risk": np.cumsum(l_[order]) / k})


def aurc(confidence, loss) -> float:
    """Area under the risk-coverage curve (lower is better)."""
    return float(risk_coverage(confidence, loss)["risk"].mean())


def risk_at_coverage(confidence, loss, coverage: float) -> float:
    rc = risk_coverage(confidence, loss)
    k = max(1, math.ceil(coverage * len(rc)))
    return float(rc["risk"].iloc[k - 1])


def straddle_pnl(realized_move, implied_move, half_spread_rel: float = 0.0):
    """Long ATM straddle held to expiry, per unit of spot: |move| minus cost paid at the ask.

    Approximation: ignores residual time value when expiry is later than the post-event close.
    """
    return np.asarray(realized_move, dtype=float) - np.asarray(implied_move, dtype=float) * (
        1.0 + half_spread_rel
    )


def pnl_shape(pnl, alpha: float = 0.01) -> dict:
    """Judge a P&L stream by its shape: skew, expected shortfall, drawdown, not mean or Sharpe."""
    x = np.asarray(pnl, dtype=float)
    x = x[~np.isnan(x)]
    k = max(1, math.ceil(alpha * x.size))
    cum = np.concatenate([[0.0], np.cumsum(x)])
    drawdown = cum - np.maximum.accumulate(cum)
    return {
        "n": int(x.size),
        "mean": float(x.mean()),
        "median": float(np.median(x)),
        "std": float(x.std(ddof=1)) if x.size > 1 else float("nan"),
        "skew": float(stats.skew(x)) if x.size > 2 else float("nan"),
        "expected_shortfall": float(np.sort(x)[:k].mean()),
        "worst": float(x.min()),
        "max_drawdown": float(-drawdown.min()),
        "hit_rate": float((x > 0).mean()),
    }
