"""Earnings calendar loader.

Input CSV needs columns: symbol, date (YYYY-MM-DD), timing. Optional: confirmed, source.
Timing labels are normalized to BMO (before open), AMC (after close) or UNKNOWN.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

TIMINGS = ("BMO", "AMC", "UNKNOWN")

_BMO = {"bmo", "before open", "before market open", "pre-market", "premarket", "pre market"}
_AMC = {"amc", "after close", "after market close", "post-market", "postmarket", "post market"}


def normalize_timing(label) -> str:
    if not isinstance(label, str):
        return "UNKNOWN"
    s = label.strip().lower()
    if s in _BMO:
        return "BMO"
    if s in _AMC:
        return "AMC"
    return "UNKNOWN"


def load_calendar_csv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    missing = {"symbol", "date", "timing"} - set(df.columns)
    if missing:
        raise ValueError(f"calendar CSV missing columns: {sorted(missing)}")
    df["symbol"] = df["symbol"].str.strip().str.upper()
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    df["timing"] = df["timing"].map(normalize_timing)
    if "confirmed" in df.columns:
        df["confirmed"] = df["confirmed"].astype(str).str.lower().isin({"true", "1", "yes", "y"})
    else:
        df["confirmed"] = False
    df["usable"] = df["timing"].isin(["BMO", "AMC"])
    return df.drop_duplicates(["symbol", "date"]).sort_values(["date", "symbol"]).reset_index(drop=True)
