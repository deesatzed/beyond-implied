"""Operational status snapshot for the monitoring dashboard: `bi status`.

Reads only local logs, run summaries and derived reports, and writes counts, dates, exit codes and
headline statistics. It never includes vendor data (prices, quotes, chains), so its output may be
published.
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
import re
import shutil
import subprocess
from pathlib import Path

from .config import data_dir, project_root

LAUNCHD_LABEL = "com.deesatzed.beyond-implied.daily"
_PROGRESS = re.compile(r"\[(\d+)/(\d+)\]\s+(\S+?):.*?([\d.]+) min")
_EXIT = re.compile(r"=== (\d{4}-\d{2}-\d{2} [\d:]+ \w+) exit (\d+)")
_START = re.compile(r"=== (\d{4}-\d{2}-\d{2} [\d:]+ \w+) start")


def _run(cmd: list[str], cwd: Path | None = None) -> str:
    try:
        return subprocess.run(cmd, check=False, cwd=cwd, capture_output=True,
                              text=True, timeout=20).stdout
    except Exception:  # noqa: BLE001
        return ""


def _mtime_iso(p: Path) -> str:
    return dt.datetime.fromtimestamp(p.stat().st_mtime, dt.UTC).isoformat(timespec="seconds")


def _count_rows(path: Path) -> int | None:
    if not path.exists():
        return None
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt") as f:
        return max(sum(1 for _ in f) - 1, 0)


def launchd_state() -> dict:
    out = _run(["launchctl", "list"])
    line = next((ln for ln in out.splitlines() if LAUNCHD_LABEL in ln), None)
    if line is None:
        return {"label": LAUNCHD_LABEL, "loaded": False}
    pid, last_exit, _ = line.split("\t")
    return {"label": LAUNCHD_LABEL, "loaded": True, "running": pid != "-",
            "last_exit": int(last_exit) if last_exit.lstrip("-").isdigit() else None,
            "schedule": "Mon-Fri 16:25 America/New_York"}


def daily_runs(logs: Path, raw: Path, n: int = 15) -> list[dict]:
    runs = []
    for log in sorted(logs.glob("daily-*.log"))[-n:]:
        text = log.read_text(errors="replace")
        starts, exits = _START.findall(text), _EXIT.findall(text)
        summaries = [json.loads(ln) for ln in text.splitlines()
                     if ln.startswith("{") and '"n_ok"' in ln]
        s = summaries[-1] if summaries else {}
        date = log.stem.removeprefix("daily-")
        snap_dir = raw / "cboe_options" / date
        runs.append({
            "date": date, "attempts": len(starts),
            "started": starts[-1] if starts else None,
            "finished": exits[-1][0] if exits else None,
            "exit": int(exits[-1][1]) if exits else None,
            "selected": s.get("selected"), "ok": s.get("n_ok"), "failed": s.get("n_failed"),
            "files": len(list(snap_dir.glob("*.json.gz"))) if snap_dir.exists() else 0,
        })
    return runs


def long_runs(logs: Path) -> list[dict]:
    procs = _run(["ps", "-axo", "pid,etime,command"])
    active = [ln.strip() for ln in procs.splitlines()
              if re.search(r"\bbi (phase2|timing-iv|power-real|power)\b", ln) and "grep" not in ln]
    out = []
    for log in sorted(logs.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True):
        if log.name.startswith("daily-"):
            continue
        lines = log.read_text(errors="replace").splitlines()
        prog = next((m for ln in reversed(lines) if (m := _PROGRESS.search(ln))), None)
        last = next((ln for ln in reversed(lines) if ln.strip()), "")
        age_min = (dt.datetime.now().timestamp() - log.stat().st_mtime) / 60
        running = bool(active) and age_min < 15
        out.append({
            "log": log.name, "updated": _mtime_iso(log), "running": running,
            "done": prog.group(1) if prog else None, "total": prog.group(2) if prog else None,
            "current": prog.group(3) if prog else None,
            "minutes": float(prog.group(4)) if prog else None,
            "last_line": last[:160],
        })
    return out[:8]


def processes() -> list[dict]:
    procs = _run(["ps", "-axo", "pid,etime,command"])
    rows = []
    for ln in procs.splitlines():
        if (re.search(r"bin/bi (?!status)", ln) and "grep" not in ln
                and not re.search(r"\b(osascript|sh -c|zsh -c)\b", ln)):
            pid, etime, *cmd = ln.split()
            rows.append({"pid": int(pid), "elapsed": etime,
                         "command": " ".join(c.split("/")[-1] for c in cmd)[:120]})
    return rows


def git_state(root: Path) -> dict:
    head = _run(["git", "log", "-1", "--format=%h|%cI|%s"], root).strip().split("|", 2)
    dirty = [ln for ln in _run(["git", "status", "--porcelain"], root).splitlines() if ln]
    behind = _run(["git", "rev-list", "--count", "HEAD..@{u}"], root).strip()
    return {"head": head[0] if head else None, "date": head[1] if len(head) > 1 else None,
            "subject": head[2] if len(head) > 2 else None, "uncommitted": len(dirty),
            "behind_remote": int(behind) if behind.isdigit() else None}


def data_inventory(d: Path) -> dict:
    proc = d / "processed"
    snaps = sorted(p.name for p in (d / "raw" / "cboe_options").glob("20*") if p.is_dir())
    theta = d / "raw" / "thetadata"
    missing = proc / "calendar_missing.txt"
    return {
        "calendar_announcements": _count_rows(proc / "calendar_hist.csv.gz"),
        "calendar_days_missing": (len(missing.read_text().split())
                                  if missing.exists() else None),
        "events_built": _count_rows(proc / "events.csv.gz"),
        "event_failures": _count_rows(proc / "failures.csv"),
        "timing_iv_rows": _count_rows(proc / "timing_iv.csv.gz"),
        "forward_snapshot_days": len(snaps),
        "first_snapshot": snaps[0] if snaps else None,
        "thetadata_cache_files": sum(1 for _ in theta.rglob("*") if _.is_file()) if theta.exists() else 0,
    }


def results(root: Path) -> dict:
    rep = root / "report"
    out: dict = {}
    rp = rep / "data_test" / "real_params.json"
    if rp.exists():
        out["real_params"] = json.loads(rp.read_text())
    seasons = rep / "data_test" / "seasons.csv"
    if seasons.exists():
        lines = seasons.read_text().strip().splitlines()
        keys = lines[0].split(",")
        out["seasons"] = [dict(zip(keys, ln.split(","), strict=False)) for ln in lines[1:]]
    tiv = rep / "timing_iv.md"
    if tiv.exists():
        m = re.search(r"\| 1\.5 \| ([\d.]+)% \| ([\d.]+)% \| (\d+) \|", tiv.read_text())
        if m:
            out["timing_iv"] = {"coverage": float(m.group(1)), "accuracy": float(m.group(2)),
                                "n": int(m.group(3))}
    dt_md = rep / "data_test.md"
    if dt_md.exists():
        m = re.search(r"## Decision: (.+)", dt_md.read_text())
        out["decision"] = m.group(1).strip() if m else None
    pr = rep / "power" / "power_real.csv"
    if pr.exists():
        lines = pr.read_text().strip().splitlines()
        keys = lines[0].split(",")
        out["power_real"] = [dict(zip(keys, ln.split(","), strict=False)) for ln in lines[1:]]
    return out


def ledger_state(d: Path) -> dict:
    from .config import ledger_path
    from .ledger import verify

    p = Path(ledger_path())
    if not p.exists():
        return {"exists": False, "records": 0}
    res = verify(p)
    return {"exists": True, **{k: v for k, v in res.__dict__.items() if not isinstance(v, list)}}


def collect() -> dict:
    root, d = project_root(), data_dir()
    logs = d / "logs"
    usage = shutil.disk_usage(root)
    return {
        "generated_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "host": _run(["scutil", "--get", "ComputerName"]).strip() or _run(["hostname"]).strip(),
        "launchd": launchd_state(),
        "daily_runs": daily_runs(logs, d / "raw"),
        "processes": processes(),
        "long_runs": long_runs(logs),
        "git": git_state(root),
        "data": data_inventory(d),
        "ledger": ledger_state(d),
        "results": results(root),
        "disk_free_gb": round(usage.free / 1e9, 1),
    }


def write(path: Path | None = None) -> Path:
    path = path or data_dir() / "logs" / "status.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(collect(), indent=1, default=str))
    return path


def _f(x):
    try:
        return round(float(x), 4)
    except (TypeError, ValueError):
        return None


def rows(s: dict) -> list[dict]:
    """Flatten a status snapshot into one table of rows for the dashboard, one `kind` per section.

    Every row has a unique `key`. Kinds: summary, daily, longrun, process, season.
    """
    res, data, git, led = s["results"], s["data"], s["git"], s["ledger"]
    rp, tiv = res.get("real_params", {}), res.get("timing_iv", {})
    lj = s["launchd"]
    out = [{
        "kind": "summary", "key": "summary", "generated_utc": s["generated_utc"], "host": s["host"],
        "launchd_loaded": lj.get("loaded"), "launchd_last_exit": lj.get("last_exit"),
        "launchd_schedule": lj.get("schedule"),
        "git_head": git["head"], "git_date": git["date"], "git_subject": git["subject"],
        "git_uncommitted": git["uncommitted"], "git_behind": git["behind_remote"],
        "events_built": data["events_built"], "event_failures": data["event_failures"],
        "calendar_announcements": data["calendar_announcements"],
        "calendar_days_missing": data["calendar_days_missing"],
        "timing_iv_rows": data["timing_iv_rows"],
        "forward_snapshot_days": data["forward_snapshot_days"],
        "first_snapshot": data["first_snapshot"],
        "thetadata_cache_files": data["thetadata_cache_files"],
        "ledger_records": led.get("n_records", 0), "ledger_ok": led.get("ok"),
        "disk_free_gb": s["disk_free_gb"], "decision": res.get("decision"),
        "n_usable": rp.get("n_usable"), "n_dates": rp.get("n_dates"),
        "ratio_median": _f(rp.get("ratio_quantiles", {}).get("0.5")),
        "timing_iv_accuracy": tiv.get("accuracy"), "timing_iv_coverage": tiv.get("coverage"),
        "n_processes": len(s["processes"]),
    }]
    out += [{"kind": "daily", "key": f"daily:{r['date']}", **r} for r in s["daily_runs"]]
    out += [{"kind": "longrun", "key": f"log:{r['log']}", **r,
             "done": int(r["done"]) if r["done"] else None,
             "total": int(r["total"]) if r["total"] else None} for r in s["long_runs"]]
    out += [{"kind": "process", "key": f"pid:{r['pid']}", **r} for r in s["processes"]]
    for r in res.get("seasons", []):
        out.append({"kind": "season", "key": f"season:{r['season']}", "season": r["season"],
                    "events": int(r["events"]), "usable": int(r["usable"]),
                    **{k: _f(r[k]) for k in ("implied_event_mean", "realized_mean",
                                             "realized_over_implied", "win_rate",
                                             "straddle_ret_mid", "straddle_ret_exec")}})
    return out
