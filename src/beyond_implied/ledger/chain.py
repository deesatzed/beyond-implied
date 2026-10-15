"""Append-only, hash-chained prediction ledger (JSON Lines)."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

GENESIS = "0" * 64
KINDS = frozenset({"prereg", "prediction", "outcome", "note"})


def _canonical(obj) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def _hash_record(rec: dict) -> str:
    body = {k: v for k, v in rec.items() if k != "hash"}
    return hashlib.sha256(_canonical(body)).hexdigest()


def _now_iso() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="seconds")


def _parse_ts(s: str) -> dt.datetime:
    t = dt.datetime.fromisoformat(s)  # Python 3.11+ accepts a trailing "Z"
    if t.tzinfo is None:
        raise ValueError(f"timestamp without timezone: {s!r}")
    return t


def read(path: str | Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def append(path: str | Path, kind: str, payload: dict, *, ts_utc: str | None = None) -> dict:
    """Append one record and return it. `ts_utc` is for tests; production uses the clock."""
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {sorted(KINDS)}, got {kind!r}")
    if kind in {"prediction", "outcome"} and "prediction_id" not in payload:
        raise ValueError(f"{kind} payload needs a prediction_id")
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    records = read(p)
    rec = {
        "seq": len(records),
        "ts_utc": ts_utc or _now_iso(),
        "kind": kind,
        "payload": payload,
        "prev_hash": records[-1]["hash"] if records else GENESIS,
    }
    _parse_ts(rec["ts_utc"])
    rec["hash"] = _hash_record(rec)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")
    return rec


@dataclass(frozen=True)
class VerifyResult:
    ok: bool
    n_records: int
    first_bad: int | None = None
    reason: str | None = None


def verify(path: str | Path) -> VerifyResult:
    records = read(path)
    prev = GENESIS
    predictions: dict[str, dict] = {}
    for i, rec in enumerate(records):
        if rec.get("seq") != i:
            return VerifyResult(False, len(records), i, f"seq {rec.get('seq')} != {i}")
        if rec.get("prev_hash") != prev:
            return VerifyResult(False, len(records), i, "prev_hash does not link to prior record")
        if _hash_record(rec) != rec.get("hash"):
            return VerifyResult(False, len(records), i, "hash mismatch (record altered)")
        kind, payload = rec.get("kind"), rec.get("payload", {})
        if kind not in KINDS:
            return VerifyResult(False, len(records), i, f"unknown kind {kind!r}")
        try:
            ts = _parse_ts(rec["ts_utc"])
        except (KeyError, ValueError) as e:
            return VerifyResult(False, len(records), i, f"bad ts_utc: {e}")
        if kind == "prediction":
            pid = payload["prediction_id"]
            if pid in predictions:
                return VerifyResult(False, len(records), i, f"duplicate prediction_id {pid}")
            if "event_ts" in payload and ts >= _parse_ts(payload["event_ts"]):
                return VerifyResult(False, len(records), i, "prediction written at/after event_ts")
            predictions[pid] = rec
        elif kind == "outcome":
            pid = payload["prediction_id"]
            if pid not in predictions:
                return VerifyResult(False, len(records), i, f"outcome for unknown prediction {pid}")
        prev = rec["hash"]
    return VerifyResult(True, len(records))


def prereg_payload(paths: list[str | Path]) -> dict:
    """SHA-256 of each pre-registration file, for a `prereg` ledger record."""
    files = {}
    for p in paths:
        p = Path(p)
        files[p.as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return {"files": files}
