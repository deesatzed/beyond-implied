# Ledger

`predictions.jsonl` is created in Phase 3 when the pre-registration is frozen. Each line is a record
hash-chained to the one before it. Verify the whole chain with:

```bash
bi ledger verify ledger/predictions.jsonl
```

Records are never edited or deleted. Corrections are new `note` records that reference the original.
