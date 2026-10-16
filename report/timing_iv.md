# IV-collapse timing: validation

Run 2026-10-16 on the Mac with `bi timing-iv` (100 names, 1,307 announcements, July 2023 – October 2026).
The rule dates each report by the close at which front-expiry ATM implied volatility collapses
(≥ 2 vol points); it never looks at the stock move.

Reference = recorded timing where available, else the company's habitual timing.
Coverage = share of reference events the rule classifies; accuracy = agreement among those.

| Min ratio | Coverage | Accuracy | n classified |
| --- | --- | --- | --- |
| 1.25 | 95.4% | 96.2% | 728 |
| 1.5 | 94.5% | 96.1% | 721 |
| 2.0 | 93.2% | 96.1% | 711 |
| 3.0 | 89.9% | 96.4% | 686 |

- Events with a reference: 763; against recorded timing only: 100.0% of 11.
- Events with no reference timing: 544 (41 names); the rule classifies 86.4% of them at ratio ≥ 1.5.

**Decision:** passes the ≥ 95% bar. Pre-registered as the fallback timing source at ratio ≥ 1.5.
Accuracy is flat across thresholds, so the choice is not tuned. About 4% of IV-timed events are
expected to be mis-timed; results are reported with and without IV-timed events.
