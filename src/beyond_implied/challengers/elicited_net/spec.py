"""Load and validate an elicited-network spec (see spec_schema.md). Raises SpecError on any problem."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ALLOWED_INPUTS = frozenset({
    "implied_move_event", "implied_move_simple", "f_trailing", "trailing_n", "past_move_kurtosis",
    "market_cap", "n_estimates", "eps_forecast", "rel_spread", "vix", "vix_vix3m", "vvix",
    "sector", "timing", "days_to_expiry_1",
})
FORBIDDEN = frozenset({
    "realized_move", "post_close", "eps", "surprise_pct", "straddle_ret_mid", "straddle_ret_exec",
    "timing_inferred",
})
KINDS = {"latent", "input", "target"}
UNITS = {"fraction", "ratio", "count", "usd", "index_points", "category"}
DISTS = {"lognormal", "normal", "gamma", "beta", "student_t", "categorical"}
POSITIVE = {"lognormal", "gamma"}


class SpecError(ValueError):
    pass


def _fail(msg: str) -> None:
    raise SpecError(msg)


def _check_node(n: dict) -> None:
    nid = n.get("id")
    if not nid or not isinstance(nid, str):
        _fail("node without an id")
    if nid in FORBIDDEN or n.get("input") in FORBIDDEN:
        _fail(f"node {nid!r} uses a forbidden (outcome or post-event) field")
    if n.get("kind") not in KINDS:
        _fail(f"node {nid!r}: kind must be one of {sorted(KINDS)}")
    if n.get("unit") not in UNITS:
        _fail(f"node {nid!r}: unit must be one of {sorted(UNITS)}")
    if not n.get("rationale"):
        _fail(f"node {nid!r}: rationale is required")
    if n["kind"] == "input" and n.get("input") not in ALLOWED_INPUTS:
        _fail(f"node {nid!r}: input {n.get('input')!r} is not an allowed pre-event column")
    dist = n.get("distribution")
    if dist not in DISTS:
        _fail(f"node {nid!r}: distribution must be one of {sorted(DISTS)}")
    if dist == "categorical":
        if not n.get("categories"):
            _fail(f"node {nid!r}: categorical needs categories")
        return
    rng, med, cov = n.get("range"), n.get("median"), n.get("range_coverage", 0.9)
    if not (isinstance(rng, list) and len(rng) == 2 and rng[0] < rng[1]):
        _fail(f"node {nid!r}: range must be [low, high] with low < high")
    if med is None or not rng[0] <= med <= rng[1]:
        _fail(f"node {nid!r}: median must lie inside range")
    if not 0 < cov < 1:
        _fail(f"node {nid!r}: range_coverage must be in (0, 1)")
    if dist in POSITIVE and rng[0] <= 0:
        _fail(f"node {nid!r}: {dist} needs a positive range")
    if dist == "beta" and not (0 <= rng[0] and rng[1] <= 1):
        _fail(f"node {nid!r}: beta range must lie in [0, 1]")


def _check_graph(nodes: dict[str, dict]) -> None:
    for nid, n in nodes.items():
        for p in n.get("parents", []):
            if p == nid:
                _fail(f"node {nid!r} lists itself as a parent")
            if p not in nodes:
                _fail(f"node {nid!r}: unknown parent {p!r}")
    state: dict[str, int] = {}

    def visit(nid: str) -> None:
        if state.get(nid) == 1:
            _fail(f"cycle through node {nid!r}")
        if state.get(nid) == 2:
            return
        state[nid] = 1
        for p in nodes[nid].get("parents", []):
            visit(p)
        state[nid] = 2

    for nid in nodes:
        visit(nid)


def validate(spec: dict) -> dict:
    if spec.get("spec_version") != "1":
        _fail("spec_version must be '1'")
    raw = spec.get("nodes") or []
    if not raw:
        _fail("spec has no nodes")
    for n in raw:
        _check_node(n)
    nodes = {n["id"]: n for n in raw}
    if len(nodes) != len(raw):
        _fail("duplicate node ids")
    targets = [n["id"] for n in raw if n["kind"] == "target"]
    if targets != [spec.get("target")]:
        _fail("exactly one target node is required and its id must equal `target`")
    _check_graph(nodes)
    return spec


def load(path: str | Path) -> tuple[dict, str]:
    """Return (validated spec, SHA-256 of the file bytes)."""
    data = Path(path).read_bytes()
    return validate(json.loads(data)), hashlib.sha256(data).hexdigest()
