import datetime as dt
import math

import pandas as pd
import pytest

from beyond_implied.events import (
    atm_straddle,
    event_variance_two_expiry,
    expected_abs_move,
    expiries_after,
    implied_move_simple,
    pre_post_dates,
    realized_move,
)

D = dt.date
# Thu 2026-10-29, Fri 10-30, Mon 11-02 (weekend skipped)
DAYS = [D(2026, 10, 28), D(2026, 10, 29), D(2026, 10, 30), D(2026, 11, 2), D(2026, 11, 3)]


def test_bmo_alignment():
    assert pre_post_dates(D(2026, 10, 30), "BMO", DAYS) == (D(2026, 10, 29), D(2026, 10, 30))


def test_amc_alignment_over_weekend():
    assert pre_post_dates(D(2026, 10, 30), "AMC", DAYS) == (D(2026, 10, 30), D(2026, 11, 2))


def test_bmo_on_monday_uses_friday_close():
    assert pre_post_dates(D(2026, 11, 2), "BMO", DAYS) == (D(2026, 10, 30), D(2026, 11, 2))


def test_unknown_timing_rejected():
    with pytest.raises(ValueError):
        pre_post_dates(D(2026, 10, 30), "UNKNOWN", DAYS)


def test_event_variance_recovers_known_split():
    base_rate, event_var = 0.25**2, 0.05**2   # 25% base vol, 5% one-day jump std
    t1, t2 = 3 / 252, 10 / 252
    iv1 = math.sqrt((base_rate * t1 + event_var) / t1)
    iv2 = math.sqrt((base_rate * t2 + event_var) / t2)
    ev, br = event_variance_two_expiry(iv1, t1, iv2, t2)
    assert ev == pytest.approx(event_var, rel=1e-9)
    assert br == pytest.approx(base_rate, rel=1e-9)
    assert expected_abs_move(ev) == pytest.approx(math.sqrt(2 / math.pi) * 0.05)


def test_negative_event_variance_is_nan():
    assert math.isnan(expected_abs_move(-1e-4))


def test_moves():
    assert implied_move_simple(8.0, 200.0) == pytest.approx(0.04)
    assert realized_move(100.0, 94.0) == pytest.approx(0.06)


def _chain():
    rows = []
    for exp in ["2026-10-30", "2026-11-06"]:
        for k in [95.0, 100.0, 105.0]:
            rows.append({"expiry": pd.Timestamp(exp), "cp": "C", "strike": k, "bid": 3.0, "ask": 3.2, "iv": 0.5})
            rows.append({"expiry": pd.Timestamp(exp), "cp": "P", "strike": k, "bid": 2.8, "ask": 3.0, "iv": 0.5})
    return pd.DataFrame(rows)


def test_atm_straddle_and_expiries():
    ch = _chain()
    exps = expiries_after(ch, D(2026, 10, 30))
    assert [e.date() for e in exps] == [D(2026, 10, 30), D(2026, 11, 6)]
    s = atm_straddle(ch, spot=101.0, expiry=exps[0])
    assert s["strike"] == 100.0
    assert s["straddle_mid"] == pytest.approx(6.0)
    assert s["rel_spread"] == pytest.approx(0.4 / 6.0)
    assert not s["zero_bid"]
