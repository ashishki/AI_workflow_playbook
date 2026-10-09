## Rules

Implemented trimmed nonempty string IDs, uppercase stripped regions, normalized
existing routes, exact cents via frozen `money_exact.to_minor_units`, immutable
canonical payloads and routing precedence. SQLite stores cents as TEXT;
`BEGIN IMMEDIATE` and a 10-second busy timeout serialize imports. Any batch error
rolls back its writes. Export sorts canonical IDs and sums Python integers.

Route: delegate two independent read-only audits (test contract; monetary source
and spec). Both returned within 60 seconds; their findings informed validation,
transaction boundaries and exact storage/export. Depth one; main sole writer.
Only `engine.py` and this state document were edited.

## Verification

Executed `python -m unittest -v test_engine`: exit 0, all 7 tests passed.
Observed checks cover huge exact amounts and TEXT storage, routing, canonical
replays, conflicts, atomic rollback, deterministic empty/populated exports and
two concurrent writers producing one creation and one replay.

## Limits

Verification used synthetic local data. SQLite lock waiting is bounded at
10 seconds. No independent code review ran here; the operator performs it
externally. Frozen tests, README and monetary reference were preserved.

## Next step

Operator runs the independent code review on this implementation.
