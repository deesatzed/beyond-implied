# GOAL — regime (chaos and entropy features)

## Purpose

Test, falsifiably, whether the complexity of recent price action carries information about the
size of the next move beyond what the implied move and trailing moves already hold.
Hypothesis: a loss of complexity (more ordered recent returns) precedes variance expansion.

## Inputs

Daily log returns of the underlying (and of SPX for the index arena), in windows ending at the
pre-event close.

## Outputs

Per event: `perm_entropy`, `dfa_alpha`, `recurrence_rate`, each computed on a fixed window.

## Built in the scaffold

- `features.py`:
  - `permutation_entropy(x, order=3, delay=1)` (Bandt–Pompe, normalized 0..1)
  - `dfa_alpha(x)` (detrended fluctuation analysis; ≈0.5 for white noise)
  - `recurrence_rate(x, dim=2, delay=1, eps=None)`

## Build steps (Phase 5)

1. Fix one window length per feature before looking at outcomes (proposal: 60 trading days).
2. Compute features for every event using returns strictly before the pre-event close.
3. Check feature stability: correlation between adjacent windows; drop any feature that is noise.
4. Enter at most two regime features into the scaffold model (feature budget is 6 total).
5. Report the result whatever its sign. A clean null against HAR-IV and the ratio baseline is a
   contribution: the published literature is mostly in-sample, single-episode studies.

## Done when

- [ ] Features computed for all events with a no-look-ahead test.
- [ ] Their incremental coefficient reported in the encompassing regression on held-out seasons.

## Pitfalls

- Lyapunov exponents on noisy daily returns are unreliable; not used for that reason.
- Short windows make permutation entropy noisy; long windows make it slow.
- Ties in prices bias ordinal patterns; use returns, not prices.
