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


def _naive_dates(s: pd.Series) -> pd.Series:
    """Report timestamps -> naive local calendar dates (drops any timezone, keeps wall time)."""
    t = pd.to_datetime(s)
    if t.dt.tz is not None:
        t = t.dt.tz_localize(None)
    return t.dt.normalize()


_RIGHT = {"C": "C", "CALL": "C", "P": "P", "PUT": "P"}


def normalize_option_eod(raw: pd.DataFrame, root: str) -> pd.DataFrame:
    """Map the library's option EOD columns onto the shared chain schema."""
    df = raw.copy()
    df["root"] = root.upper()
    df["expiry"] = pd.to_datetime(df["expiration"])
    df["cp"] = df["right"].astype(str).str.upper().map(_RIGHT)
    df["date"] = _naive_dates(df["created"])
    keep = ["root", "date", "expiry", "cp", "strike", "bid", "ask", "close", "volume",
            "bid_size", "ask_size", "last_trade"]
    return df[[c for c in keep if c in df.columns]].dropna(subset=["cp"])


def _cache_path(kind: str, name: str):
    d = raw_dir("thetadata") / kind
    d.mkdir(parents=True, exist_ok=True)
    return d / name


def eod_option_chain(root: str, start: dt.date, end: dt.date | None = None, *,
                     max_dte: int | None = 60, strike_range: int | None = None,
                     min_interval: float = 2.5, cache: bool = True) -> pd.DataFrame:
    """End-of-day quotes for all expiries (optionally within max_dte) from start to end.

    With `cache`, a previously downloaded identical request is read from disk instead.
    """
    end = end or start
    tag = f"dte{max_dte}" + (f"_sr{strike_range}" if strike_range else "")
    path = _cache_path(f"option_eod/{root.upper()}", f"{start.isoformat()}_{end.isoformat()}_{tag}.csv.gz")
    if cache and path.exists():
        raw = pd.read_csv(path)
    else:
        kw = {"symbol": root.upper(), "expiration": "*", "start_date": start, "end_date": end}
        if max_dte is not None:
            kw["max_dte"] = max_dte
        if strike_range is not None:
            kw["strike_range"] = strike_range
        _throttle(min_interval)
        raw = _to_pandas(client().option_history_eod(**kw))
        if cache:
            raw.to_csv(path, index=False, compression="gzip")
    return normalize_option_eod(raw, root) if not raw.empty else raw


MAX_DAYS_PER_REQUEST = 365  # ThetaData rejects longer stock EOD ranges


def eod_stock_ohlc(symbol: str, start: dt.date, end: dt.date, *, min_interval: float = 2.5,
                   cache: bool = True) -> pd.DataFrame:
    """Daily OHLC; ranges longer than 365 days are split into chunks and joined."""
    if (end - start).days > MAX_DAYS_PER_REQUEST - 1:
        parts, a = [], start
        while a <= end:
            b = min(a + dt.timedelta(days=MAX_DAYS_PER_REQUEST - 1), end)
            parts.append(eod_stock_ohlc(symbol, a, b, min_interval=min_interval, cache=cache))
            a = b + dt.timedelta(days=1)
        parts = [p for p in parts if not p.empty]
        if not parts:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        out = pd.concat(parts).sort_index()
        return out[~out.index.duplicated(keep="last")]
    path = _cache_path("stock_eod", f"{symbol.upper()}_{start.isoformat()}_{end.isoformat()}.csv.gz")
    if cache and path.exists():
        raw = pd.read_csv(path)
    else:
        _throttle(min_interval)
        raw = _to_pandas(client().stock_history_eod(symbol=symbol.upper(), start_date=start,
                                                    end_date=end))
        if cache:
            raw.to_csv(path, index=False, compression="gzip")
    if raw.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    df = raw.copy()
    df["date"] = _naive_dates(df["created"])
    out = df.set_index("date")[["open", "high", "low", "close", "volume"]].sort_index()
    return out[~out.index.duplicated(keep="last")]
