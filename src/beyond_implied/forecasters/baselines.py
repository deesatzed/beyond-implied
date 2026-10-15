"""Baseline forecasts for earnings moves. No look-ahead: only strictly earlier events are used."""

from __future__ import annotations

import numpy as np
import pandas as pd


def trailing_mean_abs_move(events: pd.DataFrame, n: int = 12, min_n: int = 4,
                           symbol_col: str = "symbol", date_col: str = "announce_date",
                           move_col: str = "realized_move") -> pd.DataFrame:
    """Mean realized move over the previous `n` events of the same symbol.

    Returns a frame aligned to `events.index` with columns `f_trailing` and `trailing_n`.
    The current event is never included (shift before rolling).
    """
    ordered = events.sort_values([symbol_col, date_col])
    g = ordered.groupby(symbol_col, sort=False)[move_col]
    prior = g.shift(1)
    mean = prior.groupby(ordered[symbol_col], sort=False).rolling(n, min_periods=min_n).mean()
    count = prior.groupby(ordered[symbol_col], sort=False).rolling(n, min_periods=1).count()
    out = pd.DataFrame({
        "f_trailing": mean.reset_index(level=0, drop=True),
        "trailing_n": count.reset_index(level=0, drop=True).fillna(0).astype(int),
    })
    return out.reindex(events.index)


def trailing_to_implied_ratio(f_trailing: pd.Series, implied: pd.Series) -> pd.Series:
    """>1 means past moves exceeded what the market now prices."""
    return f_trailing / implied.replace(0, np.nan)
