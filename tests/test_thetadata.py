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
