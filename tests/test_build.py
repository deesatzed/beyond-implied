import datetime as dt
import math

import numpy as np
import pandas as pd
import pytest

from beyond_implied.events.build import build_event, infer_timing, season_label, straddle_vol
from beyond_implied.phase2 import season_table

DAYS = pd.to_datetime(["2026-10-27", "2026-10-28", "2026-10-29", "2026-10-30", "2026-11-02"])


def _ohlc(opens, closes):
    return pd.DataFrame({"open": opens, "high": closes, "low": closes, "close": closes,
                         "volume": 1}, index=DAYS)


def test_infer_timing_amc_and_bmo():
    amc = _ohlc([100, 100, 100, 108, 108], [100, 100, 100, 108, 108])  # gap into 10-30
    assert infer_timing(amc["close"], amc["open"], dt.date(2026, 10, 29))[0] == "AMC"
    assert infer_timing(amc["close"], amc["open"], dt.date(2026, 10, 30))[0] == "BMO"
    flat = _ohlc([100, 100.5, 100.3, 100.4, 100], [100, 100, 100, 100, 100])
    assert infer_timing(flat["close"], flat["open"], dt.date(2026, 10, 29))[0] == "UNKNOWN"


def test_straddle_vol_inverts_approximation():
    s, sigma, t = 100.0, 0.30, 10 / 252
    straddle = math.sqrt(2 / math.pi) * s * sigma * math.sqrt(t)
    assert straddle_vol(straddle, s, t) == pytest.approx(sigma)


def _chain():
    rows = []
    for date, (c1, c2) in {"2026-10-29": (5.0, 6.0), "2026-10-30": (8.5, 8.0)}.items():
        for exp, base in (("2026-10-30", c1), ("2026-11-06", c2)):
            for cp in "CP":
                bump = 0.0 if exp == "2026-10-30" else 0.5
                rows.append({"date": pd.Timestamp(date), "expiry": pd.Timestamp(exp), "cp": cp,
                             "strike": 100.0, "bid": base / 2 + bump - 0.05,
                             "ask": base / 2 + bump + 0.05, "volume": 400})
    return pd.DataFrame(rows)


def test_build_event_amc():
    ohlc = _ohlc([100, 100, 100, 108, 108], [100, 100, 100, 108, 108])
    row = build_event("XYZ", dt.date(2026, 10, 29), "AMC", ohlc, _chain())
    assert row["pre_date"] == pd.Timestamp("2026-10-29")
    assert row["post_date"] == pd.Timestamp("2026-10-30")
    assert row["realized_move"] == pytest.approx(0.08)
    assert row["implied_move_simple"] == pytest.approx(0.05)
    assert row["option_volume"] == 1600
    assert row["invariant_errors"] == ""
    assert row["straddle_ret_mid"] == pytest.approx(8.5 / 5.0 - 1)
    assert not math.isnan(row["event_var"])


def test_season_table():
    ev = pd.DataFrame({
        "announce_date": pd.to_datetime(["2026-01-20", "2026-02-10", "2026-04-20"]),
        "implied_move_event": [0.04, float("nan"), 0.05],
        "implied_move_simple": [0.05, 0.05, 0.06],
        "realized_move": [0.06, 0.02, 0.03],
        "straddle_ret_mid": [0.4, -0.5, -0.3], "straddle_ret_exec": [0.3, -0.6, -0.4],
        "usable": [True, True, False],
    })
    t = season_table(ev).set_index("season")
    assert t.loc["2026Q1", "events"] == 2 and t.loc["2026Q1", "win_rate"] == 0.5
    assert season_label("2026-11-03") == "2026Q4"


def test_macro_window():
    from beyond_implied.events.macro import macro_in_window

    assert macro_in_window("2024-11-07")["macro_fomc"]            # FOMC statement day
    assert macro_in_window("2026-10-14")["macro_cpi"]             # CPI release day
    assert not macro_in_window("2026-10-15")["macro_event"]


def _iv_chain(vols, spot=100.0):
    """Chain for D-1, D, D+1 with one expiry; straddle priced from the given ATM vols."""
    days = pd.to_datetime(["2026-10-28", "2026-10-29", "2026-10-30"])
    exp = pd.Timestamp("2026-11-06")
    rows = []
    for d, v in zip(days, vols):
        t = max(int(np.busday_count(d.date(), exp.date())), 1) / 252
        mid = math.sqrt(2 / math.pi) * spot * v * math.sqrt(t)
        for cp in "CP":
            rows.append({"date": d, "expiry": exp, "cp": cp, "strike": 100.0,
                         "bid": mid / 2 - 0.01, "ask": mid / 2 + 0.01})
    closes = pd.Series([100.0] * 3, index=days)
    return pd.DataFrame(rows), closes


def test_iv_collapse_timing():
    from beyond_implied.events.timing_iv import iv_collapse_timing

    chain, closes = _iv_chain([0.80, 0.30, 0.28])     # crush into D's close
    assert iv_collapse_timing(chain, closes, dt.date(2026, 10, 29))["timing"] == "BMO"
    chain, closes = _iv_chain([0.80, 0.82, 0.30])     # crush into D+1's close
    assert iv_collapse_timing(chain, closes, dt.date(2026, 10, 29))["timing"] == "AMC"
    chain, closes = _iv_chain([0.30, 0.30, 0.30])     # no crush
    assert iv_collapse_timing(chain, closes, dt.date(2026, 10, 29))["timing"] == "UNKNOWN"
