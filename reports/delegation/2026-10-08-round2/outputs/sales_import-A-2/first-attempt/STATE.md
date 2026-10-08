# Rules
- Normalize IDs, region and existing route; reject invalid fields with ValueError.
- Parse exact cents with frozen money_exact.to_minor_units; store cents as SQLite TEXT.
- Canonical-identical IDs replay; changed payloads fail. Any batch error rolls back all its inserts.
- Apply existing-route, manual-review, senior and standard precedence.
- Serialize writers with BEGIN IMMEDIATE; export sorted IDs, Python integer cents and an exact total.
- Edited only engine.py and STATE.md; preserved supplied tests, README and money reference. No workers, network, installs, commits or pushes.

# Verification
- Ran `python -m unittest -v test_engine`: all 7 tests passed (OK), including concurrency, atomicity and large exact amounts.

# Limits
- SQLite waits up to 30 seconds for locks; longer contention can still raise a database error.
- Independent review is performed externally by the operator; no reviewer was run here.

# Next step
- Operator runs the independent review of the completed implementation.
