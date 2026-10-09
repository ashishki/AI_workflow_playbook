## Rules

Use the standard library and frozen money_exact.to_minor_units. Normalize inputs,
enforce immutable canonical events and route precedence, and roll back failed
batches. Store exact cents as SQLite TEXT; export sorted rows and integer totals.
BEGIN IMMEDIATE and a 30-second timeout serialize writers. Repair uses exact
Decimal conversions at the text boundary to bypass Python's integer/string digit
limit without changing global settings. Only engine.py and STATE.md were edited;
no workers or reviewers ran during this repair.

## Verification

- `python -B -`: reproduced the conversion failure for exact cents from `1e4300`
  with the 4,300-digit limit; exact Decimal conversions round-tripped 4,303 digits.
- `python -B -m unittest -v test_engine`: all 7 supplied tests passed (exit 0).
- `python -B -m doctest -v engine.py`: all 3 examples passed (exit 0), including
  ingestion of `1e4300`, replay as `10e4299`, exact SQLite text, senior routing,
  exported integer cents and exact total.

## Limits

Checks cover synthetic local SQLite behavior. Extremely large inputs remain
subject to memory and SQLite resource limits; writers can exceed the 30-second
timeout. The operator's supplied review identified this repaired conversion defect;
no new independent review was run here.

## Next step

Return the repair for the operator's assessment; no further implementation planned.
