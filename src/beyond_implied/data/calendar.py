"""Earnings calendar: CSV loader and the Nasdaq public calendar.

CSV input needs columns: symbol, date (YYYY-MM-DD), timing. Optional: confirmed, source.
Timing labels are normalized to BMO (before open), AMC (after close) or UNKNOWN.

Nasdaq's calendar (unofficial endpoint; check terms, keep the request rate low) returns one day
at a time with `time` = time-pre-market / time-after-hours / time-not-supplied. Each day's raw
response is kept so the calendar version used for every event can be reconstructed.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

import pandas as pd
import requests

from ..config import raw_dir
from ._fetch import fetch_and_store

TIMINGS = ("BMO", "AMC", "UNKNOWN")
NASDAQ_URL = "https://api.nasdaq.com/api/calendar/earnings?date={date}"
_NASDAQ_HEADERS = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 (research; low rate)"}

_BMO = {"bmo", "before open", "before market open", "pre-market", "premarket", "pre market",
        "time-pre-market"}
_AMC = {"amc", "after close", "after market close", "post-market", "postmarket", "post market",
        "time-after-hours"}


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


def _money(s) -> float:
    if not isinstance(s, str):
        return float("nan")
    digits = re.sub(r"[^0-9.]", "", s)
    return float(digits) if digits else float("nan")


def parse_nasdaq_calendar(payload: dict, date: dt.date) -> pd.DataFrame:
    rows = ((payload or {}).get("data") or {}).get("rows") or []
    df = pd.DataFrame([{
        "symbol": str(r.get("symbol", "")).strip().upper(),
        "date": pd.Timestamp(date),
        "timing": normalize_timing(r.get("time")),
        "market_cap": _money(r.get("marketCap")),
        "name": r.get("name"),
        "source": "nasdaq",
    } for r in rows], columns=["symbol", "date", "timing", "market_cap", "name", "source"])
    df["usable"] = df["timing"].isin(["BMO", "AMC"])
    return df[df["symbol"] != ""].reset_index(drop=True)


def fetch_nasdaq_calendar(date: dt.date, *, session: requests.Session | None = None,
                          cache_dir: Path | None = None) -> pd.DataFrame:
    s = session or requests.Session()
    s.headers.update(_NASDAQ_HEADERS)
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    dest = (cache_dir or raw_dir("nasdaq_calendar")) / f"{date.isoformat()}_as_of_{stamp}.json"
    body, _ = fetch_and_store(NASDAQ_URL.format(date=date.isoformat()), dest, session=s)
    return parse_nasdaq_calendar(json.loads(body), date)
