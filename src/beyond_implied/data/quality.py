"""Quote quality flags and universe filter. Flag problems; never silently fill them."""

from __future__ import annotations

import math


def straddle_quote_flags(call_bid: float, call_ask: float, put_bid: float, put_ask: float) -> dict:
    mid = (call_bid + call_ask + put_bid + put_ask) / 2.0
    spread = (call_ask + put_ask) - (call_bid + put_bid)
    return {
        "straddle_mid": mid,
        "zero_bid": bool(call_bid <= 0 or put_bid <= 0),
        "crossed": bool(call_ask < call_bid or put_ask < put_bid),
        "rel_spread": spread / mid if mid > 0 else math.inf,
    }


def passes_universe(*, spot: float, option_volume: float, rel_spread: float, zero_bid: bool,
                    cfg: dict) -> bool:
    u = cfg["universe"]
    return (
        spot >= u["min_underlying_price"]
        and option_volume >= u["min_option_volume"]
        and rel_spread <= u["max_straddle_rel_spread"]
        and not (u.get("exclude_zero_bid", True) and zero_bid)
    )
