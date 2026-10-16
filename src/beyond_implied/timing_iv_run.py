"""Compute IV-collapse timing for every calendar event in the universe and validate it.

Writes data/processed/timing_iv.csv.gz (all events) and report/timing_iv.md (agreement with
recorded and habitual timing, by threshold). Resumable through the ThetaData cache.
"""

from __future__ import annotations

import datetime as dt
import time

import pandas as pd

from .config import data_dir, project_root
from .data.calendar_history import select_universe
from .data.market_calendar import next_trading_day, prev_trading_day
from .data.thetadata import eod_option_chain, eod_stock_ohlc
from .events.timing_iv import iv_collapse_timing
from .phase2 import habitual_timing


def run(start: dt.date, end: dt.date, n_names: int = 100, max_dte: int = 45) -> pd.DataFrame:
    t0 = time.time()
    cal = pd.read_csv(data_dir() / "processed" / "calendar_hist.csv.gz", parse_dates=["date"])
    universe = select_universe(cal, n_names)
    habitual, _ = habitual_timing(cal, universe)
    cal = cal[cal["symbol"].isin(universe)].sort_values(["symbol", "date"])
    rows = []
    for k, (sym, evs) in enumerate(cal.groupby("symbol", sort=False), 1):
        try:
            ohlc = eod_stock_ohlc(sym, start - dt.timedelta(days=14),
                                  min(end + dt.timedelta(days=7), dt.date.today()))
        except Exception as e:  # noqa: BLE001
            print(f"{sym}: stock_eod {type(e).__name__}", flush=True)
            continue
        for ev in evs.itertuples(index=False):
            ann = ev.date.date()
            rec = {"symbol": sym, "announce_date": ann,
                   "recorded": ev.timing if ev.timing in ("BMO", "AMC") else None,
                   "habitual": habitual.get(sym)}
            try:
                chain = eod_option_chain(sym, prev_trading_day(ann), next_trading_day(ann),
                                         max_dte=max_dte)
                res = iv_collapse_timing(chain, ohlc["close"], ann) if not chain.empty else {}
            except Exception as e:  # noqa: BLE001
                res = {"timing": "UNKNOWN", "error": f"{type(e).__name__}: {str(e)[:100]}"}
            rows.append({**rec, **res})
        print(f"[{k}/{len(universe)}] {sym}: {len(rows)} events, {(time.time()-t0)/60:.1f} min",
              flush=True)
    out = pd.DataFrame(rows).rename(columns={"timing": "iv_timing"})
    out.to_csv(data_dir() / "processed" / "timing_iv.csv.gz", index=False, compression="gzip")
    return out


def report(df: pd.DataFrame) -> str:
    ref = df["recorded"].fillna(df["habitual"])
    v = df[ref.notna()].copy()
    v["ref"] = ref[ref.notna()]
    lines = ["# IV-collapse timing: validation", "",
             "Reference = recorded timing where available, else the company's habitual timing.",
             "Coverage = share of reference events the rule classifies; accuracy = agreement among those.",
             "", "| Min ratio | Coverage | Accuracy | n classified |", "| --- | --- | --- | --- |"]
    for r in (1.25, 1.5, 2.0, 3.0):
        cls = v[(v["ratio"] >= r) & (v[["drop_bmo", "drop_amc"]].max(axis=1) >= 0.02)]
        cls = cls.assign(t=lambda x: x["drop_bmo"].gt(x["drop_amc"]).map({True: "BMO", False: "AMC"}))
        acc = (cls["t"] == cls["ref"]).mean() if len(cls) else float("nan")
        lines.append(f"| {r} | {len(cls)/max(len(v),1):.1%} | {acc:.1%} | {len(cls)} |")
    rec = df[df["recorded"].notna() & df["iv_timing"].isin(["BMO", "AMC"])]
    acc_rec = (rec["iv_timing"] == rec["recorded"]).mean() if len(rec) else float("nan")
    unknown = df[ref.isna()]
    lines += ["", (f"- Events with a reference: {len(v)}; against recorded timing only: "
              f"{acc_rec:.1%} of {len(rec)}."),
              (f"- Events with no reference timing: {len(unknown)}; the rule classifies "
              f"{unknown['iv_timing'].isin(['BMO','AMC']).mean():.1%} of them at ratio ≥ 1.5."),
              f"- Names with no reference timing: {unknown['symbol'].nunique()}.", ""]
    path = project_root() / "report" / "timing_iv.md"
    path.write_text("\n".join(lines))
    return str(path)
