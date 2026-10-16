import copy
import json
from pathlib import Path

import pytest

from beyond_implied.challengers.elicited_net import SpecError, load, validate

EXAMPLE = (Path(__file__).resolve().parents[1] / "src" / "beyond_implied" / "challengers"
           / "elicited_net" / "example_spec.json")


def _spec():
    return json.loads(EXAMPLE.read_text())


def test_example_spec_is_valid_and_hashed():
    spec, sha = load(EXAMPLE)
    assert spec["target"] == "abs_move" and len(sha) == 64


def _node(spec, nid):
    return next(n for n in spec["nodes"] if n["id"] == nid)


@pytest.mark.parametrize("mutate,msg", [
    (lambda s: _node(s, "f_trailing").update(input="realized_move"), "forbidden"),
    (lambda s: _node(s, "f_trailing").update(input="close_next_day"), "allowed pre-event"),
    (lambda s: _node(s, "abs_move").update(median=0.5), "median"),
    (lambda s: _node(s, "abs_move").update(range=[0.2, 0.01]), "range"),
    (lambda s: _node(s, "underpricing").update(range=[-0.1, 1.4]), "positive"),
    (lambda s: _node(s, "implied_move_event").update(parents=["abs_move"]), "cycle"),
    (lambda s: _node(s, "abs_move").update(parents=["nope"]), "unknown parent"),
    (lambda s: _node(s, "abs_move").update(unit="percent"), "unit"),
    (lambda s: _node(s, "abs_move").update(rationale=""), "rationale"),
    (lambda s: _node(s, "underpricing").update(kind="target"), "target"),
])
def test_validator_rejects(mutate, msg):
    s = copy.deepcopy(_spec())
    mutate(s)
    with pytest.raises(SpecError, match=msg):
        validate(s)
