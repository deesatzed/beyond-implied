"""ATM straddle selection from a parsed chain (columns as in data.cboe_options.parse_chain)."""

from __future__ import annotations

import datetime as dt

import pandas as pd

from ..data.quality import straddle_quote_flags


def expiries_after(chain: pd.DataFrame, date: dt.date, n: int = 2) -> list[pd.Timestamp]:
    """First `n` expiries on or after `date`."""
    exp = sorted(e for e in chain["expiry"].unique() if pd.Timestamp(e).date() >= date)
    return [pd.Timestamp(e) for e in exp[:n]]


def atm_straddle(chain: pd.DataFrame, spot: float, expiry) -> dict:
    """Straddle at the strike closest to spot that has both a call and a put for `expiry`."""
    sub = chain[chain["expiry"] == pd.Timestamp(expiry)]
    calls = sub[sub["cp"] == "C"].set_index("strike")
    puts = sub[sub["cp"] == "P"].set_index("strike")
    strikes = calls.index.intersection(puts.index)
    if strikes.empty:
        raise ValueError(f"no strike with both legs for expiry {expiry}")
    k = min(strikes, key=lambda s: (abs(s - spot), s))
    c, p = calls.loc[k], puts.loc[k]
    flags = straddle_quote_flags(float(c["bid"]), float(c["ask"]), float(p["bid"]), float(p["ask"]))
    out = {"expiry": pd.Timestamp(expiry), "strike": float(k), **flags}
    if "iv" in sub.columns:
        out["iv_call"], out["iv_put"] = c.get("iv"), p.get("iv")
    return out
