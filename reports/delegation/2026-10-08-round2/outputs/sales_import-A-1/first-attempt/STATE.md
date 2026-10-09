# Rules

Implemented engine.py using the standard library and supplied money_exact.to_minor_units. IDs are trimmed and validated; regions are stripped and uppercased; existing routes are stripped with case preserved. Canonical replays count once per occurrence; conflicting payloads and invalid events roll back the entire batch. Route precedence is existing route, blank-region manual review, senior at 1000000 cents, then standard. SQLite stores cents as TEXT; export returns sorted rows and exact integer totals. BEGIN IMMEDIATE serializes writers with a 30-second busy timeout. Frozen source and tests were left unchanged. No network, installs, workers, reviews, commits, or pushes were used.

# Verification

Executed `python -m unittest -v test_engine`: all 7 tests passed (OK). The suite exercised exact large amounts and TEXT storage, routing, canonical replays, conflicts, batch rollback, deterministic/unused-database export, and concurrent creation/replay.

# Limits

Writer lock waits are bounded by the 30-second timeout. Independent external review has not been performed in this workspace.

# Next step

Operator runs the prescribed independent review.
