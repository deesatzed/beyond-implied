import numpy as np
import pytest

from beyond_implied.metrics import (
    aurc,
    christoffersen,
    encompassing,
    kupiec,
    mincer_zarnowitz,
    pit_uniformity,
    pnl_shape,
    qlike,
    risk_at_coverage,
    risk_coverage,
    straddle_pnl,
)

rng = np.random.default_rng(7)


def test_qlike_prefers_true_variance():
    true_var = rng.uniform(0.5, 2.0, 5000)
    proxy = true_var * rng.chisquare(1, 5000)  # noisy unbiased proxy, like a squared return
    assert qlike(proxy, true_var) < qlike(proxy, true_var * 1.5)
    assert qlike(proxy, true_var) < qlike(proxy, true_var * 0.7)


def test_qlike_normalized_zero_at_perfect():
    v = np.array([1.0, 2.0, 3.0])
    assert qlike(v, v, normalized=True) == pytest.approx(0.0)


def test_mincer_zarnowitz_unbiased():
    f = rng.uniform(0.01, 0.08, 4000)
    y = f + rng.normal(0, 0.01, 4000)
    mz = mincer_zarnowitz(y, f)
    assert mz["slope"] == pytest.approx(1.0, abs=0.05)
    assert mz["wald_p"] > 0.01


def test_encompassing_detects_extra_information():
    n = 3000
    implied = rng.uniform(0.02, 0.08, n)
    signal = rng.normal(0, 0.01, n)          # information the benchmark does not have
    y = implied + signal + rng.normal(0, 0.005, n)
    model = implied + signal
    dates = np.repeat(np.arange(n // 10), 10)  # 10 events per announcement date
    res = encompassing(y, model, implied, cluster=dates)
    assert res["adds_information"] and res["n_clusters"] == n // 10

    trailing = implied + rng.normal(0, 0.02, n)
    res3 = encompassing(y, model, implied, cluster=dates, controls={"trailing": trailing})
    assert res3["adds_information"] and "b_trailing" in res3

    useless = implied + rng.normal(0, 0.01, n)
    res2 = encompassing(implied + rng.normal(0, 0.005, n), useless, implied, cluster=dates)
    assert not res2["adds_information"]


def test_pit_uniform():
    assert pit_uniformity(rng.uniform(0, 1, 2000))["ks_p"] > 0.01
    assert pit_uniformity(rng.beta(5, 5, 2000))["ks_p"] < 0.01


def test_kupiec_and_christoffersen():
    hits = rng.uniform(0, 1, 2000) < 0.05
    assert kupiec(hits, 0.05)["p_uc"] > 0.01
    assert kupiec(hits, 0.01)["p_uc"] < 0.01
    clustered = np.zeros(1000, dtype=bool)
    clustered[100:150] = True  # 5% breaches, all in one run
    cc = christoffersen(clustered, 0.05)
    assert cc["p_uc"] > 0.05 and cc["p_ind"] < 0.01


def test_risk_coverage():
    conf = np.array([0.9, 0.8, 0.1, 0.2])
    loss = np.array([0.0, 1.0, 5.0, 3.0])
    rc = risk_coverage(conf, loss)
    assert rc["risk"].tolist() == pytest.approx([0.0, 0.5, 4.0 / 3.0, 9.0 / 4.0])
    assert risk_at_coverage(conf, loss, 0.5) == pytest.approx(0.5)
    assert aurc(conf, loss) == pytest.approx(np.mean([0.0, 0.5, 4 / 3, 9 / 4]))


def test_pnl_shape():
    pnl = straddle_pnl([0.02, 0.10, 0.01, 0.0], [0.04, 0.04, 0.04, 0.04], half_spread_rel=0.0)
    s = pnl_shape(pnl, alpha=0.25)
    assert s["worst"] == pytest.approx(-0.04)
    assert s["expected_shortfall"] == pytest.approx(-0.04)
    assert s["hit_rate"] == pytest.approx(0.25)
    assert s["max_drawdown"] == pytest.approx(0.07)
