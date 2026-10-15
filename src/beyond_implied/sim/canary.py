"""Look-ahead canary: a feature for an event must not change when outcomes on or after it change."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd


class LookAheadError(AssertionError):
    pass


def assert_no_lookahead(feature_fn: Callable[[pd.DataFrame], pd.Series], events: pd.DataFrame,
                        *, date_col: str = "announce_date", outcome_col: str = "realized_move",
                        n_checks: int = 25, seed: int = 0, atol: float = 1e-12) -> None:
    """Perturb outcomes on/after a cut date; features for events on that date must not move.

    `feature_fn(events) -> Series` aligned to events.index. Raises LookAheadError on a leak.
    """
    rng = np.random.default_rng(seed)
    base = feature_fn(events)
    dates = np.sort(events[date_col].unique())
    for cut in rng.choice(dates, size=min(n_checks, dates.size), replace=False):
        perturbed = events.copy()
        future = perturbed[date_col] >= cut
        perturbed.loc[future, outcome_col] = rng.uniform(0, 1, int(future.sum()))
        after = feature_fn(perturbed)
        at_cut = events[date_col] == cut
        a, b = base[at_cut].to_numpy(float), after[at_cut].to_numpy(float)
        same = np.isclose(a, b, atol=atol, equal_nan=True)
        if not same.all():
            raise LookAheadError(f"feature changed for events on {cut} when outcomes on/after it changed")
