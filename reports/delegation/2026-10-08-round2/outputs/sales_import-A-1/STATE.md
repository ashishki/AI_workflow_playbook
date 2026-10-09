# Rules

Standard-library importer uses frozen money_exact.to_minor_units. IDs and routing fields are normalized; canonical replays count per occurrence, while conflicts and invalid input roll back the batch. Route precedence: existing route, blank-region manual review, senior at 1000000 cents, standard. SQLite TEXT preserves cents; export sorts IDs and sums exact integers. BEGIN IMMEDIATE serializes writers. Repair uses nine-digit integer/text conversions in both directions without changing Python's global digit limit. Persistent doctests cover the reported `1e4300` amount. Only engine.py and STATE.md were edited; no workers or reviewers were run during repair.

# Verification

Before repair, a local Python probe reproduced ValueError ingesting `1e4300` at the 4300-digit conversion limit.

After repair, actually executed:

- `python -m unittest -v test_engine`: all 7 tests passed.
- `python -B -m doctest -v engine.py`: both persistent regression checks passed.
- `python -B -` with inline LargeAmountRegression: both tests passed, covering `1e4300` ingest/export, canonical replay, exact total, SQLite TEXT, unchanged global digit limit, and conversion chunk boundaries including zero and a huge nonzero suffix.
- SHA-256 comparisons of test_engine.py, money_exact.py, and README.md matched their pre-repair hashes.

# Limits

Writer lock waits remain bounded by 30 seconds. Extremely large amounts remain subject to available memory and computation time; no application amount-size ceiling is imposed. Operator verification of this repair has not yet been observed.

# Next step

Return the repaired files for operator verification; no further implementation work is pending.
