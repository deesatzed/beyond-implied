# GOAL — gates (expert-system rule layer)

## Purpose

Decide, for every event, whether the scaffold commits to a forecast or abstains, using explicit,
auditable rules. Abstention is what lets an imperfect model be useful: the claim is low risk at a
stated coverage, not accuracy everywhere.

## Inputs

A flat dict of fields per event: timing, quote flags, spot, option volume, trailing history count,
regime and premium features, model confidence.

## Outputs

`Decision(commit: bool, fired: [rule IDs], reasons: [text], missing: [fields])`, logged with every
prediction in the ledger.

## Built in the scaffold

- `engine.py`: rules loaded from `config/gates.toml`; operators `eq, ne, lt, le, gt, ge, in, not_in,
  is_null, not_null`; `all = [...]` for conjunctions; no `eval`.
- Draft rules G1–G7: unknown timing, zero bid, wide spread, low price, thin options, short history,
  and a stress-regime gate (inverted VIX term structure with high VVIX).

## Build steps

1. Phase 3: settle thresholds from training seasons only, then freeze `config/gates.toml` with the
   pre-registration (its hash goes in the ledger).
2. Phase 5: add one confidence gate (abstain when model confidence is below a fixed quantile) and
   report the risk-coverage curve with and without it.
3. Phase 5: report how often each rule fires, by season. A rule that never fires is dead weight;
   a rule that fires on most events is a universe filter, not a gate.

## Done when

- [ ] Rules frozen and hashed in the ledger.
- [ ] Every ledger prediction carries its decision and fired rule IDs.
- [ ] Fire-rate table by rule and season in the report.

## Pitfalls

- Tuning rules after seeing held-out outcomes turns the gate layer into overfitting with extra steps.
- Missing fields: a condition on a missing field does not fire (except `is_null`); the decision
  records which fields were missing so silent gaps are visible.
