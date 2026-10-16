# Spec format — elicited network (JSON)

```json
{
  "spec_version": "1",
  "target": "abs_move",
  "elicitation": {
    "model_id": "provider/model-name",
    "stated_training_cutoff": "YYYY-MM",
    "prompt_sha256": "<hex>",
    "elicited_utc": "YYYY-MM-DDTHH:MM:SSZ"
  },
  "review": {
    "approved_by": "name",
    "approved_utc": "YYYY-MM-DDTHH:MM:SSZ",
    "changes": [{"node": "id", "field": "median", "from": 0.04, "to": 0.05, "reason": "..."}]
  },
  "nodes": [
    {
      "id": "abs_move",
      "kind": "latent | input | target",
      "input": "column name in the event table (kind=input only)",
      "unit": "fraction | ratio | count | usd | index_points | category",
      "distribution": "lognormal | normal | gamma | beta | student_t | categorical",
      "median": 0.045,
      "range": [0.005, 0.25],
      "range_coverage": 0.9,
      "parents": ["implied_move_event"],
      "relation": "log(abs_move) ~ a + b * log(implied_move_event) + ...",
      "rationale": "one line"
    }
  ]
}
```

Rules enforced by `spec.py`:

- Exactly one node with `kind = "target"`, and its id equals `target`.
- Every `input` node names an allowed input column (see GOAL.md); forbidden fields are rejected anywhere.
- `range` has low < high, `range_coverage` is in (0, 1), and `median` lies inside `range`
  (categorical nodes give `categories` instead of median/range).
- Positive-only families (lognormal, gamma) need low > 0; beta needs 0 ≤ low < high ≤ 1.
- Parents exist, there are no self-loops, and the graph is acyclic.
- Every node has a unit and a rationale.
