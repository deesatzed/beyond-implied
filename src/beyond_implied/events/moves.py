"""Implied and realized earnings moves."""

from __future__ import annotations

import math

SQRT_2_OVER_PI = math.sqrt(2.0 / math.pi)


def implied_move_simple(straddle_mid: float, spot: float) -> float:
    """ATM straddle mid / spot: the market's expected absolute move to expiry (approx.)."""
    if spot <= 0:
        raise ValueError("spot must be positive")
    return straddle_mid / spot


def event_variance_two_expiry(iv1: float, t1: float, iv2: float, t2: float) -> tuple[float, float]:
    """Split total implied variance into an event jump and a base diffusion rate.

    Both expiries must be after the event, with t2 > t1 (years). Total variance
    w_i = iv_i^2 * t_i = base_rate * t_i + event_var. Returns (event_var, base_rate).
    A negative event_var means the term structure is inconsistent with an event premium; flag it.
    """
    if not t2 > t1 > 0:
        raise ValueError("need 0 < t1 < t2")
    w1, w2 = iv1 * iv1 * t1, iv2 * iv2 * t2
    base_rate = (w2 - w1) / (t2 - t1)
    return w1 - base_rate * t1, base_rate


def expected_abs_move(event_var: float) -> float:
    """E|move| under a normal jump with variance event_var; NaN if event_var <= 0."""
    if not event_var > 0:
        return math.nan
    return SQRT_2_OVER_PI * math.sqrt(event_var)


def realized_move(pre_close: float, post_close: float) -> float:
    if pre_close <= 0:
        raise ValueError("pre_close must be positive")
    return abs(post_close / pre_close - 1.0)
