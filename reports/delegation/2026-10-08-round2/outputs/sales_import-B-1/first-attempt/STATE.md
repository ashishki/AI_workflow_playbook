## Rules

Implemented engine.py using the standard library and frozen money_exact.to_minor_units.
Normalize IDs, region and existing route; reject invalid input. Canonical IDs are
immutable; identical payloads replay. Preserve exact cents as SQLite TEXT, apply
the specified route precedence, and export sorted rows with an exact integer total.
BEGIN IMMEDIATE and a 30-second busy timeout serialize writers; errors roll back
the whole batch. Only engine.py and STATE.md were edited; no workers or reviewers ran.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_engine`: all 7 tests passed,
  including huge exact amounts, routing, replays, conflicts, rollback, export and concurrency.
- `PYTHONDONTWRITEBYTECODE=1 python -` supplemental assertions passed: empty batch,
  9 invalid events with rollback, 5 invalid batch inputs, interrupted iterable rollback.

## Limits

Evidence covers synthetic local SQLite behavior. A writer blocked longer than the
30-second busy timeout can fail. Independent operator review has not run here.

## Next step

Operator performs the planned independent code review.
