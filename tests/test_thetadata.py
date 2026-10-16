import pandas as pd
import pytest

from beyond_implied.data import thetadata


def test_api_key_from_env_alias(monkeypatch, tmp_path):
    monkeypatch.setenv("BI_ROOT", str(tmp_path))
    for k in thetadata.KEY_NAMES:
        monkeypatch.delenv(k, raising=False)
    (tmp_path / ".env").write_text('# comment\nTHETA_DATA_API_KEY="abc123"\nOTHER=1\n')
    assert thetadata.api_key() == "abc123"
    monkeypatch.setenv("THETADATA_API_KEY", "fromenv")
    assert thetadata.api_key() == "fromenv"


def test_api_key_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("BI_ROOT", str(tmp_path))
    for k in thetadata.KEY_NAMES:
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(RuntimeError):
        thetadata.api_key()


def test_normalize_option_eod():
    raw = pd.DataFrame({
        "symbol": ["AAPL"] * 3,
        "expiration": ["2026-07-31"] * 3,
        "strike": [210.0, 210.0, 215.0],
        "right": ["CALL", "PUT", "weird"],
        "created": ["2026-07-30T17:15:00.000"] * 3,
        "bid": [5.0, 4.8, 1.0], "ask": [5.2, 5.0, 1.1], "close": [5.1, 4.9, 1.0],
        "volume": [100, 90, 5],
    })
    out = thetadata.normalize_option_eod(raw, "aapl")
    assert len(out) == 2 and set(out["cp"]) == {"C", "P"}
    assert out["root"].iloc[0] == "AAPL"
    assert out["date"].iloc[0] == pd.Timestamp("2026-07-30")
    assert out["expiry"].iloc[0] == pd.Timestamp("2026-07-31")


def test_stock_ohlc_chunks_long_ranges(monkeypatch, tmp_path):
    import datetime as dt

    monkeypatch.setenv("BI_ROOT", str(tmp_path))
    calls = []

    class Fake:
        def stock_history_eod(self, symbol, start_date, end_date):
            assert (end_date - start_date).days <= 364
            calls.append((start_date, end_date))
            days = pd.bdate_range(start_date, end_date)
            return pd.DataFrame({"created": days, "open": 1.0, "high": 1.0, "low": 1.0,
                                 "close": 1.0, "volume": 1})

    monkeypatch.setattr(thetadata, "client", lambda: Fake())
    out = thetadata.eod_stock_ohlc("AAPL", dt.date(2023, 6, 1), dt.date(2026, 10, 15),
                                   min_interval=0, cache=False)
    assert len(calls) == 4
    assert out.index.min() == pd.Timestamp("2023-06-01") and out.index.is_unique


def test_naive_dates_mixed_offsets_and_precision():
    s = pd.Series(["2023-12-26 17:16:22-05:00", "2024-07-30 17:15:00.123-04:00", "2026-07-30T17:15:00.000"])
    out = thetadata._naive_dates(s)
    assert out.tolist() == [pd.Timestamp("2023-12-26"), pd.Timestamp("2024-07-30"),
                            pd.Timestamp("2026-07-30")]
