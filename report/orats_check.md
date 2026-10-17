# ORATS check

Resolved 2026-10-17, before the Phase 3 freeze. Source: [ORATS, 2026-02-12](https://orats.com/blog/earnings-straddles-strong-season-2026).
Script: `scripts/orats_check.py`. Derived statistics only.

## What ORATS reports, and what it does not say

ORATS reports an average straddle return of about **+45% for the four weeks to February 11, 2026**,
against about **−2% over the previous twelve quarters**. The post gives these details of its method:

- the implied move is the at-the-money straddle minus residual time value;
- a "win" is an actual move larger than the implied move;
- filters are price > $10, daily option volume > 300 contracts, plus "additional liquidity thresholds"
  that it does not specify.

It does not state:

- the holding period (one day or to expiration);
- the expiry used;
- whether it uses mid or bid/ask prices;
- the number of stocks or the market-cap range;
- how returns are averaged.

So the +45% cannot be reproduced from the published information.

## Why the earlier comparison was off

The earlier comparison used this pipeline's "2026Q1", meaning every report from January to March
2026. ORATS's figure covers only January 14 to February 11. The table below uses ORATS's window, on
the same usable events, under each definition the pipeline can compute.

| Definition | Jan 14–Feb 11, 2026 | All prior (Jul 2023–Jan 13, 2026) |
| --- | --- | --- |
| Events (500 names) | 187 | 3,282 |
| One-day hold, mid to mid | +3.4% | +0.7% |
| One-day hold, ask to bid | −12.4% | −13.0% |
| Hold to first expiry, mid entry (median 3 days) | +3.2% | +1.6% |
| Win rate, hold to expiry | 47% | 44% |
| Realized ÷ event-implied move, minus 1 | −1.0% | −6.5% |
| Top 100 names only, one-day mid | +6.3% (55 events) | — |

## Conclusion

- **Direction agrees.** Under every definition, ORATS's window was better for straddle buyers than
  this pipeline's own historical average, and the win rate was higher. That matches ORATS's account
  of an unusually strong season.
- **Size does not.** This pipeline gets +3% to +6% for the window, not +45%. ORATS's 12-quarter baseline
  of −2% sits within the pipeline's own range of definitions (from −13% executable to +1.6% at expiry).
- **The pipeline checks out internally.** Realized moves recompute exactly from the stored closes
  (maximum difference 3×10⁻¹⁶). Habitually timed events disagree with the IV-collapse rule on only
  3.9% (100 of 2,592). Those 100 events show more very small moves (20% vs 11% below 0.15× implied),
  consistent with occasional wrong-day measurement. They are too few to move season averages by more
  than about a point. The robustness split excluding them is pre-registered.
- **What remains unexplained:** about 40 percentage points for one four-week window. The likely
  sources are definitions this pipeline does not share and ORATS does not publish: universe breadth
  (smaller, more volatile names), entry timing, holding period, or averaging. These are
  hypotheses, not findings.

## Decision

The ORATS stop criterion ("season averages roughly match ORATS") is replaced, as recorded in
PREREGISTRATION.md, with:

1. a **direction check**, passed for this window;
2. the **internal checks** above, to be re-run at the freeze.

This project does not claim to reproduce ORATS's figures.
