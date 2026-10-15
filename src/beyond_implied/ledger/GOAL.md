# GOAL — ledger

## Purpose

Make every prediction verifiable: written before its outcome exists, impossible to edit afterward
without detection. The ledger is the proof-of-skill artifact; a stranger should be able to verify it
with one command.

## Inputs

- Pre-registration files (their SHA-256 hashes).
- Prediction records: `prediction_id`, `symbol`, `event_ts` (announcement time, UTC ISO), forecast,
  implied move, gate decision and fired rule IDs.
- Outcome records: `prediction_id`, realized move, post-event close.

## Outputs

- `ledger/predictions.jsonl`: one JSON record per line with `seq`, `ts_utc`, `kind`, `payload`,
  `prev_hash`, `hash` (SHA-256 of the canonical record without `hash`).
- `bi ledger verify` result: OK, or the first bad record and why.

## Built in the scaffold

- `chain.py`: `append`, `read`, `verify`, `prereg_payload`.
- `verify` checks sequence, hash links, recomputed hashes, that each outcome references an earlier
  prediction, and that each prediction was written before its `event_ts`.

## Build steps

1. Phase 3: `bi ledger prereg PREREGISTRATION.md config/gates.toml config/universe.toml`.
2. Phase 6: write predictions from daily snapshots before announcements; append outcomes after.
3. Optional: sign each record (Ed25519) and publish the public key in the README.
4. Optional: post the latest hash publicly (e.g., in a dated commit or gist) each week so the chain
   cannot be rewritten wholesale.

## Done when

- [ ] Ledger verifies end to end in CI.
- [ ] Every forward prediction's `ts_utc` precedes its `event_ts`.
- [ ] README explains how to verify in one command.

## Pitfalls

- A local hash chain proves internal consistency, not wall-clock time. Public pushes (GitHub) and
  weekly published head hashes are what anchor the timestamps.
- Never rewrite history on `main` once predictions are in the ledger.
