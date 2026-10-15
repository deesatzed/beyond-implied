"""Declarative commit/abstain rules. Any rule that fires means ABSTAIN."""

from __future__ import annotations

import math
import operator
from dataclasses import dataclass, field
from pathlib import Path

from ..config import load_toml

_OPS = {
    "eq": operator.eq,
    "ne": operator.ne,
    "lt": operator.lt,
    "le": operator.le,
    "gt": operator.gt,
    "ge": operator.ge,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
}


@dataclass(frozen=True)
class Rule:
    id: str
    conditions: tuple[dict, ...]
    reason: str = ""


@dataclass
class Decision:
    commit: bool
    fired: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)

    def as_payload(self) -> dict:
        return {"commit": self.commit, "fired": self.fired, "missing": sorted(set(self.missing))}


def _is_missing(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v))


def _check(cond: dict, fields: dict, missing: list[str]) -> bool:
    name, op = cond["field"], cond["op"]
    value = fields.get(name)
    if op == "is_null":
        return _is_missing(value)
    if op == "not_null":
        return not _is_missing(value)
    if op not in _OPS:
        raise ValueError(f"unknown op {op!r} in rule condition {cond}")
    if _is_missing(value):
        missing.append(name)
        return False
    return bool(_OPS[op](value, cond["value"]))


def load_rules(path: str | Path) -> list[Rule]:
    rules = []
    for r in load_toml(path).get("rule", []):
        if "when" in r:
            conds = (r["when"],)
        elif "all" in r:
            conds = tuple(r["all"])
        else:
            raise ValueError(f"rule {r.get('id')!r} needs `when` or `all`")
        rules.append(Rule(id=r["id"], conditions=conds, reason=r.get("reason", "")))
    ids = [r.id for r in rules]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate rule ids")
    return rules


def evaluate(rules: list[Rule], fields: dict) -> Decision:
    d = Decision(commit=True)
    for rule in rules:
        if all(_check(c, fields, d.missing) for c in rule.conditions):
            d.fired.append(rule.id)
            d.reasons.append(rule.reason)
    d.commit = not d.fired
    return d
