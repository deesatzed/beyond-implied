"""Cboe daily index history (VIX, VIX3M, VIX9D, VVIX, SKEW).

Parsed frame: DatetimeIndex `date`, lower-case columns (`close`, or `open/high/low/close`,
or the symbol name for single-value files such as VVIX).
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from ..config import raw_dir
from ._fetch import fetch_and_store

URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/{symbol}_History.csv"


def parse_index_csv(text: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(text))
    df.columns = [c.strip().lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"], format="%m/%d/%Y")
    df = df.drop_duplicates("date").set_index("date").sort_index()
    return df.apply(pd.to_numeric, errors="coerce")


def fetch_index_history(symbol: str, *, cache_dir: Path | None = None,
                        session: requests.Session | None = None) -> pd.DataFrame:
    symbol = symbol.upper()
    dest = (cache_dir or raw_dir("cboe_indices")) / f"{symbol}_History.csv"
    body, _ = fetch_and_store(URL.format(symbol=symbol), dest, session=session)
    return parse_index_csv(body.decode("utf-8"))


def value_column(df: pd.DataFrame) -> str:
    if "close" in df.columns:
        return "close"
    return df.columns[-1]


def quality_report(df: pd.DataFrame, *, jump_log: float = 0.7, gap_bdays: int = 5) -> dict:
    """Flag gaps, non-positive values and large day-over-day log jumps."""
    col = value_column(df)
    s = df[col].dropna()
    log_jump = np.log(s).diff().abs()
    bday_gaps = np.busday_count(s.index[:-1].values.astype("datetime64[D]"),
                                s.index[1:].values.astype("datetime64[D]"))
    return {
        "column": col,
        "n": int(s.size),
        "start": s.index.min().date().isoformat() if s.size else None,
        "end": s.index.max().date().isoformat() if s.size else None,
        "missing_values": int(df[col].isna().sum()),
        "non_positive": int((s <= 0).sum()),
        "large_jumps": [d.date().isoformat() for d in log_jump[log_jump > jump_log].index],
        "gaps_over_bdays": int((bday_gaps > gap_bdays).sum()),
    }
