# GOAL — events

## Purpose

Turn calendars, chains and prices into one row per earnings event with a trustworthy label:
the implied move the market priced and the move that happened. This table is the dataset.

## Inputs

- Earnings calendar (`data/calendar.py`): symbol, date, timing (BMO / AMC / UNKNOWN).
- Option chain at the pre-event close (`data/cboe_options.py` or `data/thetadata.py`).
- Underlying closes around the event.
- Trading-day calendar (derived from the underlying's price history).

## Outputs

One row per event: `symbol, announce_date, timing, pre_date, post_date, spot, expiry_1, expiry_2,
straddle_mid, rel_spread, zero_bid, implied_move_simple, event_var, implied_move_event, pre_close,
post_close, realized_move, quality_ok`.

## Definitions (also in PREREGISTRATION.md)

- **BMO on day D:** pre = close of the last trading day before D; post = close of D.
- **AMC on day D:** pre = close of D; post = close of the next trading day.
- **Realized move:** `|post / pre − 1|`.
- **Implied move (simple):** ATM straddle mid / spot, first expiry on or after the post date.
- **Implied move (event):** two-expiry extraction. With total implied variance `w_i = iv_i² · t_i`
  for two expiries after the event, base variance rate `σ_b² = (w_2 − w_1)/(t_2 − t_1)`, event
  variance `e = w_1 − σ_b² · t_1`, and expected absolute move `√(2/π) · √e`. Negative `e` is flagged.

## Built in the scaffold

- `timing.py`: `pre_post_dates` for BMO/AMC with a trading-day list.
- `moves.py`: simple implied move, two-expiry event variance, expected absolute move, realized move.
- `straddle.py`: ATM strike selection and straddle quote from a parsed chain.
- `invariants.py`: admissibility checks with IDs (I1–I11): timing usable, pre before post, expiry
  on/after post (and not too far), positive spot/straddle/close, implied move in (0, 1), non-negative
  realized move and spread; negative event variance is a warning. Errors exclude a row.

## Build steps (Phase 2)

1. Build the trading-day list from underlying closes.
2. For each calendar event with BMO/AMC timing, locate pre/post dates and closes.
3. Select first and second expiries after the post date (first within
   `max_days_to_first_expiry`); compute both implied-move definitions.
4. Attach quality flags; run `check_events`; mark `quality_ok` using the universe filter and the
   absence of invariant errors.
5. Write the table to `data/processed/events.parquet` (gitignored) and season summaries to
   `report/data_test.md`.
6. Sanity check: season-average implied and realized moves against ORATS's published figures.

## Done when

- [ ] Event table built for ~100 names over ~4 seasons (quality test), then scaled toward ~2,000
      usable events for H1 (`report/power.md`).
- [ ] Share of events failing quality is reported, by invariant check ID.
- [ ] Season averages roughly match ORATS.
- [ ] Unit tests cover BMO/AMC alignment, weekends/holidays, and the variance extraction.

## Pitfalls

- Wrong timing flag = wrong straddle = garbage label. Exclude UNKNOWN; never guess.
- Weekly expiries: the first expiry may be the day after the event; residual time value is small
  but nonzero. The event definition handles it; the simple definition overstates slightly.
- Splits and symbol changes around the event.
