# IV-collapse timing: validation

Reference = recorded timing where available, else the company's habitual timing.
Coverage = share of reference events the rule classifies; accuracy = agreement among those.

| Min ratio | Coverage | Accuracy | n classified |
| --- | --- | --- | --- |
| 1.25 | 86.2% | 93.6% | 3790 |
| 1.5 | 85.1% | 93.8% | 3739 |
| 2.0 | 82.7% | 94.2% | 3637 |
| 3.0 | 78.9% | 94.6% | 3469 |

- Events with a reference: 4396; against recorded timing only: 96.0% of 75.
- Events with no reference timing: 1986; the rule classifies 82.4% of them at ratio ≥ 1.5.
- Names with no reference timing: 153.

## Scale check

At 100 names (2026-10-16): 94.5% coverage, 96.1% agreement on 763 reference events. At 500 names
(2026-10-17, above): 85.1% coverage, 93.8% agreement on 4,396 reference events; 96.0% against
recorded timing only (75 events). Agreement falls slightly as smaller names are added (not yet
explained). The rule and its 1.5 threshold are unchanged; IV-timed events are reported separately.
