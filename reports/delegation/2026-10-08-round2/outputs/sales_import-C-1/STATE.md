## Rules

Implemented canonical string normalization, exact cents via supplied
money_exact.to_minor_units, immutable event IDs, replay counting, route precedence,
whole-batch rollback, TEXT cents storage, and sorted exports with Python integer totals.
BEGIN IMMEDIATE and a 10-second SQLite busy timeout serialize ingest writers.
Only engine.py and STATE.md were edited; frozen sources/tests were preserved.

Route: Delegate. Two read-only, depth-one native workers audited distinct sources:
canonical normalization/money/routing and SQLite/test constraints. Both returned
within their 60-second windows. Main alone wrote code and integrated their findings,
including canonical replay comparison and explicit connection closure. No worker reuse.

## Verification

Executed `python -m unittest -v test_engine`: all 7 tests passed (0.146 seconds).
Checks covered exact huge amounts and TEXT storage, routing, replay, conflicts,
atomic rollback, deterministic/empty export, and concurrent creation/replay.

## Limits

Verification covers the supplied synthetic local checks. Independent code review
was not run here; it is performed externally by the operator. Lock waits are bounded
to 10 seconds. No network, accounts, dependency installs, commit or push were used.

## Next step

Operator performs the prescribed independent review of engine.py.
