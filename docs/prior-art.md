# Prior art (Phase 1)

Compiled 2026-10-15. Each entry was opened at its source page; where only an abstract or a
summary was accessible, that is noted. One row per work.

## What changes because of this

1. **H1 as drafted is already answered for the simplest feature.** Two studies find that the
   history of a firm's earnings moves relative to the implied move predicts straddle returns
   (Xing & Zhang; the 2023 weekly-options study). So "a trailing-move signal adds information
   beyond the implied move" is known. **H1 is narrowed:** the scaffold must add information beyond
   *both* the implied move and the trailing/implied ratio. Adding a third, correlated regressor
   costs some power; re-run `bi power` with a three-regressor benchmark.
2. **The market's magnitude forecast is good.** Govindaraj et al. report that the option market
   correctly forecasts the size of the uncertainty jump around events. A null on H1 is a likely,
   reportable outcome.
3. **Literature-backed features beat speculative ones for the 6-feature budget.** Underpricing of
   earnings uncertainty is stronger for smaller firms, firms with less analyst coverage, higher past
   jump frequency and kurtosis, and more volatile past surprises (Xing & Zhang). Premiums concentrate
   in bellwether firms carrying market-wide volatility risk (Barth & So). Market cap and analyst
   count come free in the Nasdaq calendar; past-move dispersion comes from our own event history.
   Proposed v1 list: trailing/implied ratio (baseline), past-move kurtosis or jump frequency,
   log analyst count, log market cap, VIX/VIX3M, and at most one regime feature.
4. **Our two-expiry event-variance split has precedent** (Dubinsky, Johannes, Kaeck & Seeger), who
   also find anticipated announcement uncertainty is large, time-varying and predictive.
5. **Measurement is commoditized** (ORATS); **industry already applies ML** to earnings-driven
   implied-volatility shocks (Citi, 2022). The contribution here is a public, pre-registered,
   ledger-verified test, not the measurement or the use of ML.

## Entries

| # | Work | Question | Data / baseline | Finding | Use here |
| --- | --- | --- | --- | --- | --- |
| 1 | [Dubinsky, Johannes, Kaeck & Seeger (2019), *Review of Financial Studies* 32(2):646–687](https://ideas.repec.org/a/oup/rfinst/v32y2019i2p646-687..html) | How much of option prices reflects earnings-announcement risk? | Option prices; reduced-form models separating announcement uncertainty from ordinary volatility (abstract only) | Anticipated announcement uncertainty is large, time-varying, and predicts future volatility | Precedent for `event_variance_two_expiry` |
| 2 | Xing & Zhang, "Anticipating Uncertainty: Straddles Around Earnings Announcements" ([JFQA](https://resolve.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/anticipating-uncertainty-straddles-around-earnings-announcements/7B34877AD5E06304BA3C55FBA3219FDD); working-paper summary via [Alpha Architect](https://alphaarchitect.com/straddle-earnings-announcements-and-win/)) | Do straddles earn abnormal returns around earnings? | US equity options 1996–2010; ATM straddles around announcements | Straddles lose outside earnings but earn positive returns into announcements; underestimation stronger for small, low-coverage, high-jump, high-kurtosis, volatile-surprise firms; net of costs only viable for near-term options | Feature candidates; evidence that implied underprices some events |
| 3 | [Barth & So (2014), *The Accounting Review* 89(5):1579–1607](https://dspace.mit.edu/handle/1721.1/111118) | Do announcements carry priced market-wide volatility risk? | Option-implied premiums around earnings | Premiums rise with exposure to non-diversifiable volatility risk, concentrate in bellwether firms, and predict straddle returns | Game-theory/premium framing; bellwether or market-beta feature |
| 4 | ["The Efficiency of Weekly Option Prices around Earnings Announcements" (2023), *J. Risk Financial Manag.* 16(5):270](https://ideas.repec.org/a/gam/jjrfmx/v16y2023i5p270-d1145938.html) | Do historical vs implied earnings moves predict weekly straddle returns? | Weekly options near announcements; portfolio sorts and Fama–MacBeth | Straddle returns higher when historical earnings move is high relative to implied; no association with HV, IV, or HV−IV | The baseline to beat; H1 narrowed |
| 5 | [Govindaraj, Jin, Livnat & Zhao (2014), SSRN](https://wallstreethorizon.com/news/Govindaraj) | Do implied volatilities predict absolute returns around events? | Earnings dates and shareholder meetings (vendor summary only) | Option market correctly forecasts the magnitude of the uncertainty jump; IV complements historical volatility | Sets expectations: null on H1 is plausible |
| 6 | [Goyal & Saretto (2009), *Journal of Financial Economics*, 310–326](https://academicnewsletter.sufe.edu.cn/info/357238) | Does HV − IV predict option returns cross-sectionally? | Monthly sorts on historical minus ATM implied volatility | Long-short straddle strategy earns significant returns not explained by risk factors | Related baseline (HV/IV); robustness check |
| 7 | [Busch, Christensen & Nielsen (2011), *Journal of Econometrics*](https://www.econ.queensu.ca/research/working-papers/1181) | Does IV add information to HAR forecasts of realized volatility? | FX, stock, bond; HAR with continuous/jump components | IV adds incremental information, is unbiased in stocks and FX | Index arena is a control; null expected |
| 8 | [Corsi (2009), *J. Financial Econometrics* 7(2):174](https://academic.oup.com/jfec/article/7/2/174/856522) | Simple long-memory model of realized volatility | Daily/weekly/monthly RV components | HAR-RV: the standard hard-to-beat baseline | `forecasters/har.py` |
| 9 | [Patton (2011), *Journal of Econometrics* 160(1):246–256](https://scholars.duke.edu/publication/792433) | Which loss functions rank variance forecasts correctly with noisy proxies? | Analytical; IBM 1993–2003 | Only "robust" loss functions (MSE, QLIKE family) preserve rankings | QLIKE in `metrics/second_order.py` |
| 10 | [Hansen, Lunde & Nason (2011), *Econometrica* 79(2):453–497](https://ideas.repec.org/a/ecm/emetrp/v79y2011i2p453-497.html) | Which models are statistically indistinguishable from the best? | Model Confidence Set | Set-valued comparison with controlled error | Phase 4 multi-model comparison |
| 11 | [Gibbs & Candès (2021), NeurIPS](https://proceedings.neurips.cc/paper/2021/hash/0d441de75945e5acbc865406fc9a2559-Abstract.html) | Conformal coverage under distribution shift | Online adaptive α update | Long-run coverage guarantees without exchangeability | `metrics/conformal.py` (ACI) |
| 12 | [ORATS (2026-02-12)](https://orats.com/blog/earnings-straddles-strong-season-2026) | Practitioner tracking of implied vs actual earnings moves | ATM straddle minus residual time value; price > $10, option volume > 300 | Seasons rotate between regimes; Jan–Feb 2026 straddles ≈ +45% vs ≈ −2% over 12 prior quarters | Phase 2 sanity check; filters |
| 13 | [Risk.net on Citi's model (2022-11-07)](https://www.risk.net/node/7955019) | Industry ML for earnings shocks to IV surfaces | Paywalled; headline and subtitle only | ML forecasts effect of shocks on IV surfaces in minutes | Industry prior art; differentiate on openness and verification |

## Data finding from this pass

The Nasdaq calendar returns past dates with EPS, surprise, consensus and analyst count, but the
before-open/after-close flag is missing for past dates (all `time-not-supplied` for 79, 91 and 170
names ≥ $2B on 2025-10-22, 2026-07-23 and 2026-04-29). Consequences:

- Forward runs must keep each day's calendar response (they do).
- Retrospective seasons need timing inferred, e.g. from which overnight gap is larger
  (close D−1 → open D vs close D → open D+1), flagged as inferred.
- The inference rule can be validated on Q3 2026 forward events, where Nasdaq gave the timing.

## Not yet covered

- Christensen & Prabhala (1998) and the implied-vs-realized bias literature (classic; not opened).
- Analyst-coverage and earnings-surprise predictability (post-earnings drift) beyond entry 2.
