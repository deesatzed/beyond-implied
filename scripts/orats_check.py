"""ORATS comparison (2026-10-17): hold-to-expiry straddle payoff on usable events. Derived stats only.

Run from the repo root on the machine with the ThetaData cache: `python scripts/orats_check.py`.
"""
import glob
import tomllib
from pathlib import Path

import pandas as pd

from beyond_implied.phase2 import _usable

cfg = tomllib.loads(Path("config/universe.toml").read_text())
e = pd.read_csv("data/processed/events.csv.gz", parse_dates=["announce_date", "expiry_1"])
e["usable"] = _usable(e, cfg)
u = e[e.usable].copy()
rows = []
for sym, g in u.groupby("symbol"):
    files = glob.glob(f"data/raw/thetadata/stock_eod/{sym.upper()}_*.csv.gz")
    if not files:
        continue
    raw = pd.concat([pd.read_csv(f) for f in files])
    raw["date"] = pd.to_datetime(raw["created"].astype(str).str[:10])
    c = raw.drop_duplicates("date", keep="last").set_index("date")["close"].sort_index()
    for r in g.itertuples():
        ex = c[c.index <= r.expiry_1]
        if len(ex) and r.straddle_mid > 0:
            rows.append({"symbol": sym, "announce_date": r.announce_date,
                         "ret_expiry": abs(ex.iloc[-1] - r.strike) / r.straddle_mid - 1,
                         "days": (r.expiry_1 - r.announce_date).days,
                         "ret_1d_mid": r.straddle_ret_mid})
d = pd.DataFrame(rows)
win = (d.announce_date >= "2026-01-14") & (d.announce_date <= "2026-02-11")
for label, x in [("ORATS window 2026-01-14..02-11", d[win]), ("all prior (2023-07..2026-01-13)", d[d.announce_date < "2026-01-14"])]:
    print(f"{label}: n={len(x)} hold-to-expiry mean {100*x.ret_expiry.mean():+.1f}% "
          f"median {100*x.ret_expiry.median():+.1f}% win {100*(x.ret_expiry>0).mean():.0f}% "
          f"| 1-day mid mean {100*x.ret_1d_mid.mean():+.1f}% | median days to expiry {x.days.median():.0f}")
# 12 prior ORATS-style windows (weeks 2-6 after quarter end)
for q in pd.period_range("2023Q2", "2025Q3", freq="Q"):
    s = q.end_time.normalize() + pd.Timedelta(days=14)
    x = d[(d.announce_date >= s) & (d.announce_date < s + pd.Timedelta(days=28))]
    print(str(q), len(x), f"{100*x.ret_expiry.mean():+.1f}%")
