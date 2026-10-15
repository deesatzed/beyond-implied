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

    pp = sub.add_parser("power", help="simulation power analysis for the primary test")
    pp.add_argument("--sims", type=int, default=500)
    pp.add_argument("--out", default="report/power")
    pp.set_defaults(func=_cmd_power)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
