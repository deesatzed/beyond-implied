"""Command line: `bi indices`, `bi snapshot`, `bi ledger verify|prereg`."""

from __future__ import annotations

import argparse
import json
import sys
import time

from . import config


def _cmd_indices(args) -> int:
    from .data.cboe_indices import fetch_index_history, quality_report

    for sym in args.symbols:
        df = fetch_index_history(sym)
        print(json.dumps({"symbol": sym.upper(), **quality_report(df)}, indent=2))
        time.sleep(args.pause)
    return 0


def _cmd_snapshot(args) -> int:
    from .data.cboe_options import snapshot

    for sym in args.symbols:
        path, meta = snapshot(sym)
        print(f"{sym.upper()}: {path} sha256={meta['sha256'][:12]} bytes={meta['bytes']}")
        time.sleep(args.pause)
    return 0


def _cmd_ledger(args) -> int:
    from .ledger import append, prereg_payload, verify

    if args.action == "verify":
        target = args.files[0] if args.files else (args.path or config.ledger_path())
        res = verify(target)
        print(json.dumps(res.__dict__))
        return 0 if res.ok else 1
    if args.action == "prereg":
        if not args.files:
            print("prereg needs the files to hash", file=sys.stderr)
            return 2
        rec = append(args.path or config.ledger_path(), "prereg", prereg_payload(args.files))
        print(json.dumps(rec, indent=2))
        return 0
    return 2


def _cmd_status(args) -> int:
    from .status import collect, write

    if args.stdout:
        print(json.dumps(collect(), indent=1, default=str))
    else:
        print(write())
    return 0


def _cmd_daily(args) -> int:
    from .data.daily import run_daily

    log = run_daily(min_market_cap=args.min_cap, max_names=args.max_names, pause=args.pause)
    summary = {k: v for k, v in log.items() if k not in ("snapshots", "failed")}
    summary["n_ok"] = len(log.get("snapshots", []))
    summary["n_failed"] = len(log.get("failed", []))
    print(json.dumps(summary))
    return 0 if not log.get("failed") else 1


def _cmd_calendar(args) -> int:
    import datetime as dt

    from .data.calendar import fetch_nasdaq_calendar

    cal = fetch_nasdaq_calendar(dt.date.fromisoformat(args.date))
    cal = cal[cal["market_cap"] >= args.min_cap].sort_values("market_cap", ascending=False)
    print(cal[["symbol", "timing", "market_cap", "name"]].to_string(index=False))
    print(f"{len(cal)} names; timing: {cal['timing'].value_counts().to_dict()}")
    return 0


def _cmd_theta_probe(args) -> int:
    """Smoke test the ThetaData connection on one symbol and date. Never prints the key."""
    import datetime as dt

    from .data.thetadata import eod_option_chain, eod_stock_ohlc
    from .events import atm_straddle, expiries_after, implied_move_simple

    day = dt.date.fromisoformat(args.date)
    ohlc = eod_stock_ohlc(args.symbol, day - dt.timedelta(days=7), day)
    print(f"stock EOD rows: {len(ohlc)}; last close {ohlc['close'].iloc[-1] if len(ohlc) else 'n/a'}")
    chain = eod_option_chain(args.symbol, day, max_dte=args.max_dte)
    print(f"option EOD rows: {len(chain)}; columns: {list(chain.columns)}")
    if len(chain) and len(ohlc):
        spot = float(ohlc["close"].iloc[-1])
        exp = expiries_after(chain, day, n=2)
        print(f"expiries: {[e.date().isoformat() for e in exp]}")
        s = atm_straddle(chain[chain["date"] == chain["date"].max()], spot, exp[0])
        print(f"ATM strike {s['strike']} straddle mid {s['straddle_mid']:.2f} "
              f"implied move {implied_move_simple(s['straddle_mid'], spot):.4f} "
              f"rel spread {s['rel_spread']:.3f} zero bid {s['zero_bid']}")
    return 0


def _cmd_phase2(args) -> int:
    import datetime as dt

    import pandas as pd

    from .config import data_dir
    from .phase2 import build_events, write_report

    if args.report_only:
        events = pd.read_csv(data_dir() / "processed" / "events.csv.gz")
        failures = pd.read_csv(data_dir() / "processed" / "failures.csv")
    else:
        syms = args.symbols.split(",") if args.symbols else None
        events, failures = build_events(dt.date.fromisoformat(args.start),
                                        dt.date.fromisoformat(args.end), args.names,
                                        symbols=syms)
    print(write_report(events, failures, args.names))
    return 0


def _cmd_power_real(args) -> int:
    """Power grid with parameters and move shapes from the real event table (run where data is)."""
    from pathlib import Path

    import numpy as np
    import pandas as pd

    from .config import data_dir, project_root
    from .sim.power import real_data_grid

    params = json.loads((project_root() / "report" / "data_test" / "real_params.json").read_text())
    ev = pd.read_csv(data_dir() / "processed" / "events.csv.gz")
    imp = ev["implied_move_event"].where(ev["implied_move_event"] > 0, ev["implied_move_simple"])
    ratio = (ev["realized_move"] / imp).replace([np.inf, -np.inf], np.nan).dropna()
    ratio = ratio[(ratio >= 0) & (ratio < 20)]
    scale = args.target_names / args.names
    n_seasons = 13  # full seasons in the free ThetaData history (mid-2023 to Q3 2026)
    epd = max(2, round(params["n_usable"] / params["n_dates"] * scale))
    dps = max(10, round(params["n_dates"] / n_seasons))
    print(f"simulating {args.target_names} names: ~{epd} events per date, {dps} dates per season")
    grid = real_data_grid(params, tuple(ratio.round(6).tolist()), n_sims=args.sims,
                          events_per_date=epd, dates_per_season=dps)
    out = Path(project_root() / "report" / "power")
    out.mkdir(parents=True, exist_ok=True)
    grid.to_csv(out / "power_real.csv", index=False)
    print(grid.to_string(index=False))
    return 0


def _cmd_timing_iv(args) -> int:
    import datetime as dt

    import pandas as pd

    from .config import data_dir
    from .timing_iv_run import report, run

    if args.report_only:
        df = pd.read_csv(data_dir() / "processed" / "timing_iv.csv.gz")
    else:
        df = run(dt.date.fromisoformat(args.start), dt.date.fromisoformat(args.end), args.names)
    print(report(df))
    return 0


def _cmd_power(args) -> int:
    from pathlib import Path

    from .sim import adversarial_table, conformal_under_regime_flip, power_grid

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    grid = power_grid(n_sims=args.sims)
    grid.to_csv(out / "power_grid.csv", index=False)
    adv = adversarial_table(n_sims=args.sims)
    adv.to_csv(out / "power_adversarial.csv", index=False)
    conf = conformal_under_regime_flip()
    conf.to_csv(out / "conformal_regime_flip.csv", index=False)
    print(grid.to_string(index=False))
    print(adv.to_string(index=False))
    print(conf.to_string(index=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="bi", description="Beyond Implied")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("indices", help="download Cboe daily index history")
    pi.add_argument("symbols", nargs="+")
    pi.add_argument("--pause", type=float, default=1.0)
    pi.set_defaults(func=_cmd_indices)

    ps = sub.add_parser("snapshot", help="save today's delayed option chains")
    ps.add_argument("symbols", nargs="+")
    ps.add_argument("--pause", type=float, default=2.0)
    ps.set_defaults(func=_cmd_snapshot)

    pl = sub.add_parser("ledger", help="verify the ledger or record a pre-registration")
    pl.add_argument("action", choices=["verify", "prereg"])
    pl.add_argument("files", nargs="*", help="verify: ledger path; prereg: files to hash")
    pl.add_argument("--path", help="ledger path (default ledger/predictions.jsonl)")
    pl.set_defaults(func=_cmd_ledger)

    pd_ = sub.add_parser("daily", help="after the close: snapshot names with a pre/post-event close today")
    pd_.add_argument("--min-cap", type=float, default=2e9)
    pd_.add_argument("--max-names", type=int, default=250)
    pd_.add_argument("--pause", type=float, default=1.5)
    pd_.set_defaults(func=_cmd_daily)

    pc = sub.add_parser("calendar", help="show the Nasdaq earnings calendar for a date")
    pc.add_argument("date", help="YYYY-MM-DD")
    pc.add_argument("--min-cap", type=float, default=2e9)
    pc.set_defaults(func=_cmd_calendar)

    pt = sub.add_parser("theta-probe", help="smoke test ThetaData on one symbol and date")
    pt.add_argument("symbol")
    pt.add_argument("date", help="YYYY-MM-DD")
    pt.add_argument("--max-dte", type=int, default=45)
    pt.set_defaults(func=_cmd_theta_probe)

    p2 = sub.add_parser("phase2", help="build the event table and the data-test report")
    p2.add_argument("--start", default="2023-07-01")
    p2.add_argument("--end", default="2026-10-14")
    p2.add_argument("--names", type=int, default=100)
    p2.add_argument("--symbols", help="comma-separated list instead of the auto universe")
    p2.add_argument("--report-only", action="store_true")
    p2.set_defaults(func=_cmd_phase2)

    pv = sub.add_parser("timing-iv", help="IV-collapse timing for all events, with validation")
    pv.add_argument("--start", default="2023-07-01")
    pv.add_argument("--end", default="2026-10-14")
    pv.add_argument("--names", type=int, default=100)
    pv.add_argument("--report-only", action="store_true")
    pv.set_defaults(func=_cmd_timing_iv)

    pr = sub.add_parser("power-real", help="power grid using real-data parameters (after phase2)")
    pr.add_argument("--sims", type=int, default=300)
    pr.add_argument("--names", type=int, default=100, help="names in the real event table")
    pr.add_argument("--target-names", type=int, default=500, help="universe size to project")
    pr.set_defaults(func=_cmd_power_real)

    pst = sub.add_parser("status", help="write data/logs/status.json for the monitoring dashboard")
    pst.add_argument("--stdout", action="store_true", help="print instead of writing the file")
    pst.set_defaults(func=_cmd_status)

    pp = sub.add_parser("power", help="simulation power analysis for the primary test")
    pp.add_argument("--sims", type=int, default=500)
    pp.add_argument("--out", default="report/power")
    pp.set_defaults(func=_cmd_power)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
