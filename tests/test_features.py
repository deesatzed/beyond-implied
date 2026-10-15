import numpy as np
import pandas as pd
import pytest

from beyond_implied.forecasters import fit_har, trailing_mean_abs_move
from beyond_implied.premium import event_premium_ratio, is_inverted, premium_sign
from beyond_implied.regime import dfa_alpha, permutation_entropy, recurrence_rate

rng = np.random.default_rng(11)


def test_permutation_entropy_bounds():
    assert permutation_entropy(np.arange(200)) == pytest.approx(0.0)
    assert permutation_entropy(rng.normal(size=5000)) > 0.98


def test_dfa_alpha_noise_vs_walk():
    noise = rng.normal(size=4096)
    assert 0.4 < dfa_alpha(noise) < 0.6
    assert 1.3 < dfa_alpha(np.cumsum(noise)) < 1.7


def test_recurrence_rate_constant_series():
    assert recurrence_rate(np.ones(50)) == pytest.approx(1.0)
    assert 0.0 < recurrence_rate(rng.normal(size=200)) < 0.2


def test_trailing_mean_has_no_look_ahead():
    ev = pd.DataFrame({
        "symbol": ["A"] * 6 + ["B"] * 3,
        "announce_date": list(pd.date_range("2025-01-01", periods=6, freq="90D"))
        + list(pd.date_range("2025-01-01", periods=3, freq="90D")),
        "realized_move": [0.01, 0.02, 0.03, 0.04, 0.05, 0.99, 0.10, 0.20, 0.30],
    })
    out = trailing_mean_abs_move(ev, n=3, min_n=2)
    a = out.loc[ev["symbol"] == "A"]
    assert np.isnan(a["f_trailing"].iloc[0]) and np.isnan(a["f_trailing"].iloc[1])
    assert a["f_trailing"].iloc[2] == pytest.approx(0.015)
    assert a["f_trailing"].iloc[5] == pytest.approx(0.04)   # 0.99 (current) excluded
    assert a["trailing_n"].tolist() == [0, 1, 2, 3, 3, 3]
    b = out.loc[ev["symbol"] == "B"]
    assert b["f_trailing"].iloc[2] == pytest.approx(0.15)   # no bleed from symbol A


def test_premium_features():
    assert bool(is_inverted(22.0, 20.0)) and not bool(is_inverted(18.0, 20.0))
    assert premium_sign(0.30, 0.20) == 1 and premium_sign(0.20, 0.30) == -1
    assert event_premium_ratio(0.04, 0.05) == pytest.approx(0.8)


def test_har_fits_persistent_variance():
    n = 1500
    rv = np.empty(n)
    rv[0] = 1.0
    for t in range(1, n):
        rv[t] = 0.1 + 0.9 * rv[t - 1] + rng.normal(0, 0.05)
    res = fit_har(pd.Series(np.abs(rv)), horizon=5, step=5)
    assert res.params[["rv_d", "rv_w", "rv_m"]].sum() > 0.7
