from pathlib import Path

import pytest

from beyond_implied.gates import evaluate, load_rules

RULES = Path(__file__).resolve().parents[1] / "config" / "gates.toml"

CLEAN = {
    "timing": "AMC", "zero_bid": False, "rel_spread": 0.04, "spot": 180.0,
    "option_volume": 25_000, "trailing_n": 12, "vix_vix3m": 0.88, "vvix": 92.0,
    "macro_event": False,
}


def test_clean_event_commits():
    d = evaluate(load_rules(RULES), CLEAN)
    assert d.commit and d.fired == [] and d.missing == []


@pytest.mark.parametrize("change,rule", [
    ({"timing": "UNKNOWN"}, "G1-timing-unknown"),
    ({"zero_bid": True}, "G2-zero-bid"),
    ({"rel_spread": 0.40}, "G3-wide-spread"),
    ({"spot": 6.0}, "G4-low-price"),
    ({"option_volume": 50}, "G5-thin-options"),
    ({"trailing_n": 2}, "G6-short-history"),
    ({"vix_vix3m": 1.08, "vvix": 135.0}, "G7-stress-regime"),
    ({"macro_event": True}, "G8-macro-event"),
])
def test_each_rule_fires(change, rule):
    d = evaluate(load_rules(RULES), {**CLEAN, **change})
    assert not d.commit and rule in d.fired


def test_stress_gate_needs_both_conditions():
    d = evaluate(load_rules(RULES), {**CLEAN, "vix_vix3m": 1.08, "vvix": 95.0})
    assert d.commit


def test_missing_field_is_recorded_not_fired():
    fields = dict(CLEAN)
    del fields["vvix"]
    d = evaluate(load_rules(RULES), {**fields, "vix_vix3m": 1.2})
    assert d.commit and "vvix" in d.missing
