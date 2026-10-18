# GOAL — Challenger C1: open-world AI-elicited expert system (ESS)

Status: **specified, not built.** Revised 2026-10-17 from a fixed-input network to an open-world one.
The fixed-input version is kept as ablation C1-closed (below). C1 is pre-registered and frozen
alongside v1, then logs forward predictions from the freeze onward. Its promotion test is the
Phase 9 rule in BUILD.md.

## Question

For a given instrument and forecast origin, an LLM can name any factor it judges to drive that
instrument's volatility: company-specific, sector, supply chain, macro, policy and political,
legal, weather and climate, geopolitical, or strategic (game-theoretic). Each factor becomes a
node with a probability distribution over its state and over its effect on the move. Numerical
inference combines the nodes into a predictive distribution of move size.

**Does that forecast carry information about realized move size beyond the option market's
implied move and the v1 champion?** Direction is never forecast.

The node list is not fixed in advance. Which factors matter, and how much, is the model's job for
each instrument and date. Nothing in this file names required factors; examples elsewhere are
illustrations only.

## Units forecast

1. **Earnings events** (primary). Every population event (PREREGISTRATION.md, Study population)
   reporting after the freeze. Target: the absolute one-day event move. This reuses the v1
   pipeline, the daily snapshots and the scoring rules. It gives about 10–30 forecasts per trading
   day in season.
2. **Non-earnings panel** (secondary). A frozen list of liquid optionable ETFs covering sectors,
   commodities, rates and currencies, chosen at the freeze by liquidity rules, not by topic.
   Weekly origins. Target: realized volatility over the next 21 trading days, compared with
   30-day implied volatility. This is where factors outside any single company carry the most
   weight.

## How one forecast is made

1. **Context snapshot.** At the origin, before the pre-event close, fetch the allowed context
   sources (below). Store them verbatim, with retrieval time and SHA-256. The model sees only
   this snapshot plus its own training knowledge.
2. **Elicit.** The LLM gets the instrument, the origin, the horizon, the allowed pre-event market
   inputs and the snapshot. It returns a spec in `spec_schema.md` (v2) form:
   - nodes of any kind, each with a state distribution (median and range, or category
     probabilities);
   - for each node, its effect on the move as a multiplier distribution (median and range);
   - parents, and a dependency group for nodes that share a cause, so correlated evidence is not
     counted twice;
   - for strategic nodes (game-theoretic), the players, their options and the payoff logic behind
     the outcome distribution, in one or two lines each;
   - a citation from the snapshot, or "prior knowledge", for every node.
3. **Validate.** `spec.py` rejects outcome or post-event fields, medians outside ranges, cycles,
   unknown parents, missing units, missing citations and unbounded effects.
4. **Combine numerically.** Monte Carlo over node states, respecting parents and dependency
   groups, produces the predictive distribution: median, 10th and 90th percentiles, and mean.
   The LLM never states the final probability itself.
5. **Seal.** The prompt, model ID, stated training cutoff, snapshot hash, raw response, validated
   spec and predictive distribution are written to the ledger before the pre-event close.
   Nothing is revised afterward.

## Arms (pre-registered, run on the same units)

| Arm | What it sees and does | Question it answers |
| --- | --- | --- |
| C1-open | Full open-world ESS, anchored to the implied move (effects multiply the implied move) | The main question |
| C1-open-unanchored | Same, but anchored to the trailing move; the implied move is hidden | Does it add information independently of the market? |
| C1-closed | Nodes limited to market-internal inputs (the original fixed catalogue) | Do outside-the-market factors add value? (C1-open vs C1-closed) |
| C1-direct | Same model and snapshot; asked for median and range directly, no network | Does the ESS structure add value over a plain LLM guess? |

## Scoring (same rules as v1)

- **Primary:** the pooled encompassing regression of the realized move on the implied move, the
  trailing move, the v1 champion and C1-open, normalized by the implied move and clustered by
  announcement date (panel: clustered by week).
- **Secondary:** QLIKE; quantile loss of the 10th and 90th percentiles; interval coverage; PIT;
  risk at matched coverage.
- **Ablation contrasts** as in the table.
- **Reporting:** by node category (which kinds of factors the forecasts leaned on), and LLM cost
  per scored forecast.

## Contamination rules

- **Forward only.** Every scored forecast is sealed before its outcome exists, and after the
  eliciting model's stated training cutoff.
- **Retrospective runs are exploratory, never scored.** The LLM may know how past events turned out.
- **The snapshot is the only fresh information.** No live browsing during elicitation. Snapshot
  sources are fixed at the freeze.
- **Model version is pinned for the season.** A model change is a new challenger.

## Allowed context sources (fixed at the freeze; access to be verified before it)

Each source is fetched only through a recorded call at the origin:

- company filings and press releases (SEC EDGAR);
- scheduled macro and policy calendars (already in `config/macro_events.toml`);
- official agency outlooks (for example NOAA, USDA, EIA);
- prediction-market prices for scheduled events;
- a headline feed restricted to items published before the origin.

Sources that cannot be fetched reproducibly are excluded rather than approximated.

## Allowed market inputs

The v1 pre-event columns: `implied_move_event`, `implied_move_simple`, `f_trailing`, `trailing_n`,
`past_move_kurtosis`, `market_cap`, `n_estimates`, `eps_forecast`, `rel_spread`, `vix`, `vix_vix3m`,
`vvix`, `sector`, `timing`, `days_to_expiry_1`. Forbidden fields are as before: `realized_move`,
`post_close`, `eps`, `surprise_pct`, straddle returns, `timing_inferred`, and anything computed after
the pre-event close.

## Human role

Too many forecasts are made each day to review each one before sealing. The person reviews and
freezes:

- the prompt;
- the snapshot sources;
- the validator;
- the combination code.

A random 5% of sealed specs are audited after the fact for nonsense nodes, and the audit findings
are published. Edits to individual forecasts are not allowed.

## Cost and limits

The rough estimate, to be confirmed in a dry run, is a few cents per forecast through OpenRouter
(key in `.env`). There is a hard daily spend cap. If the cap is hit, the remaining events are marked
NOT_FORECAST, never filled in later.

## Promotion and expected timeline

- Interim results go in the December 1 write-up, labeled underpowered.
- The confirmatory read comes after the Jan–Feb 2027 season, under BUILD.md Phase 9.
- C1 replaces the champion only if it wins the pre-registered test on forecasts it sealed before
  the outcomes.

## Build steps

1. Spec v2 format and validator (`spec_schema.md`, `spec.py`), with tests for every rejection rule.
2. Snapshot fetchers, each tested to refuse items timestamped after the origin.
3. The Monte Carlo combiner, with tests on synthetic specs that have known answers.
4. A dry run on 20 past events, labeled exploratory: cost, latency, failure rate.
5. Freeze the prompt, sources, combiner, panel list and spend cap; hash them into the ledger with v1.
6. Daily forward run after the snapshot job; seal before the close.

## Done when

- [ ] Prompt, sources, combiner and model ID are frozen and hashed in the ledger.
- [ ] Forward forecasts for every arm are sealed daily, each before its outcome.
- [ ] An interim report is published on December 1; the confirmatory report is published after
      the Jan–Feb 2027 season, whatever the result.
