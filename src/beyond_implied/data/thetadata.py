"""ThetaData adapter via the official Python library (`pip install -e ".[theta]"`, Python 3.12+).

The library connects directly to ThetaData's servers; no Terminal or Java is needed.
Docs: https://thetadata.net/docs/Python-Library/Getting-Started.html

Auth: an API key from THETADATA_API_KEY (the library's name) or THETA_DATA_API_KEY, read from the
environment or the repo's .env. The key is passed to the client and never logged or written.

License note: retail ThetaData data is for individual use. Raw responses are cached under
data/raw/thetadata/ (gitignored); publish only derived statistics.

Returned shapes match cboe_options.parse_chain so downstream code is source-agnostic:
- eod_option_chain -> DataFrame[root, expiry, cp, strike, bid, ask, close, volume, date, ...]
- eod_stock_ohlc  -> DataFrame indexed by date with open, high, low, close, volume
"""

from __future__ import annotations

import datetime as dt
import os
import time
from functools import lru_cache

import pandas as pd

from ..config import project_root, raw_dir

KEY_NAMES = ("THETADATA_API_KEY", "THETA_DATA_API_KEY")
_last_call = [0.0]


def _read_dotenv() -> dict:
    path = project_root() / ".env"
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def api_key() -> str:
    env = _read_dotenv()
    for name in KEY_NAMES:
        v = os.environ.get(name) or env.get(name)
        if v:
            return v
    raise RuntimeError(f"No ThetaData key: set one of {KEY_NAMES} in the environment or .env")


@lru_cache(maxsize=1)
def client():
    from thetadata import ThetaClient  # optional dependency

    return ThetaClient(api_key=api_key(), dataframe_type="pandas")


def _throttle(min_interval: float) -> None:
    wait = _last_call[0] + min_interval - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    _last_call[0] = time.monotonic()


def _to_pandas(df) -> pd.DataFrame:
    return df if isinstance(df, pd.DataFrame) else df.to_pandas()


_RIGHT = {"C": "C", "CALL": "C", "P": "P", "PUT": "P"}


def normalize_option_eod(raw: pd.DataFrame, root: str) -> pd.DataFrame:
    """Map the library's option EOD columns onto the shared chain schema."""
    df = raw.copy()
    df["root"] = root.upper()
    df["expiry"] = pd.to_datetime(df["expiration"])
    df["cp"] = df["right"].astype(str).str.upper().map(_RIGHT)
    df["date"] = pd.to_datetime(df["created"]).dt.tz_localize(None).dt.normalize()
    keep = ["root", "date", "expiry", "cp", "strike", "bid", "ask", "close", "volume",
            "bid_size", "ask_size", "last_trade"]
    return df[[c for c in keep if c in df.columns]].dropna(subset=["cp"])


def eod_option_chain(root: str, start: dt.date, end: dt.date | None = None, *,
                     max_dte: int | None = 60, strike_range: int | None = None,
                     min_interval: float = 2.5, cache: bool = True) -> pd.DataFrame:
    """End-of-day quotes for all expiries (optionally within max_dte) from start to end."""
    end = end or start
    kw = {"symbol": root.upper(), "expiration": "*", "start_date": start, "end_date": end}
    if max_dte is not None:
        kw["max_dte"] = max_dte
    if strike_range is not None:
        kw["strike_range"] = strike_range
    _throttle(min_interval)
    raw = _to_pandas(client().option_history_eod(**kw))
    if cache and not raw.empty:
        d = raw_dir("thetadata") / "option_eod" / root.upper()
        d.mkdir(parents=True, exist_ok=True)
        raw.to_csv(d / f"{start.isoformat()}_{end.isoformat()}.csv.gz", index=False,
                   compression="gzip")
    return normalize_option_eod(raw, root) if not raw.empty else raw


def eod_stock_ohlc(symbol: str, start: dt.date, end: dt.date, *, min_interval: float = 2.5,
                   cache: bool = True) -> pd.DataFrame:
    _throttle(min_interval)
    raw = _to_pandas(client().stock_history_eod(symbol=symbol.upper(), start_date=start,
                                                end_date=end))
    if raw.empty:
        return raw
    if cache:
        d = raw_dir("thetadata") / "stock_eod"
        d.mkdir(parents=True, exist_ok=True)
        raw.to_csv(d / f"{symbol.upper()}_{start.isoformat()}_{end.isoformat()}.csv.gz",
                   index=False, compression="gzip")
    df = raw.copy()
    df["date"] = pd.to_datetime(df["created"]).dt.tz_localize(None).dt.normalize()
    return df.set_index("date")[["open", "high", "low", "close", "volume"]].sort_index()
