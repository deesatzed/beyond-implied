"""Phase 2 data test: calendar -> universe -> prices -> chains -> event table -> report.

Resumable: calendar days and ThetaData responses are cached under data/raw/, so a rerun only
fetches what is missing. Outputs:
- data/processed/calendar_hist.csv.gz, data/processed/events.csv.gz, data/processed/failures.csv
  (gitignored: built from vendor data)
- report/data_test.md and report/data_test/*.csv (derived statistics only)
"""

from __future__ import annotations

import datetime as dt
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .config import data_dir, project_root, universe_config
from .data.calendar_history import MISSING, calendar_range, select_universe
from .data.quality import passes_universe
from .data.thetadata import eod_option_chain, eod_stock_ohlc
from .events.build import build_event, infer_timing, season_label
from .events.timing import pre_post_dates


def _processed() -> Path:
    p = data_dir() / "processed"
    p.mkdir(parents=True, exist_ok=True)
    return p


def build_events(start: dt.date, end: dt.date, n_names: int = 100, max_dte: int = 45,
                 symbols: list[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    t0 = time.time()
    cal = calendar_range(start, end)
    cal.to_csv(_processed() / "calendar_hist.csv.gz", index=False, compression="gzip")
    (_processed() / "calendar_missing.txt").write_text("\n".join(MISSING))
    if len(MISSING) > 5:
        raise RuntimeError(f"{len(MISSING)} calendar days missing after retries; rerun later "
                           "(cached days are reused)")
    universe = symbols or select_universe(cal, n_names)
    print(f"calendar rows {len(cal)}; universe {len(universe)} names; {time.time()-t0:.0f}s",
          flush=True)
    rows, fails = [], []
    cal = cal[cal["symbol"].isin(universe)].sort_values(["symbol", "date"])
    for k, (sym, evs) in enumerate(cal.groupby("symbol", sort=False), 1):
        try:
            ohlc = eod_stock_ohlc(sym, start - dt.timedelta(days=14),
                                  min(end + dt.timedelta(days=7), dt.date.today()))
            ohlc = ohlc[ohlc["close"] > 0]
        except Exception as e:  # noqa: BLE001 - record and continue
            fails.append({"symbol": sym, "announce_date": None, "stage": "stock_eod",
                          "reason": f"{type(e).__name__}: {str(e)[:150]}"})
            continue
        for ev in evs.itertuples(index=False):
            ann = ev.date.date()
            rec = {"symbol": sym, "announce_date": ann}
            inferred, ratio = infer_timing(ohlc["close"], ohlc["open"], ann)
            known = ev.timing if ev.timing in ("BMO", "AMC") else None
            timing = known or inferred
            if timing not in ("BMO", "AMC"):
                fails.append({**rec, "stage": "timing", "reason": "timing unknown and not inferable"})
                continue
            try:
                pre, post = pre_post_dates(ann, timing, [d.date() for d in ohlc.index])
                chain = eod_option_chain(sym, pre, post, max_dte=max_dte)
                if chain.empty:
                    raise ValueError("empty option chain")
                row = build_event(sym, ann, timing, ohlc, chain,
                                  timing_source="calendar" if known else "inferred",
                                  timing_ratio=ratio)
                row["timing_inferred"] = inferred
                row.update(market_cap=ev.market_cap, n_estimates=ev.n_estimates,
                           eps_forecast=ev.eps_forecast, eps=ev.eps, surprise_pct=ev.surprise_pct)
                rows.append(row)
            except Exception as e:  # noqa: BLE001
                fails.append({**rec, "stage": "event",
                              "reason": f"{type(e).__name__}: {str(e)[:150]}"})
        print(f"[{k}/{len(universe)}] {sym}: events so far {len(rows)}, failures {len(fails)}, "
              f"{(time.time()-t0)/60:.1f} min", flush=True)
    events = pd.DataFrame(rows)
    failures = pd.DataFrame(fails, columns=["symbol", "announce_date", "stage", "reason"])
    events.to_csv(_processed() / "events.csv.gz", index=False, compression="gzip")
    failures.to_csv(_processed() / "failures.csv", index=False)
    return events, failures


def _usable(events: pd.DataFrame, cfg: dict) -> pd.Series:
    ok = []
    for r in events.itertuples(index=False):
        good = not (isinstance(r.invariant_errors, str) and r.invariant_errors)
        good = good and passes_universe(spot=r.spot, option_volume=r.option_volume,
                                        rel_spread=r.rel_spread, zero_bid=bool(r.zero_bid), cfg=cfg)
        ok.append(good)
    return pd.Series(ok, index=events.index)


def season_table(events: pd.DataFrame) -> pd.DataFrame:
    e = events.copy()
    e["season"] = e["announce_date"].map(season_label)
    imp = e["implied_move_event"].where(e["implied_move_event"].notna(), e["implied_move_simple"])
    e["implied"] = imp
    e["win"] = e["realized_move"] > e["implied"]
    g = e.groupby("season")
    return pd.DataFrame({
        "events": g.size(),
        "usable": g["usable"].sum(),
        "implied_event_mean": g["implied_move_event"].mean(),
        "implied_simple_mean": g["implied_move_simple"].mean(),
        "realized_mean": g["realized_move"].mean(),
        "realized_over_implied": g["realized_move"].mean() / g["implied"].mean(),
        "win_rate": g["win"].mean(),
        "straddle_ret_mid": g["straddle_ret_mid"].mean(),
        "straddle_ret_exec": g["straddle_ret_exec"].mean(),
    }).reset_index()


def real_data_parameters(events: pd.DataFrame) -> dict:
    """Inputs for re-running the power analysis on realistic numbers (usable events only)."""
    u = events[events["usable"]].copy()
    imp = u["implied_move_event"].where(u["implied_move_event"] > 0, u["implied_move_simple"])
    ratio = (u["realized_move"] / imp).replace([np.inf, -np.inf], np.nan).dropna()
    logr = np.log(ratio.clip(lower=1e-4))
    date_means = logr.groupby(u.loc[ratio.index, "announce_date"]).mean()
    return {
        "n_usable": len(u),
        "n_dates": int(u["announce_date"].nunique()),
        "events_per_date_median": float(u.groupby("announce_date").size().median()),
        "sd_log_implied": float(np.log(imp[imp > 0]).std()),
        "base_move_median": float(imp.median()),
        "ratio_mean": float(ratio.mean()),
        "ratio_quantiles": {q: float(ratio.quantile(q)) for q in (0.1, 0.5, 0.9, 0.99)},
        "sd_date_effect": float(date_means.std()),
    }


def write_report(events: pd.DataFrame, failures: pd.DataFrame, n_names: int) -> Path:
    cfg = universe_config()
    if events.empty:
        path = project_root() / "report" / "data_test.md"
        reasons = failures.groupby(["stage"]).size().to_dict() if len(failures) else {}
        path.write_text(f"# Phase 2 data test\n\nNo events built. Failures by stage: {reasons}\n")
        return path
    events = events.copy()
    for c in ("announce_date", "pre_date", "post_date", "expiry_1", "expiry_2"):
        if c in events:
            events[c] = pd.to_datetime(events[c])
    events["usable"] = _usable(events, cfg) if len(events) else []
    out = project_root() / "report" / "data_test"
    out.mkdir(parents=True, exist_ok=True)
    seasons = season_table(events)
    seasons.to_csv(out / "seasons.csv", index=False)

    err = events["invariant_errors"].fillna("").str.split(";").explode()
    err = err[err != ""].value_counts()
    warn = events["invariant_warnings"].fillna("").str.split(";").explode()
    warn = warn[warn != ""].value_counts()
    fail_stage = failures.groupby("stage").size() if len(failures) else pd.Series(dtype=int)

    known = events[events["timing_source"] == "calendar"]
    agree = (known["timing"] == known["timing_inferred"]).mean() if len(known) else math.nan
    params = real_data_parameters(events)
    pd.Series(params, dtype=object).to_json(out / "real_params.json", indent=2)

    attempted = len(events) + len(failures)
    usable = int(events["usable"].sum())
    unusable_share = 1 - usable / attempted if attempted else math.nan
    n_seasons = seasons["season"].nunique()
    per_season_500 = usable / max(n_seasons, 1) * 500 / max(n_names, 1)

    def fmt(x, pct=False):
        if x is None or (isinstance(x, float) and math.isnan(x)):
            return "n/a"
        return f"{x:.1%}" if pct else f"{x:.4f}"

    lines = [
        "# Phase 2 data test",
        "",
        (f"Built {dt.date.today().isoformat()} by `bi phase2`. Universe: {n_names} largest names with "
        "≥ 8 announcements since mid-2023. Raw data stays local; this file holds derived statistics."),
        "",
        "## Headline",
        "",
        (f"- Events attempted: {attempted}; built: {len(events)}; usable after invariants and the "
        f"universe filter: {usable} ({fmt(usable / attempted if attempted else math.nan, True)})."),
        f"- Unusable share: {fmt(unusable_share, True)} (stop criterion: > 10–15%).",
        (f"- Seasons covered: {n_seasons}. Projected usable events at 500 names: "
        f"~{per_season_500 * n_seasons:,.0f} ({per_season_500:,.0f} per season)."),
        (f"- Timing: {int((events['timing_source'] == 'inferred').sum())} events used inferred timing; "
        f"{len(known)} had calendar timing, where inference agreed {fmt(agree, True)}."),
        "",
        "## By season",
        "",
        "| Season | Events | Usable | Implied (event) | Implied (simple) | Realized | Realized / implied | Win rate | Straddle ret (mid) | Straddle ret (exec) |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in seasons.itertuples(index=False):
        lines.append(
            f"| {r.season} | {r.events} | {int(r.usable)} | {fmt(r.implied_event_mean, True)} | "
            f"{fmt(r.implied_simple_mean, True)} | {fmt(r.realized_mean, True)} | "
            f"{r.realized_over_implied:.2f} | {fmt(r.win_rate, True)} | "
            f"{fmt(r.straddle_ret_mid, True)} | {fmt(r.straddle_ret_exec, True)} |")
    lines += [
        "",
        ("Win = realized move above the implied move (event estimate when available). Straddle "
        "returns hold the pre-event ATM straddle for one day (mid to mid, and pre ask to post bid)."),
        ("ORATS check: ORATS reported ≈ +45% average straddle returns for the season ending "
        "February 2026 versus ≈ −2% over the prior twelve quarters; compare the 2026Q1 row."),
        "",
        "## Failures",
        "",
        "| Stage or check | Count |",
        "| --- | --- |",
    ]
    for k, v in fail_stage.items():
        lines.append(f"| pipeline: {k} | {v} |")
    for k, v in err.items():
        lines.append(f"| invariant error: {k} | {v} |")
    for k, v in warn.items():
        lines.append(f"| invariant warning: {k} | {v} |")
    lines += [
        "",
        "## Real-data parameters for the power analysis",
        "",
        "```json",
        pd.Series(params, dtype=object).to_json(indent=2),
        "```",
        "",
    ]
    path = project_root() / "report" / "data_test.md"
    path.write_text("\n".join(lines))
    return path
