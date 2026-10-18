"""Smoke test: Timestral-209M zero-shot forecast of daily absolute returns for one cached symbol.

Run on the machine with the ThetaData cache: `python scripts/timestral_smoke.py AAPL`.
Prints only summary statistics (no vendor data). Exploratory; not part of any scored test.
"""

import glob
import sys
import time

import numpy as np
import pandas as pd


def closes(sym: str) -> pd.Series:
    files = glob.glob(f"data/raw/thetadata/stock_eod/{sym.upper()}_*.csv.gz")
    raw = pd.concat([pd.read_csv(f) for f in files])
    raw["date"] = pd.to_datetime(raw["created"].astype(str).str[:10])
    return raw.drop_duplicates("date", keep="last").set_index("date")["close"].sort_index()


def main(sym: str = "AAPL", horizon: int = 21) -> None:
    from timestral import TimestralForecaster

    c = closes(sym)
    absret = np.abs(np.log(c).diff().dropna())
    context, future = absret.iloc[:-horizon], absret.iloc[-horizon:]
    t0 = time.time()
    model = TimestralForecaster.from_pretrained("mistralai/Timestral-209M")
    load_s = time.time() - t0
    t1 = time.time()
    fc = model.forecast(context.to_numpy(dtype=np.float32), prediction_length=horizon)
    run_s = time.time() - t1
    med = np.asarray(fc.median).ravel()
    q10 = np.asarray(fc.quantile(0.1)).ravel()
    q90 = np.asarray(fc.quantile(0.9)).ravel()
    inside = np.mean((future.to_numpy() >= q10) & (future.to_numpy() <= q90))
    print(f"{sym}: context {len(context)} days, horizon {horizon}")
    print(f"load {load_s:.1f}s, forecast {run_s:.2f}s")
    print(f"mean forecast median |r| {med.mean():.4f} vs realized {future.mean():.4f} "
          f"vs trailing-21 {context.iloc[-21:].mean():.4f}")
    print(f"share of realized days inside 10-90% band: {inside:.0%}")


if __name__ == "__main__":
    main(*(sys.argv[1:2] or ["AAPL"]))
