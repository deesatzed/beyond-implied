"""Align an earnings announcement to its pre-event and post-event closes."""

from __future__ import annotations

import bisect
import datetime as dt
from collections.abc import Sequence


def pre_post_dates(announce: dt.date, timing: str,
                   trading_days: Sequence[dt.date]) -> tuple[dt.date, dt.date]:
    """Return (pre_date, post_date) as trading days.

    BMO on D: pre = last trading day strictly before D; post = first trading day on/after D.
    AMC on D: pre = last trading day on/before D; post = next trading day after pre.
    Raises ValueError for UNKNOWN timing or when the calendar does not cover the event.
    """
    days = sorted(trading_days)
    if timing == "BMO":
        i = bisect.bisect_left(days, announce)
        if i == 0 or i >= len(days):
            raise ValueError(f"trading calendar does not cover BMO event on {announce}")
        return days[i - 1], days[i]
    if timing == "AMC":
        i = bisect.bisect_right(days, announce) - 1
        if i < 0 or i + 1 >= len(days):
            raise ValueError(f"trading calendar does not cover AMC event on {announce}")
        return days[i], days[i + 1]
    raise ValueError(f"cannot align timing {timing!r}; only BMO and AMC are usable")
