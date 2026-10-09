# Rules
- Normalize IDs, region and existing route; reject invalid fields with ValueError.
- Parse exact cents with frozen money_exact.to_minor_units; store cents as SQLite TEXT.
- Convert integer cents through Decimal for storage/export, avoiding Python's decimal integer string digit limit without rounding or changing global settings.
- Canonical-identical IDs replay; changed payloads fail. Any batch error rolls back all its inserts.
- Apply existing-route, manual-review, senior and standard precedence.
- Serialize writers with BEGIN IMMEDIATE; export sorted IDs, Python integer cents and an exact total.
- Edited only engine.py and STATE.md; preserved supplied tests, README and money reference. No workers, network, installs, commits or pushes.

# Verification
- Reproduced the original ValueError importing a valid 5,001-digit amount; the frozen money helper accepted it.
- Ran `python -m unittest -v test_engine` after repair: all 7 tests passed (OK).
- Ran `python -B -m doctest -v engine.py`: 4 examples passed; regression verifies import, equivalent-amount replay, integer export and exact total for the 5,001-digit amount under Decimal precision 6.
- Compared `sha256sum test_engine.py money_exact.py README.md` before and after repair: all hashes unchanged.

# Limits
- SQLite waits up to 30 seconds for locks; longer contention can still raise a database error.
- Available memory and SQLite storage limits still apply to very large amounts.
- Independent review is performed externally by the operator; no reviewer was run here.

# Next step
- Operator checks the repaired implementation externally; no further implementation work is pending.
