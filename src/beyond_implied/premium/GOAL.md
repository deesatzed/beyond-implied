# GOAL — premium (game-theory features)

## Purpose

Treat implied volatility as an equilibrium price, not a neutral forecast. Hedgers buy insurance,
sellers collect premium, and implied usually exceeds realized (the variance risk premium). Straddles
pay when that equilibrium breaks. The target here is the **sign of the premium**: when is the
insurance underpriced?

## Inputs

- VIX, VIX3M, VVIX (market-wide stress and crowding proxies).
- Event implied move and the trailing realized move (single-name premium).
- Scaffold variance forecast (for the forecast-based premium).

## Outputs

Per event: `vix_vix3m` (term-structure ratio; >1 = inverted), `vvix`, `event_premium_ratio`
(implied / trailing), `premium_sign` (sign of implied² − forecast²).

## Built in the scaffold

- `features.py`: `term_structure_ratio`, `is_inverted`, `variance_premium`, `premium_sign`,
  `event_premium_ratio`.

## Build steps (Phase 5)

1. Join VIX, VIX3M and VVIX closes to each event's pre-event date (previous close; no same-day data
   for AMC events beyond the close).
2. Compute the features; check their distributions by season (regime rotation shows up here first).
3. Enter at most two premium features into the scaffold model.
4. Use `vix_vix3m` and `vvix` in the draft stress gate (`config/gates.toml`, G7); fix thresholds in
   Phase 3 from training seasons only.

## Done when

- [ ] Features joined without look-ahead.
- [ ] Season-level table of premium sign vs straddle outcome (training seasons).

## Pitfalls

- Dealer gamma positioning is the most direct game-theory signal, but good data is paid. Do not
  add it unless a free, documented history exists.
- Market-wide features vary by date, not by event: their effective N is the number of dates.
  Cluster by date (already the plan).
