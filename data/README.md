# Data

Nothing under `raw/`, `interim/` or `processed/` is committed. Raw downloads are kept exactly as
received, each with a `.meta.json` sidecar (URL, UTC fetch time, SHA-256).

- `raw/cboe_indices/` — `{SYMBOL}_History.csv`
- `raw/cboe_options/<UTC date>/` — `{SYMBOL}.json` daily chain snapshots
- `raw/thetadata/` — cached Terminal responses (individual-use license; never published)
- `processed/events.parquet` — the event table (Phase 2)
