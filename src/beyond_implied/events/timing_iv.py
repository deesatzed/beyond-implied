"""Outcome-free announcement timing from the collapse of front-expiry implied volatility.

Earnings uncertainty leaves option prices at the first close after the announcement, whether or
not the stock moves much. For a report dated D, compare ATM implied volatility of one fixed expiry
(the first expiry after D+1) at three closes:

    drop_bmo = iv(D-1) - iv(D)      collapse into D's close  -> before-open report
    drop_amc = iv(D)   - iv(D+1)    collapse into D+1's close -> after-close report

ATM is re-centred on each day's close so the measure tracks volatility, not moneyness.
The rule never looks at the size or sign of the stock move. Validated against recorded or habitual
timing before use (BUILD.md, Phase 2).
"""

from __future__ import annotations

import datetime as dt
import math

import numpy as np
import pandas as pd

from .build import straddle_vol
from .straddle import atm_straddle


def _t_years(day, expiry) -> float:
    n = np.busday_count(pd.Timestamp(day).date(), pd.Timestamp(expiry).date())
    return max(int(n), 1) / 252.0


def atm_vol(chain_day: pd.DataFrame, spot: float, expiry, day) -> float:
    s = atm_straddle(chain_day, spot, expiry)
    if s["zero_bid"] or s["straddle_mid"] <= 0:
        return math.nan
    return straddle_vol(s["straddle_mid"], spot, _t_years(day, expiry))


def iv_collapse_timing(chain: pd.DataFrame, closes: pd.Series, announce: dt.date,
                       min_ratio: float = 1.5, min_drop: float = 0.02) -> dict:
    """Return {'timing', 'drop_bmo', 'drop_amc', 'ratio'}; timing is BMO, AMC or UNKNOWN.

    `min_drop` is the smallest collapse (in annualised vol units) that counts as an event.
    `chain` must cover the closes of D-1, D and D+1 (trading days); `closes` is the stock's
    daily close series indexed by date.
    """
    out = {"timing": "UNKNOWN", "drop_bmo": math.nan, "drop_amc": math.nan, "ratio": math.nan}
    days = list(closes.index)
    ts = pd.Timestamp(announce)
    if ts not in closes.index:
        return out
    i = days.index(ts)
    if i == 0 or i + 1 >= len(days):
        return out
    d0, d1, d2 = days[i - 1], days[i], days[i + 1]
    exps = sorted(e for e in chain["expiry"].unique() if pd.Timestamp(e) > d2)
    if not exps:
        return out
    expiry = pd.Timestamp(exps[0])
    try:
        ivs = [atm_vol(chain[chain["date"] == d], float(closes.loc[d]), expiry, d) for d in (d0, d1, d2)]
    except (ValueError, KeyError):
        return out
    if any(math.isnan(v) for v in ivs):
        return out
    drop_bmo, drop_amc = ivs[0] - ivs[1], ivs[1] - ivs[2]
    out.update(drop_bmo=drop_bmo, drop_amc=drop_amc)
    hi, lo = max(drop_bmo, drop_amc), min(drop_bmo, drop_amc)
    if hi < min_drop:  # no collapse of at least 2 vol points: not identifiable
        return out
    ratio = hi / max(lo, 0.002) if lo > 0 else math.inf
    out["ratio"] = ratio
    if ratio >= min_ratio:
        out["timing"] = "BMO" if drop_bmo > drop_amc else "AMC"
    return out
