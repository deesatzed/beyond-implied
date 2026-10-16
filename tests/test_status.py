import json

from beyond_implied import status


def test_status_reads_logs_without_vendor_data(tmp_path, monkeypatch):
    root = tmp_path
    (root / "pyproject.toml").write_text("")
    logs = root / "data" / "logs"
    logs.mkdir(parents=True)
    (logs / "daily-2026-10-15.log").write_text(
        "=== 2026-10-15 16:25:01 EDT start\n"
        + json.dumps({"date": "2026-10-15", "selected": 27, "n_ok": 27, "n_failed": 0}) + "\n"
        "=== 2026-10-15 16:26:40 EDT exit 0\n")
    (logs / "pull500.log").write_text("[12/500] AAPL: 140 events, 7.5 min\n")
    snap = root / "data" / "raw" / "cboe_options" / "2026-10-15"
    snap.mkdir(parents=True)
    (snap / "AAPL.json.gz").write_bytes(b"x")
    monkeypatch.setenv("BI_ROOT", str(root))

    s = status.collect()
    run = s["daily_runs"][0]
    assert (run["date"], run["exit"], run["ok"], run["files"]) == ("2026-10-15", 0, 27, 1)
    lr = s["long_runs"][0]
    assert (lr["log"], lr["done"], lr["total"], lr["current"]) == ("pull500.log", "12", "500", "AAPL")
    assert s["data"]["forward_snapshot_days"] == 1
    assert s["ledger"]["exists"] is False
    # Nothing from inside the vendor files is read.
    assert "AAPL.json.gz" not in json.dumps(s)
