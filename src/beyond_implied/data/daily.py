"""Daily forward collection: snapshot chains for names whose pre- or post-event close is today.

Run after the close (about 16:20 New York time) on trading days.

- pre-event today:  AMC today, or BMO on the next trading day
- post-event today: BMO today, or AMC on the previous trading day
- UNKNOWN timing reporting today or next trading day: snapshotted too (timing may be filled in
  later), flagged, and excluded from H1 unless the timing is confirmed afterwards.

Names are filtered by market cap (a cheap proxy for liquid options) and capped per day.
A run log is written next to the snapshots: data/raw/cboe_options/<date>/_run.json.
"""

from __future__ import annotations

import datetime as dt
import json
import time
from pathlib import Path

import pandas as pd
import requests

from ..config import raw_dir
from .calendar import fetch_nasdaq_calendar
from .cboe_options import market_date, snapshot
from .market_calendar import is_trading_day, next_trading_day, prev_trading_day


def select_names(cal_today: pd.DataFrame, cal_next: pd.DataFrame, cal_prev: pd.DataFrame,
                 *, min_market_cap: float = 2e9, max_names: int = 250) -> pd.DataFrame:
    """Rows with a `role` column: pre, post, or unknown."""
    parts = [
        cal_today[cal_today["timing"] == "AMC"].assign(role="pre"),
        cal_next[cal_next["timing"] == "BMO"].assign(role="pre"),
        cal_today[cal_today["timing"] == "BMO"].assign(role="post"),
        cal_prev[cal_prev["timing"] == "AMC"].assign(role="post"),
        cal_today[cal_today["timing"] == "UNKNOWN"].assign(role="unknown"),
        cal_next[cal_next["timing"] == "UNKNOWN"].assign(role="unknown"),
    ]
    parts = [p for p in parts if not p.empty]
    if not parts:
        return pd.DataFrame(columns=[*cal_today.columns, "role"])
    sel = pd.concat(parts, ignore_index=True)
    sel = sel[sel["market_cap"] >= min_market_cap]
    sel = sel.sort_values("market_cap", ascending=False).drop_duplicates("symbol")
    return sel.head(max_names).reset_index(drop=True)


def run_daily(*, min_market_cap: float = 2e9, max_names: int = 250, pause: float = 1.5,
              today: dt.date | None = None, out_dir: Path | None = None) -> dict:
    today = today or market_date()
    if not is_trading_day(today):
        return {"date": today.isoformat(), "skipped": "not a trading day"}
    s = requests.Session()
    nxt, prv = next_trading_day(today), prev_trading_day(today)
    cals = {}
    for label, d in (("today", today), ("next", nxt), ("prev", prv)):
        cals[label] = fetch_nasdaq_calendar(d, session=s)
        time.sleep(pause)
    names = select_names(cals["today"], cals["next"], cals["prev"],
                         min_market_cap=min_market_cap, max_names=max_names)
    base = out_dir or raw_dir("cboe_options")
    ok, failed = [], []
    for row in names.itertuples(index=False):
        try:
            _, meta = snapshot(row.symbol, out_dir=base, session=requests.Session())
            ok.append({"symbol": row.symbol, "role": row.role, "timing": row.timing,
                       "announce_date": row.date.date().isoformat(), "sha256": meta["sha256"]})
        except requests.RequestException as e:
            failed.append({"symbol": row.symbol, "role": row.role, "error": str(e)[:200]})
        time.sleep(pause)
    log = {
        "date": today.isoformat(),
        "run_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "next_trading_day": nxt.isoformat(),
        "prev_trading_day": prv.isoformat(),
        "calendar_rows": {k: len(v) for k, v in cals.items()},
        "selected": len(names),
        "snapshots": ok,
        "failed": failed,
    }
    day_dir = base / today.isoformat()
    day_dir.mkdir(parents=True, exist_ok=True)
    (day_dir / "_run.json").write_text(json.dumps(log, indent=2))
    return log
