"""Planted-signal earnings seasons with known ground truth.

Generative model, per event i on announcement date d (log scale):

    v_i  ~ N(0, sd_public)        information the market prices
    x_i  ~ N(0, sd_private)       information only the model has (the planted signal)
    t_i  ~ N(0, sd_trailing)      information the market misses but trailing moves capture
    m_i  = log(base_move) + v_i + x_i + t_i    true log expected move
    TR_i = exp(log(base_move) + v_i + t_i + n_i)  trailing-move baseline (n_i = averaging noise)
    IM_i = exp(log(base_move) + v_i + premium_s + e_i),  e_i ~ N(0, sd_market_noise)
    F_i  = IM_i * exp(-premium_bar + x_i + f_i),         f_i ~ N(0, sd_model_noise)
    |r_i| = exp(m_i + u_d) * |z_i|,  z_i ~ N(0, 1) scaled so E|z| = 1,  u_d ~ N(0, sd_date)

The model forecast is built only from what is observable (the implied move), a long-run premium
correction `premium_bar` (it does not know the current season's premium), and the planted x_i.
With sd_private = 0 the model is the implied move times independent noise: it carries no extra
information, so the encompassing test should reject at about its nominal size.
`premium_s` is the season's variance risk premium in log terms (positive = implied overprices).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SimConfig:
    n_seasons: int = 4
    dates_per_season: int = 35
    events_per_date: int = 15
    base_move: float = 0.045
    sd_public: float = 0.50
    sd_private: float = 0.0
    sd_market_noise: float = 0.10
    sd_model_noise: float = 0.10
    sd_date: float = 0.25
    premium: float = 0.10
    regime_flip: bool = False         # alternate the premium's sign by season
    catastrophe: bool = False         # one event with a 10x move in the last season
    trailing_share: float = 0.0       # market-missed info that trailing moves capture (not the model)
    sd_trailing_noise: float = 0.35   # noise in a 12-event trailing average, log scale
    z_pool: tuple = ()                # empirical realized/expected shapes to resample (mean ~1)
    seed: int = 0

    def with_(self, **kw) -> SimConfig:
        return replace(self, **kw)


def private_sd_for_share(share: float, sd_public: float = 0.50) -> float:
    """sd_private such that private info is `share` of the variance of the true log expected move."""
    if not 0.0 <= share < 1.0:
        raise ValueError("share must be in [0, 1)")
    return sd_public * math.sqrt(share / (1.0 - share))


def simulate_events(cfg: SimConfig) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.seed)
    n_dates = cfg.n_seasons * cfg.dates_per_season
    n = n_dates * cfg.events_per_date
    date_idx = np.repeat(np.arange(n_dates), cfg.events_per_date)
    season = date_idx // cfg.dates_per_season

    premium = np.full(cfg.n_seasons, cfg.premium)
    if cfg.regime_flip:
        premium = np.where(np.arange(cfg.n_seasons) % 2 == 0, cfg.premium, -cfg.premium)

    v = rng.normal(0, cfg.sd_public, n)
    x = rng.normal(0, cfg.sd_private, n) if cfg.sd_private > 0 else np.zeros(n)
    e = rng.normal(0, cfg.sd_market_noise, n)
    f = rng.normal(0, cfg.sd_model_noise, n)
    u = rng.normal(0, cfg.sd_date, n_dates)[date_idx]
    if cfg.z_pool:
        pool = np.asarray(cfg.z_pool, dtype=float)
        z = rng.choice(pool / pool.mean(), size=n, replace=True)
    else:
        z = np.abs(rng.standard_normal(n)) * math.sqrt(math.pi / 2.0)  # E|z| = 1
    sd_t = private_sd_for_share(cfg.trailing_share, cfg.sd_public) if cfg.trailing_share else 0.0
    xt = rng.normal(0, sd_t, n) if sd_t > 0 else np.zeros(n)
    nt = rng.normal(0, cfg.sd_trailing_noise, n)

    log_base = math.log(cfg.base_move)
    true_log = log_base + v + x + xt
    realized = np.exp(true_log + u) * z
    if cfg.catastrophe:
        realized[-1] = 10.0 * np.exp(true_log[-1])

    implied = np.exp(log_base + v + premium[season] + e)
    premium_bar = float(premium.mean())
    return pd.DataFrame({
        "date": date_idx,
        "season": season,
        "implied_move": implied,
        "f_model": implied * np.exp(-premium_bar + x + f),
        "f_trailing": np.exp(log_base + v + xt + nt),
        "true_expected": np.exp(true_log),
        "realized_move": realized,
    })
