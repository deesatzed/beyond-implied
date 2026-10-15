"""Cboe delayed option chains: raw daily snapshots and a parser.

Parsed chain columns: root, expiry (datetime64), cp ('C'/'P'), strike, bid, ask, iv, volume,
open_interest, delta, gamma, vega, theta, last_trade_price, last_trade_time.
Units (checked 2026-10-15): per-contract `iv` is decimal (ATM AAPL 0.2346); the underlying's
`iv30` is in percent (26.7).
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

URL = "https://cdn.cboe.com/api/global/delayed_quotes/options/{symbol}.json"
INDEX_SYMBOLS = {"SPX", "XSP", "VIX", "NDX", "RUT", "DJX"}

OCC_RE = re.compile(
    r"^(?P<root>[A-Z0-9.]+?)(?P<yy>\d{2})(?P<mm>\d{2})(?P<dd>\d{2})(?P<cp>[CP])(?P<strike>\d{8})$"
)

QUOTE_FIELDS = ["bid", "ask", "iv", "volume", "open_interest", "delta", "gamma", "vega", "theta",
                "last_trade_price", "last_trade_time"]


def cboe_symbol(symbol: str) -> str:
    s = symbol.upper().lstrip("_")
    return f"_{s}" if s in INDEX_SYMBOLS else s


def parse_occ(option: str) -> dict:
    m = OCC_RE.match(option)
    if not m:
        raise ValueError(f"not an OCC option symbol: {option!r}")
    return {
        "root": m["root"],
        "expiry": dt.date(2000 + int(m["yy"]), int(m["mm"]), int(m["dd"])),
        "cp": m["cp"],
        "strike": int(m["strike"]) / 1000.0,
    }


def parse_chain(payload: dict) -> tuple[pd.DataFrame, dict]:
    """Return (chain, underlying) from a Cboe delayed-quotes JSON payload."""
    data = payload["data"]
    rows = []
    for o in data.get("options", []):
        try:
            row = parse_occ(o["option"])
        except ValueError:
            continue
        row.update({k: o.get(k) for k in QUOTE_FIELDS})
        rows.append(row)
    chain = pd.DataFrame(rows)
    if not chain.empty:
        chain["expiry"] = pd.to_datetime(chain["expiry"])
    underlying = {k: v for k, v in data.items() if k != "options"}
    underlying["cboe_timestamp"] = payload.get("timestamp")
    return chain, underlying


def snapshot(symbol: str, *, out_dir: Path | None = None,
             session: requests.Session | None = None) -> tuple[Path, dict]:
    """Save today's raw chain to data/raw/cboe_options/<UTC date>/<SYMBOL>.json with a hash sidecar."""
    sym = cboe_symbol(symbol)
    day = dt.datetime.now(dt.UTC).date().isoformat()
    dest = (out_dir or raw_dir("cboe_options")) / day / f"{sym}.json"
    _, meta = fetch_and_store(URL.format(symbol=sym), dest, session=session)
    return dest, meta


def load_snapshot(path: str | Path) -> tuple[pd.DataFrame, dict]:
    return parse_chain(json.loads(Path(path).read_text()))
