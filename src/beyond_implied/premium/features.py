"""Variance-risk-premium features: who is paying for insurance, and is it underpriced?"""

from __future__ import annotations

import numpy as np
import pandas as pd


def term_structure_ratio(vix, vix3m):
    """VIX / VIX3M. Above 1 = inverted term structure (near-term stress priced above later)."""
    return vix / vix3m


def is_inverted(vix, vix3m):
    return term_structure_ratio(vix, vix3m) > 1.0


def variance_premium(implied_vol, forecast_vol):
    """Implied variance minus forecast variance. Positive = insurance priced above the forecast."""
    return np.square(implied_vol) - np.square(forecast_vol)


def premium_sign(implied_vol, forecast_vol):
    """+1 insurance looks overpriced, -1 underpriced (straddle favored), 0 equal."""
    return np.sign(variance_premium(implied_vol, forecast_vol))


def event_premium_ratio(implied_move, trailing_move):
    """Implied move / trailing realized move. Below 1 = the market prices less than history."""
    if isinstance(trailing_move, pd.Series):
        trailing_move = trailing_move.replace(0, np.nan)
    return implied_move / trailing_move
