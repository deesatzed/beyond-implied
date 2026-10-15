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
    files = sorted(raw_dir("nasdaq_calendar").glob(f"{date.isoformat()}_as_of_*.json"))
    return files[-1] if files else None


def calendar_range(start: dt.date, end: dt.date, *, pause: float = 0.8,
                   log_every: int = 50) -> pd.DataFrame:
    s = requests.Session()
    frames, d, n = [], start, 0
    while d <= end:
        if is_trading_day(d):
            path = _cached(d)
            try:
                if path:
                    frames.append(parse_nasdaq_calendar(json.loads(path.read_bytes()), d))
                else:
                    frames.append(fetch_nasdaq_calendar(d, session=s))
                    time.sleep(pause)
            except (requests.RequestException, ValueError) as e:
                print(f"calendar {d}: {type(e).__name__} {str(e)[:120]}", flush=True)
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
