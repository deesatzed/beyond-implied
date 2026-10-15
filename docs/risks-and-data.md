# Risks and Data

*Source: "Forecasting Lab: Risks and Data" Claude Doc, 2026-10-15.*

The data is easy to get; the project fails on three things: no edge left beyond implied vol, a result that
is one regime's luck, and a scope that never closes.

## Data availability

| Data need | Source | Cost | Catch |
| --- | --- | --- | --- |
| VIX, VIX3M, VIX9D, SKEW, VVIX | Cboe `cdn.cboe.com/api/global/us_indices/daily_prices/{SYMBOL}_History.csv` | Free | VIX close from 1990; methodology changed Sept 2003; VVIX file has odd early rows (2006) to clean |
| Historical option chains | ThetaData | Free: 1 year EOD; $40 / $80 / $160 per month retail | Retail is individual use; publish derived stats only. Standard tier has tick-level options from 2016 |
| Bulk EOD option history | HistoricalOptionData.com | One month of SPX for $3.85 | Bulk history from 2002 |
| Live chains (forward) | Cboe `cdn.cboe.com/api/global/delayed_quotes/options/{SYMBOL}.json` | Free | Unofficial; check terms. Verified reachable 2026-10-15 |
| Live chains (fallback) | yfinance | Free | Repeated rate limits; Yahoo blocks IPs |
| Earnings calendar | FMP free tier (250 calls/day) or manual CSV | Free | Dates move; need before-open/after-close flag and confirmation status |

## Failure modes, most likely first

1. **No edge in the index arena.** Implied vol adds information beyond past realized vol and is unbiased
   in stocks (Busch, Christensen & Nielsen). Treat the index as the control arena.
2. **Regime luck.** ORATS: earnings straddles averaged about +45% in the season ending February 2026,
   against roughly −2% across the prior twelve quarters. Use multiple seasons.
3. **Label errors.** Stale quotes, zero bids, mid vs bid-ask, wrong timing flags. Strip residual time
   value; filter price ≥ $10 and option volume ≥ 300.
4. **The simplest baseline may already explain it.** A 2023 study: straddle returns higher when the
   historical earnings move is large relative to the implied move. That ratio is the baseline to beat.
5. **The innovative pieces are the weakest empirically.** Design the project to succeed even if entropy
   and chaos features add nothing.
6. **Small effective N and forking paths.** Cluster by date, pre-register, keep features few.
7. **The measurement is a commodity.** ORATS publishes weekly implied-vs-actual summaries. The
   contribution is the forecast, the abstention rule and the public ledger.
8. **Scope.** v1: earnings arena only, done by December 1.

## Sources

- ORATS, "Earnings Straddles Are Having Their Moment" (2026-02-12): https://orats.com/blog/earnings-straddles-strong-season-2026
- "The Efficiency of Weekly Option Prices around Earnings Announcements" (JRFM, 2023): https://ideas.repec.org/a/gam/jjrfmx/v16y2023i5p270-d1145938.html
- Busch, Christensen & Nielsen: https://www.econ.queensu.ca/research/working-papers/1181
- Swansea WP2019-03: https://rahwebdav.swan.ac.uk/repec/pdf/WP2019-03.pdf
- ThetaData subscriptions: https://docs.thetadata.us/Articles/Getting-Started/Subscriptions.html
- ThetaData pricing: https://thetadata.net/pricing
- HistoricalOptionData.com: https://historicaloptiondata.com/historical-options-prices/
- Cboe delayed quotes API listing: https://apis.io/providers/cboe/
- yfinance rate limiting: https://github.com/ranaroussi/yfinance/issues/2480
