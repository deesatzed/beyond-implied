"""Admissibility checks on the event table. Errors exclude a row; warnings are reported and kept.

Every check has an ID so the data-test report can count failures by reason.
"""

from __future__ import annotations

import math

import pandas as pd

ERROR, WARNING = "error", "warning"


def _val(row, name):
    v = row.get(name)
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return v


def check_event(row: dict, max_days_to_expiry: int = 10) -> list[tuple[str, str]]:
    """Return [(check_id, severity)] for one event row (dict or Series)."""
    out: list[tuple[str, str]] = []
    timing = _val(row, "timing")
    if timing not in ("BMO", "AMC"):
        out.append(("I1-timing", ERROR))
    pre, post, exp1 = (_val(row, k) for k in ("pre_date", "post_date", "expiry_1"))
    if pre is not None and post is not None and not pd.Timestamp(pre) < pd.Timestamp(post):
        out.append(("I2-pre-before-post", ERROR))
    if exp1 is not None and post is not None:
        gap = (pd.Timestamp(exp1) - pd.Timestamp(post)).days
        if gap < 0:
            out.append(("I3-expiry-before-post", ERROR))
        elif gap > max_days_to_expiry:
            out.append(("I4-expiry-too-far", WARNING))
    for col, cid in (("spot", "I5-spot-positive"), ("straddle_mid", "I6-straddle-positive"),
                     ("pre_close", "I7-pre-close-positive")):
        v = _val(row, col)
        if v is not None and not v > 0:
            out.append((cid, ERROR))
    im = _val(row, "implied_move_simple")
    if im is not None and not 0.0 < im < 1.0:
        out.append(("I8-implied-move-range", ERROR))
    rm = _val(row, "realized_move")
    if rm is not None and rm < 0:
        out.append(("I9-realized-nonnegative", ERROR))
    rs = _val(row, "rel_spread")
    if rs is not None and rs < 0:
        out.append(("I10-spread-nonnegative", ERROR))
    ev = _val(row, "event_var")
    if ev is not None and ev < 0:
        out.append(("I11-event-variance-negative", WARNING))
    return out


def check_events(events: pd.DataFrame, max_days_to_expiry: int = 10) -> pd.DataFrame:
    """One row per violation: index, check_id, severity. Empty frame means all rows pass."""
    rows = []
    for idx, row in events.iterrows():
        for cid, sev in check_event(row.to_dict(), max_days_to_expiry):
            rows.append({"index": idx, "check_id": cid, "severity": sev})
    return pd.DataFrame(rows, columns=["index", "check_id", "severity"])
