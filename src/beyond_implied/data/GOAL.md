# GOAL — data

## Purpose

Get every input into a clean, reproducible local form, with raw downloads hashed and kept, and
quality problems flagged rather than silently fixed. Bad labels sink this project before bad models do.

## Inputs (sources)

| Need | Source | Module |
| --- | --- | --- |
| VIX, VIX3M, VIX9D, VVIX, SKEW daily history | Cboe `us_indices/daily_prices/{SYMBOL}_History.csv` | `cboe_indices.py` |
| Live option chains (forward) | Cboe `delayed_quotes/options/{SYMBOL}.json` (index symbols prefixed `_`) | `cboe_options.py` |
| Historical EOD option chains | ThetaData Terminal (free tier: 1 year) | `thetadata.py` (stub) |
| Earnings dates with timing flag | Any provider exported to CSV; FMP free tier later | `calendar.py` |
| Underlying daily OHLC | ThetaData stock EOD (same terminal) | `thetadata.py` (stub) |

## Outputs

- `data/raw/<source>/...` — raw downloads exactly as received, plus a `.meta.json` with fetch time
  (UTC), URL and SHA-256. Never committed.
- Parsed DataFrames with documented columns (see each module's docstring).
- Quality flags per row: zero bid, crossed quote, relative spread, gaps, outliers.

## Built in the scaffold

- `cboe_indices.py`: download, cache, parse, and quality report (gaps, non-positive values, large jumps).
  Verified reachable 2026-10-15.
- `cboe_options.py`: daily raw snapshot with hash sidecar; parser for OCC option symbols into
  `root, expiry, cp, strike` plus quote fields. Verified reachable 2026-10-15 (AAPL: 3,508 contracts).
- `calendar.py`: CSV loader that normalizes timing labels to `BMO` / `AMC` / `UNKNOWN`, plus the
  Nasdaq public calendar (one day per request, raw response kept with an as-of timestamp).
- `market_calendar.py`: NYSE trading days with 2026–2027 holidays.
- `daily.py` (`bi daily`): after the close, snapshots every name whose pre-event close (AMC today,
  BMO next trading day) or post-event close (BMO today, AMC previous day) is today, plus UNKNOWN
  timing for today/tomorrow; market cap ≥ $2B; ≤ 250 names; gzipped; run log in `_run.json`.
  First live run 2026-10-15: calendar rows 27/15/17 (today/next/prev); TSM, SCHW, PLD, HDB captured.
- `quality.py`: quote flags and universe filter.
- `thetadata.py`: interface only.

## Build steps (Phase 2)

1. `bi indices VIX VIX3M VIX9D VVIX SKEW`; read the quality report. Note the VIX methodology break
   (22 Sept 2003) and the odd early VVIX rows (March 2006). First run, 2026-10-15: VIX 9,294 rows
   (1990-01-02 to 2026-10-14), one flagged jump on 2018-02-05 (a real event, keep it); VVIX 5,125
   rows with a bad-looking 2006-03-15 value and 6 gaps over 5 business days (decide: start VVIX
   in 2007).
2. ~~Install the ThetaData Terminal.~~ Done 2026-10-15 with the official Python library instead
   (no Terminal, no Java): `thetadata.py` implements `eod_option_chain` and `eod_stock_ohlc`,
   throttled to ~24 requests/minute, raw responses cached. Free account checked on AAPL: option EOD
   history available back to at least 2023-10-26; 2022-10-27 and earlier are refused (paid tiers).
   That is roughly 13 earnings seasons (mid-2023 to Q3 2026), far more than the 4 planned.
3. ~~Check Cboe's option `iv` units.~~ Done 2026-10-15: per-contract `iv` is decimal, underlying
   `iv30` is percent. End-to-end check on the live AAPL chain: ATM straddle to the Oct 30 expiry
   implied a 3.8% move with a 5.8% relative spread.
4. Build the past-year calendar from Nasdaq's past dates (dates, EPS, surprise, analyst count are
   available; the timing flag is not). Infer timing from the larger overnight gap, flag it
   `inferred`, and measure the rule's accuracy on forward events whose timing was recorded.
5. Run quality flags over everything; write counts to `report/data_test.md`.

## Done when

- [ ] Index history for all five symbols downloaded and quality-checked.
- [ ] One year of EOD chains for ~100 liquid names cached locally.
- [ ] Calendar loaded; share of `UNKNOWN` timing reported.
- [ ] Daily forward snapshots running for names reporting in the next 10 trading days.

## Pitfalls

- Cboe endpoints are unofficial; check terms, keep request rates low, and cache.
- ThetaData retail is individual use: never commit or publish raw vendor data, only derived statistics.
- Delayed quotes after hours can be stale or zero-bid; flag, don't fill.
- Earnings dates move; record the calendar version used for each event.
