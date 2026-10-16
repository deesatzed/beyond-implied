"""Past earnings dates from Nasdaq's calendar, one request per trading day, resumable.

Past dates carry EPS, surprise and analyst count but no before-open/after-close flag
(docs/prior-art.md); timing is inferred later from prices (events/build.py).
"""

from __future__ import annotations

import datetime as dt
import json
import time

import pandas as pd
import requests

from ..config import raw_dir
from .calendar import fetch_nasdaq_calendar, parse_nasdaq_calendar
from .market_calendar import is_trading_day


def _cached(date: dt.date):
    files = sorted(f for f in raw_dir("nasdaq_calendar").glob(f"{date.isoformat()}_as_of_*.json")
                   if not f.name.endswith(".meta.json"))
    return files[-1] if files else None


MISSING: list[str] = []


def _fetch_with_retry(d: dt.date, s: requests.Session, backoff=(30, 120, 300)) -> pd.DataFrame:
    for i, wait in enumerate((*backoff, None)):
        try:
            return fetch_nasdaq_calendar(d, session=s)
        except (requests.RequestException, ValueError) as e:
            if wait is None:
                raise
            print(f"calendar {d}: {type(e).__name__}; retry {i + 1} in {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def calendar_range(start: dt.date, end: dt.date, *, pause: float = 2.0,
                   log_every: int = 50) -> pd.DataFrame:
    """Days that still fail after retries are listed in MISSING and reported, never silently dropped."""
    s = requests.Session()
    MISSING.clear()
    frames, d, n = [], start, 0
    while d <= end:
        if is_trading_day(d):
            path = _cached(d)
            try:
                if path:
                    frames.append(parse_nasdaq_calendar(json.loads(path.read_bytes()), d))
                else:
                    frames.append(_fetch_with_retry(d, s))
                    time.sleep(pause)
            except (requests.RequestException, ValueError) as e:
                MISSING.append(d.isoformat())
                print(f"calendar {d}: MISSING after retries ({type(e).__name__})", flush=True)
            n += 1
            if n % log_every == 0:
                print(f"calendar: {n} trading days through {d}", flush=True)
        d += dt.timedelta(days=1)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def select_universe(cal: pd.DataFrame, n: int = 100, *, min_events: int = 8,
                    min_market_cap: float = 10e9) -> list[str]:
    """Largest names (by median market cap) with at least `min_events` announcements."""
    c = cal.dropna(subset=["market_cap"])
    g = c.groupby("symbol").agg(events=("date", "nunique"), cap=("market_cap", "median"))
    g = g[(g["events"] >= min_events) & (g["cap"] >= min_market_cap)]
    g = g[g.index.str.fullmatch(r"[A-Z]{1,5}")]  # plain tickers; skips odd share classes
    return g.sort_values("cap", ascending=False).head(n).index.tolist()
