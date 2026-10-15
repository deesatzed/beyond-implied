"""Power and size of the primary test (encompassing, date-clustered) under planted signals."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..metrics.second_order import encompassing
from .generate import SimConfig, private_sd_for_share, simulate_events


def run_scenario(cfg: SimConfig, n_sims: int = 200, alpha: float = 0.05,
                 cluster_by_date: bool = True, trailing_control: bool = False) -> dict:
    """Share of simulated studies in which the model is found to add information (b_model > 0).

    `cluster_by_date=False` uses heteroskedasticity-robust errors only, to show what ignoring
    same-day correlation does to the false-positive rate.
    """
    hits, b = 0, []
    for k in range(n_sims):
        df = simulate_events(cfg.with_(seed=cfg.seed * 100_003 + k))
        res = encompassing(df["realized_move"], df["f_model"], df["implied_move"],
                           cluster=df["date"] if cluster_by_date else None, alpha=alpha,
                           controls={"trailing": df["f_trailing"]} if trailing_control else None)
        b.append(res["b_model"])
        hits += res["adds_information"]
    return {
        "n_events": cfg.n_seasons * cfg.dates_per_season * cfg.events_per_date,
        "n_dates": cfg.n_seasons * cfg.dates_per_season,
        "reject_rate": hits / n_sims,
        "b_model_median": float(np.median(b)),
        "n_sims": n_sims,
    }


def adversarial_table(n_sims: int = 500, share: float = 0.05,
                      base: SimConfig | None = None) -> pd.DataFrame:
    """Size and power when the study's assumptions are stressed (adapted from the ARC-GATE review)."""
    base = base or SimConfig()
    sig = private_sd_for_share(share, base.sd_public)
    cases = [
        ("null, date-clustered errors", base, True),
        ("null, ignoring same-day correlation", base, False),
        ("null, premium flips sign each season", base.with_(regime_flip=True), True),
        ("null, one 10x catastrophic move", base.with_(catastrophe=True), True),
        (f"{share:.0%} private info, baseline", base.with_(sd_private=sig), True),
        (f"{share:.0%} private info, premium flips", base.with_(sd_private=sig, regime_flip=True), True),
        (f"{share:.0%} private info, one 10x move", base.with_(sd_private=sig, catastrophe=True), True),
    ]
    rows = []
    for i, (name, cfg, clustered) in enumerate(cases):
        r = run_scenario(cfg.with_(seed=500 + i), n_sims=n_sims, cluster_by_date=clustered)
        rows.append({"scenario": name, **r})
    return pd.DataFrame(rows)


def conformal_under_regime_flip(alpha: float = 0.10, gamma: float = 0.05,
                                base: SimConfig | None = None, seed: int = 7) -> pd.DataFrame:
    """Coverage by season of an upper bound on the move, static vs adaptive conformal."""
    from ..metrics.conformal import conformal_upper

    base = base or SimConfig()
    df = simulate_events(base.with_(regime_flip=True, premium=0.30, seed=seed))
    rows = []
    for label, g in (("static", 0.0), ("adaptive (ACI)", gamma)):
        res = conformal_upper(df["realized_move"], df["implied_move"], df["date"], alpha=alpha,
                              gamma=g, warmup=200)
        res["season"] = df["season"].to_numpy()
        for s, grp in res[res["scored"]].groupby("season"):
            rows.append({"method": label, "season": int(s), "coverage": 1 - grp["breach"].mean(),
                         "n": len(grp)})
    return pd.DataFrame(rows)


def power_grid(shares=(0.0, 0.02, 0.05, 0.10), seasons=(1, 2, 4), events_per_date=(8, 15),
               base: SimConfig | None = None, n_sims: int = 200) -> pd.DataFrame:
    base = base or SimConfig()
    rows = []
    for share in shares:
        for s in seasons:
            for epd in events_per_date:
                cfg = base.with_(sd_private=private_sd_for_share(share, base.sd_public),
                                 n_seasons=s, events_per_date=epd,
                                 seed=int(share * 1000) + 10 * s + epd)
                rows.append({"private_share": share, "seasons": s, "events_per_date": epd,
                             **run_scenario(cfg, n_sims=n_sims)})
    return pd.DataFrame(rows)


def real_data_grid(params: dict, z_pool: tuple, n_sims: int = 300,
                   shares=(0.0, 0.02, 0.05, 0.10), seasons=(4, 8, 13),
                   trailing_share: float = 0.05) -> pd.DataFrame:
    """Power with dispersion, date shocks and move shape taken from the real event table,
    and the narrowed H1 (trailing move as a control)."""
    epd = max(2, round(params.get("events_per_date_median", 10)))
    base = SimConfig(base_move=params["base_move_median"], sd_public=params["sd_log_implied"],
                     sd_date=params["sd_date_effect"], z_pool=z_pool, events_per_date=epd,
                     trailing_share=trailing_share)
    rows = []
    for share in shares:
        for s in seasons:
            cfg = base.with_(sd_private=private_sd_for_share(share, base.sd_public), n_seasons=s,
                             seed=7000 + int(share * 1000) + s)
            rows.append({"private_share": share, "seasons": s, "events_per_date": epd,
                         **run_scenario(cfg, n_sims=n_sims, trailing_control=True)})
    return pd.DataFrame(rows)
