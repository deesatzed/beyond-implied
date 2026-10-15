"""ThetaData Terminal adapter (historical EOD option chains and stock OHLC).

Interface only. Implement in Phase 2 against the Terminal's documented endpoints, after
installing the Terminal on the Mac Mini. Do not guess endpoints: read the current docs first.

License note: retail ThetaData data is for individual use. Cache raw responses under data/raw/
(gitignored) and publish only derived statistics.

Expected return shapes (match cboe_options.parse_chain so downstream code is source-agnostic):
- eod_option_chain -> DataFrame[root, expiry, cp, strike, bid, ask, volume, open_interest, date]
- eod_stock_ohlc  -> DataFrame indexed by date with open, high, low, close, volume
"""

from __future__ import annotations

import datetime as dt

import pandas as pd

_TODO = "Phase 2: implement against the ThetaData Terminal docs (see data/GOAL.md)."


def eod_option_chain(root: str, date: dt.date) -> pd.DataFrame:
    raise NotImplementedError(_TODO)


def eod_stock_ohlc(symbol: str, start: dt.date, end: dt.date) -> pd.DataFrame:
    raise NotImplementedError(_TODO)
