"""Market-wide scheduled events (FOMC, CPI) inside an earnings event's return window.

The event window runs from the pre-event close to the post-event close, so a release counts when
it falls on the post-event date: CPI (8:30 am) and FOMC (2:00 pm) both land inside that session.
For an after-close report on day D, an FOMC statement on D (2 pm) is before the window opens.
"""

from __future__ import annotations

import datetime as dt
from functools import lru_cache

import pandas as pd

from ..config import load_toml, project_root


@lru_cache(maxsize=1)
def macro_dates() -> dict[str, frozenset]:
    cfg = load_toml(project_root() / "config" / "macro_events.toml")
    return {k: frozenset(dt.date.fromisoformat(d) for d in cfg[k]) for k in ("fomc", "cpi")}


def macro_in_window(post_date) -> dict:
    d = pd.Timestamp(post_date).date()
    m = macro_dates()
    fomc, cpi = d in m["fomc"], d in m["cpi"]
    return {"macro_fomc": fomc, "macro_cpi": cpi, "macro_event": fomc or cpi}
