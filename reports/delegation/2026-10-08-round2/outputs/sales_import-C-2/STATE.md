## Rules

Preserved normalization, exact cents via frozen `money_exact.to_minor_units`,
immutable events, routing, atomic batches and serialized SQLite imports.
Cents use canonical SQLite TEXT and exact integer export/sums. Serialization
and parsing now use nine-digit chunks without changing interpreter limits
or depending on Decimal precision.

Repair route: self, main writer only; no workers or reviewers, as instructed.
Only `engine.py` and `STATE.md` were edited during this repair.

## Verification

Executed `python -m unittest -v test_engine`: exit 0, all 7 tests passed.
Executed two inline `python -B -` probes: reproduced the pre-repair failure
for `1e4300`; after repair, verified chunk boundaries through 10,000 digits,
huge imports/replays, TEXT storage, export, exact sum, routing and conflict
rollback. Checks also passed at Decimal precision 2; the interpreter digit
limit remained 4,300. Protected test, README and money helper SHA-256 hashes
matched their pre-repair values.

## Limits

Verification used synthetic local data and finite samples, not resource
exhaustion stress tests. SQLite lock waiting remains bounded at 10 seconds.
No additional independent review ran during this repair; review is external.

## Next step

Operator checks the repaired implementation against the confirmed finding.
