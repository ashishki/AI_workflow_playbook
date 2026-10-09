## Rules

- Implemented engine.py with standard-library SQLite and frozen money_exact.to_minor_units.
- Normalize IDs, region and existing_route; reject invalid fields and conflicting immutable event IDs. Identical canonical payloads count as replays, including within a batch.
- Store exact integer cents as TEXT; apply existing_route, blank-region, senior-threshold and standard routing precedence.
- BEGIN IMMEDIATE and a 30-second busy timeout serialize imports; failures roll back the entire batch. Export a sorted snapshot with Python integer amounts and totals, including empty unused databases.
- Kept all work in this workspace; no workers, reviewers, network, installs, commits or pushes. Frozen tests, README.md and money_exact.py were not edited.

## Verification

- Ran `python -m unittest -v test_engine`: exit 0, all 7 tests passed. Covered exact large amounts and TEXT storage, routing, canonical replay, conflicts, batch rollback, deterministic export and two concurrent writers.

## Limits

- Verification covers the supplied synthetic local tests. Independent code review has not run in this session; the operator performs it externally.
- Writer waits are bounded by the 30-second SQLite timeout. Existing unrelated database schemas and migrations are outside this task.

## Next step

Operator runs the independent code review on engine.py; address confirmed findings if needed.
