import datetime as dt

import pandas as pd
import pytest

from beyond_implied.data.calendar import load_calendar_csv, normalize_timing
from beyond_implied.data.cboe_indices import parse_index_csv, quality_report
from beyond_implied.data.cboe_options import cboe_symbol, parse_chain, parse_occ
from beyond_implied.data.quality import passes_universe, straddle_quote_flags


def test_parse_occ():
    o = parse_occ("AAPL261016C00130000")
    assert o == {"root": "AAPL", "expiry": dt.date(2026, 10, 16), "cp": "C", "strike": 130.0}
    assert parse_occ("SPXW261120P05825000")["strike"] == 5825.0
    with pytest.raises(ValueError):
        parse_occ("not-an-option")


def test_cboe_symbol_prefixes_indices():
    assert cboe_symbol("spx") == "_SPX" and cboe_symbol("AAPL") == "AAPL"


def test_parse_chain_synthetic_payload():
    payload = {"timestamp": "2026-10-15 18:43:59", "symbol": "XYZ", "data": {
        "symbol": "XYZ", "current_price": 101.0,
        "options": [
            {"option": "XYZ261030C00100000", "bid": 3.0, "ask": 3.2, "iv": 0.5, "volume": 10},
            {"option": "XYZ261030P00100000", "bid": 2.8, "ask": 3.0, "iv": 0.5, "volume": 12},
            {"option": "garbage", "bid": 1.0, "ask": 1.1},
        ]}}
    chain, under = parse_chain(payload)
    assert len(chain) == 2 and set(chain["cp"]) == {"C", "P"}
    assert under["current_price"] == 101.0 and under["cboe_timestamp"] == "2026-10-15 18:43:59"


def test_index_csv_and_quality():
    text = "DATE,OPEN,HIGH,LOW,CLOSE\n01/02/1990,17.24,17.24,17.24,17.24\n" \
           "01/03/1990,18.19,18.19,18.19,18.19\n01/04/1990,40.0,40.0,40.0,40.0\n"
    df = parse_index_csv(text)
    assert list(df.columns) == ["open", "high", "low", "close"]
    q = quality_report(df, jump_log=0.5)
    assert q["n"] == 3 and q["large_jumps"] == ["1990-01-04"]


def test_calendar_normalization(tmp_path):
    p = tmp_path / "cal.csv"
    pd.DataFrame({
        "Symbol": ["aapl", "msft", "xyz"],
        "Date": ["2026-10-30", "2026-10-28", "2026-10-29"],
        "Timing": ["After Close", "bmo", "time not supplied"],
    }).to_csv(p, index=False)
    cal = load_calendar_csv(p)
    assert cal.set_index("symbol")["timing"].to_dict() == {"AAPL": "AMC", "MSFT": "BMO", "XYZ": "UNKNOWN"}
    assert cal["usable"].sum() == 2
    assert normalize_timing(None) == "UNKNOWN"


def test_quote_flags_and_universe():
    f = straddle_quote_flags(0.0, 0.5, 2.0, 2.2)
    assert f["zero_bid"] and not f["crossed"]
    cfg = {"universe": {"min_underlying_price": 10, "min_option_volume": 300,
                        "max_straddle_rel_spread": 0.1, "exclude_zero_bid": True}}
    assert passes_universe(spot=50, option_volume=500, rel_spread=0.05, zero_bid=False, cfg=cfg)
    assert not passes_universe(spot=50, option_volume=500, rel_spread=0.05, zero_bid=True, cfg=cfg)
