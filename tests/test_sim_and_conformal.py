from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from beyond_implied.config import load_toml
from beyond_implied.events.invariants import check_event, check_events
from beyond_implied.forecasters import trailing_mean_abs_move
from beyond_implied.metrics.conformal import conformal_upper, coverage
from beyond_implied.sim import (
    LookAheadError,
    SimConfig,
    assert_no_lookahead,
    private_sd_for_share,
    run_scenario,
    simulate_events,
)

ROOT = Path(__file__).resolve().parents[1]


def test_simulator_shapes_and_null_premium():
    df = simulate_events(SimConfig(n_seasons=2, dates_per_season=10, events_per_date=5, seed=1))
    assert len(df) == 100 and df["date"].nunique() == 20
    assert (df["realized_move"] >= 0).all() and (df["implied_move"] > 0).all()


def test_private_share_math():
    sd = private_sd_for_share(0.2, sd_public=0.5)
    assert sd**2 / (sd**2 + 0.25) == pytest.approx(0.2)


def test_null_size_and_planted_power():
    base = SimConfig(n_seasons=2, dates_per_season=30, events_per_date=12)
    null = run_scenario(base.with_(seed=3), n_sims=80)
    assert null["reject_rate"] <= 0.15
    strong = run_scenario(base.with_(sd_private=private_sd_for_share(0.2), seed=4), n_sims=40)
    assert strong["reject_rate"] >= 0.8


def _events_for_canary():
    rng = np.random.default_rng(0)
    dates = pd.date_range("2024-01-01", periods=8, freq="90D")
    return pd.DataFrame({
        "symbol": np.repeat(["A", "B", "C"], 8),
        "announce_date": np.tile(dates, 3),
        "realized_move": rng.uniform(0, 0.1, 24),
    })


def test_canary_passes_clean_feature():
    ev = _events_for_canary()
    assert_no_lookahead(lambda e: trailing_mean_abs_move(e, n=3, min_n=1)["f_trailing"], ev)


def test_canary_catches_leaky_feature():
    ev = _events_for_canary()

    def leaky(e):  # includes the current event in its own average
        o = e.sort_values(["symbol", "announce_date"])
        m = o.groupby("symbol")["realized_move"].transform(lambda s: s.rolling(3, min_periods=1).mean())
        return m.reindex(e.index)

    with pytest.raises(LookAheadError):
        assert_no_lookahead(leaky, ev)


def test_aci_recovers_coverage_after_shift():
    rng = np.random.default_rng(5)
    n_dates, per = 400, 10
    groups = np.repeat(np.arange(n_dates), per)
    f = np.full(groups.size, 0.04)
    scale = np.where(groups < 200, 1.0, 2.0)          # moves double in the second half
    y = f * scale * np.abs(rng.standard_normal(groups.size))
    second = groups >= 260
    static = conformal_upper(y, f, groups, alpha=0.1, gamma=0.0)
    aci = conformal_upper(y, f, groups, alpha=0.1, gamma=0.05)
    cov_static = coverage(static[second])
    cov_aci = coverage(aci[second])
    assert abs(cov_aci - 0.9) < abs(cov_static - 0.9)
    assert abs(cov_aci - 0.9) < 0.04


def test_conformal_exchangeable_coverage():
    rng = np.random.default_rng(6)
    groups = np.repeat(np.arange(300), 10)
    f = rng.uniform(0.02, 0.08, groups.size)
    y = f * np.abs(rng.standard_normal(groups.size))
    assert coverage(conformal_upper(y, f, groups, alpha=0.1)) == pytest.approx(0.9, abs=0.02)


def test_invariants():
    good = {"timing": "AMC", "pre_date": "2026-10-30", "post_date": "2026-11-02",
            "expiry_1": "2026-11-06", "spot": 100.0, "straddle_mid": 4.0, "pre_close": 100.0,
            "implied_move_simple": 0.04, "realized_move": 0.05, "rel_spread": 0.03, "event_var": 0.002}
    assert check_event(good) == []
    bad = {**good, "timing": "UNKNOWN", "expiry_1": "2026-10-29", "event_var": -0.001}
    ids = {cid for cid, _ in check_event(bad)}
    assert {"I1-timing", "I3-expiry-before-post", "I11-event-variance-negative"} <= ids
    table = check_events(pd.DataFrame([good, bad]))
    assert set(table["index"]) == {1}


def test_no_regime_feature_drives_a_gate_in_v1():
    regime = {"perm_entropy", "dfa_alpha", "recurrence_rate"}
    rules = load_toml(ROOT / "config" / "gates.toml")["rule"]
    fields = set()
    for r in rules:
        for c in ([r["when"]] if "when" in r else r["all"]):
            fields.add(c["field"])
    assert not fields & regime
