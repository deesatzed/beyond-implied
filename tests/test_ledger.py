import json

from beyond_implied.ledger import append, prereg_payload, read, verify


def test_append_and_verify(tmp_path):
    led = tmp_path / "l.jsonl"
    append(led, "note", {"text": "start"}, ts_utc="2026-10-15T20:00:00+00:00")
    append(led, "prediction", {"prediction_id": "AAPL-2026Q3", "event_ts": "2026-10-30T20:30:00+00:00",
                               "f_model": 0.041}, ts_utc="2026-10-29T21:00:00+00:00")
    append(led, "outcome", {"prediction_id": "AAPL-2026Q3", "realized_move": 0.052},
           ts_utc="2026-10-31T21:00:00+00:00")
    res = verify(led)
    assert res.ok and res.n_records == 3


def test_tamper_detected(tmp_path):
    led = tmp_path / "l.jsonl"
    append(led, "note", {"x": 1}, ts_utc="2026-10-15T20:00:00+00:00")
    append(led, "note", {"x": 2}, ts_utc="2026-10-15T20:01:00+00:00")
    lines = led.read_text().splitlines()
    rec = json.loads(lines[0])
    rec["payload"]["x"] = 99
    lines[0] = json.dumps(rec)
    led.write_text("\n".join(lines) + "\n")
    res = verify(led)
    assert not res.ok and res.first_bad == 0


def test_prediction_after_event_rejected(tmp_path):
    led = tmp_path / "l.jsonl"
    append(led, "prediction", {"prediction_id": "X", "event_ts": "2026-10-15T12:00:00+00:00"},
           ts_utc="2026-10-15T13:00:00+00:00")
    res = verify(led)
    assert not res.ok and "event_ts" in res.reason


def test_outcome_needs_prior_prediction(tmp_path):
    led = tmp_path / "l.jsonl"
    append(led, "outcome", {"prediction_id": "nope"}, ts_utc="2026-10-15T13:00:00+00:00")
    assert not verify(led).ok


def test_prereg_payload_hashes(tmp_path):
    f = tmp_path / "PRE.md"
    f.write_text("frozen")
    payload = prereg_payload([f])
    assert len(next(iter(payload["files"].values()))) == 64
    led = tmp_path / "l.jsonl"
    append(led, "prereg", payload, ts_utc="2026-10-15T13:00:00+00:00")
    assert read(led)[0]["kind"] == "prereg"
