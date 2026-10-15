"""Build one event row from prices and option chains.

Implied volatility is not in ThetaData's EOD report, so each expiry's ATM volatility is backed out
from the straddle with the Brenner–Subrahmanyam approximation: straddle ≈ √(2/π) · S · σ · √T.
T counts trading days to expiry / 252. These feed the two-expiry event-variance split.
"""

from __future__ import annotations

import datetime as dt
import math

import numpy as np
import pandas as pd

from .invariants import check_event
from .moves import (
    SQRT_2_OVER_PI,
    event_variance_two_expiry,
    expected_abs_move,
    implied_move_simple,
    realized_move,
)
from .straddle import atm_straddle, expiries_after
from .timing import pre_post_dates


def infer_timing(closes: pd.Series, opens: pd.Series, announce: dt.date,
                 min_ratio: float = 1.5) -> tuple[str, float]:
    """BMO if the gap into `announce` dominates, AMC if the gap out of it does; else UNKNOWN.

    gap_bmo = |open(D) / close(D-1) - 1|, gap_amc = |open(D+1) / close(D) - 1|.
    Returns (timing, ratio of the larger gap to the smaller).
    """
    days = list(closes.index)
    ts = pd.Timestamp(announce)
    if ts not in closes.index:
        return "UNKNOWN", math.nan
    i = days.index(ts)
    if i == 0 or i + 1 >= len(days):
        return "UNKNOWN", math.nan
    g_bmo = abs(opens.iloc[i] / closes.iloc[i - 1] - 1.0)
    g_amc = abs(opens.iloc[i + 1] / closes.iloc[i] - 1.0)
    lo, hi = sorted([g_bmo, g_amc])
    lo = max(lo, 0.001)  # a 0.1% floor keeps tiny gaps from producing huge ratios
    ratio = hi / lo
    if ratio < min_ratio:
        return "UNKNOWN", ratio
    return ("BMO" if g_bmo > g_amc else "AMC"), ratio


def straddle_vol(straddle_mid: float, spot: float, t_years: float) -> float:
    return straddle_mid / (SQRT_2_OVER_PI * spot * math.sqrt(t_years))


def _t_years(start, end) -> float:
    n = np.busday_count(pd.Timestamp(start).date(), pd.Timestamp(end).date())
    return max(int(n), 1) / 252.0


def build_event(symbol: str, announce: dt.date, timing: str, ohlc: pd.DataFrame,
                chain: pd.DataFrame, *, timing_source: str = "calendar",
                timing_ratio: float = math.nan, max_days_to_expiry: int = 10) -> dict:
    """Event row with implied and realized moves, straddle P&L, and invariant results.

    `chain` must cover the pre-event and post-event dates (one request from pre to post).
    """
    row: dict = {"symbol": symbol, "announce_date": pd.Timestamp(announce), "timing": timing,
                 "timing_source": timing_source, "timing_ratio": timing_ratio}
    days = [d.date() for d in ohlc.index]
    pre, post = pre_post_dates(announce, timing, days)
    pre_ts, post_ts = pd.Timestamp(pre), pd.Timestamp(post)
    spot = float(ohlc.loc[pre_ts, "close"])
    row.update(pre_date=pre_ts, post_date=post_ts, spot=spot, pre_close=spot,
               post_close=float(ohlc.loc[post_ts, "close"]))
    row["realized_move"] = realized_move(spot, row["post_close"])

    cpre = chain[chain["date"] == pre_ts]
    cpost = chain[chain["date"] == post_ts]
    row["option_volume"] = float(cpre["volume"].sum()) if "volume" in cpre else math.nan
    exps = expiries_after(cpre, post)
    if not exps:
        raise ValueError("no expiry on/after the post-event date in the pre-event chain")
    s1 = atm_straddle(cpre, spot, exps[0])
    row.update(expiry_1=s1["expiry"], strike=s1["strike"], straddle_mid=s1["straddle_mid"],
               rel_spread=s1["rel_spread"], zero_bid=s1["zero_bid"])
    row["implied_move_simple"] = implied_move_simple(s1["straddle_mid"], spot)

    row["event_var"] = math.nan
    row["implied_move_event"] = math.nan
    if len(exps) > 1:
        s2 = atm_straddle(cpre, spot, exps[1])
        t1, t2 = _t_years(pre_ts, exps[0]), _t_years(pre_ts, exps[1])
        if t2 > t1:
            iv1 = straddle_vol(s1["straddle_mid"], spot, t1)
            iv2 = straddle_vol(s2["straddle_mid"], spot, t2)
            ev, _ = event_variance_two_expiry(iv1, t1, iv2, t2)
            row.update(expiry_2=s2["expiry"], iv_1=iv1, iv_2=iv2, event_var=ev,
                       implied_move_event=expected_abs_move(ev))

    # Same straddle one day later: buy at the pre-event ask, sell at the post-event bid.
    row["straddle_ret_mid"] = row["straddle_ret_exec"] = math.nan
    leg = cpost[(cpost["expiry"] == s1["expiry"]) & (cpost["strike"] == s1["strike"])]
    if set(leg["cp"]) == {"C", "P"}:
        post_mid = float(((leg["bid"] + leg["ask"]) / 2).sum())
        post_bid = float(leg["bid"].sum())
        pre_legs = cpre[(cpre["expiry"] == s1["expiry"]) & (cpre["strike"] == s1["strike"])]
        pre_ask = float(pre_legs["ask"].sum())
        row["straddle_ret_mid"] = post_mid / s1["straddle_mid"] - 1.0
        row["straddle_ret_exec"] = post_bid / pre_ask - 1.0 if pre_ask > 0 else math.nan

    issues = check_event(row, max_days_to_expiry)
    row["invariant_errors"] = ";".join(c for c, sev in issues if sev == "error")
    row["invariant_warnings"] = ";".join(c for c, sev in issues if sev == "warning")
    return row


def season_label(ts) -> str:
    t = pd.Timestamp(ts)
    return f"{t.year}Q{(t.month - 1) // 3 + 1}"
