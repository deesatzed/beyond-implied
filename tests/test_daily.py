import datetime as dt

import pandas as pd

from beyond_implied.data.calendar import parse_nasdaq_calendar
from beyond_implied.data.daily import select_names
from beyond_implied.data.market_calendar import is_trading_day, next_trading_day, prev_trading_day

D = dt.date


def _payload(rows):
    return {"data": {"rows": rows}}


def test_parse_nasdaq_calendar():
    cal = parse_nasdaq_calendar(_payload([
        {"symbol": "TRV", "time": "time-pre-market", "marketCap": "$78,803,812,000", "name": "Travelers"},
        {"symbol": "ABC", "time": "time-after-hours", "marketCap": "$3,000,000,000"},
        {"symbol": "XYZ", "time": "time-not-supplied", "marketCap": "N/A"},
    ]), D(2026, 10, 16))
    assert cal["timing"].tolist() == ["BMO", "AMC", "UNKNOWN"]
    assert cal.loc[0, "market_cap"] == 78_803_812_000
    assert pd.isna(cal.loc[2, "market_cap"])
    assert parse_nasdaq_calendar({"data": {"rows": None}}, D(2026, 10, 17)).empty


def _cal(rows, date):
    return parse_nasdaq_calendar(_payload(rows), date)


def test_select_names_roles_and_filters():
    today = _cal([
        {"symbol": "AMC1", "time": "time-after-hours", "marketCap": "$50,000,000,000"},   # pre
        {"symbol": "BMO0", "time": "time-pre-market", "marketCap": "$40,000,000,000"},    # post
        {"symbol": "UNK", "time": "time-not-supplied", "marketCap": "$30,000,000,000"},   # unknown
        {"symbol": "TINY", "time": "time-after-hours", "marketCap": "$500,000,000"},      # too small
    ], D(2026, 10, 15))
    nxt = _cal([{"symbol": "BMO1", "time": "time-pre-market", "marketCap": "$20,000,000,000"},
                {"symbol": "AMC2", "time": "time-after-hours", "marketCap": "$90,000,000,000"}],
               D(2026, 10, 16))
    prv = _cal([{"symbol": "AMC0", "time": "time-after-hours", "marketCap": "$10,000,000,000"}],
               D(2026, 10, 14))
    sel = select_names(today, nxt, prv)
    roles = dict(zip(sel["symbol"], sel["role"]))
    assert roles == {"AMC1": "pre", "BMO1": "pre", "BMO0": "post", "AMC0": "post", "UNK": "unknown"}
    assert sel["symbol"].tolist()[0] == "AMC1"   # sorted by market cap
    assert len(select_names(today, nxt, prv, max_names=2)) == 2


def test_trading_days():
    assert not is_trading_day(D(2026, 11, 26))            # Thanksgiving
    assert next_trading_day(D(2026, 11, 25)) == D(2026, 11, 27)
    assert prev_trading_day(D(2026, 10, 19)) == D(2026, 10, 16)  # Monday -> Friday
