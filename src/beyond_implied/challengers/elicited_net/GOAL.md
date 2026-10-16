# GOAL — Challenger C1: AI-elicited probabilistic network

Status: **specified, not built.** Runs only after v1 is frozen (BUILD.md, Phase 9).

## Question

Can a probabilistic network whose structure, distributions, medians and ranges are proposed by an
LLM and approved by a person forecast earnings-move size better than the v1 champion, given the same
pre-event inputs?

## Why it is a challenger, not part of v1

- An LLM can produce a precisely computed posterior for the wrong model. A person must review the
  structure before it is used, and the data must decide whether it adds anything.
- LLMs may already know past outcomes. This challenger is scored **only on events after the eliciting
  model's training cutoff**, logged to the ledger before each announcement. Retrospective seasons are
  never used to score it.

## How it works

1. **Elicit.** An LLM is given the input catalogue (below) and the target, and asked for a network
   spec in the format of `spec_schema.md`: nodes, units, distribution family, median, plausible range,
   parents, and a one-line rationale per node. The prompt, model ID and response are saved verbatim.
2. **Validate.** `spec.py` rejects any spec that names an outcome or post-event field, has a median
   outside its range, a cycle, an unknown parent, an unknown input, or missing units.
3. **Review.** A person edits and approves the spec. Every change from the LLM draft is kept as a diff
   with a reason. The approved spec is the one evaluated.
4. **Freeze.** The approved spec's SHA-256, the prompt, the model ID and its stated training cutoff go
   into the ledger as a `prereg` record before the evaluation season starts.
5. **Fit.** Node parameters are updated from training seasons only (priors from the spec, likelihood
   from data). The spec's structure does not change after the freeze.
6. **Forecast and score.** For each forward event: predictive median and 80% interval of the absolute
   move, written to the ledger before the announcement. Scored with the v1 rules: encompassing over the
   champion (implied move + trailing move + champion forecast as benchmark), QLIKE, PIT, interval
   coverage, and risk at matched coverage.
7. **Promote or reject.** Replaces the champion only if it wins on the pre-registered metric over a
   full unseen season. Either way, the result is published.

## Allowed inputs (all known before the pre-event close)

`implied_move_event`, `implied_move_simple`, `f_trailing`, `trailing_n`, `past_move_kurtosis`,
`market_cap`, `n_estimates`, `eps_forecast`, `rel_spread`, `vix`, `vix_vix3m`, `vvix`, `sector`,
`timing`, `days_to_expiry_1`. Adding an input requires a test that proves it is pre-event.

## Forbidden fields (outcomes or post-event)

`realized_move`, `post_close`, `eps`, `surprise_pct`, `straddle_ret_mid`, `straddle_ret_exec`,
`timing_inferred`, anything computed from prices after the pre-event close.

## Built

- `spec_schema.md` — the spec format.
- `spec.py` — loader and validator.
- `example_spec.json` — a hand-written example (not elicited), used by the tests.

## Build steps (Phase 9)

1. Write the elicitation prompt; store it in this folder; hash it.
2. Run elicitation through OpenRouter (key in `.env`) with two different model families; keep both
   drafts. Disagreement between them is reported.
3. Human review and approval; diff recorded.
4. Implement fitting (conjugate updates where possible; otherwise a small PyMC or NumPyro model) and
   the predictive median/interval.
5. Pre-register and freeze before the next season; run forward through the season.

## Done when

- [ ] Prompt, model IDs, cutoffs, drafts and approved spec are in the repo and hashed in the ledger.
- [ ] Forward predictions for one full season are in the ledger, each written before its event.
- [ ] Result published, promotion or not.
