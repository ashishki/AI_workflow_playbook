## Rules

Worked only in this isolated workspace. Main was sole writer; three read-only investigators analyzed inventory, checkout, and refunds and completed within 180 seconds, without nested delegation or reviewer work. Changed only three existing causal source files, diagnosis.json, and STATE.md. Frozen inputs/tests/docs were preserved; no network, accounts, dependencies, evaluator access, commit/push, helper files, or caches.

## Verification

- `python -B -m unittest discover -s tests -v`: before repair, 8 tests ran with 4 failures; after repair, all 8 passed.
- `python -B -m src.replay data/current/combined.json`: before repair, metrics were 0 ready / 2 reserved / 0 refunded / 3 rejected; after repair, 1 ready / 4 reserved / 900 refunded / 0 rejected, revision 10 paid, net 100.
- Investigators ran `python -B -m src.replay data/current/inventory.json`, `python -B -m src.replay data/current/checkout.json`, and `python -B -m src.replay data/current/refunds.json` before repair, reproducing missing south hold, revision 2 pending, and 800 refunded with REF-323 rejected.
- Main ran `python -B -` with stdin assertions: 44 passed, covering scoped identity/conflicts, revision permutations, readiness, capture equality, rejected retries, and purity/repeatability/transport equivalence for all five current fixtures.
- A separate `python -B -` report check initially failed on the archive log's pretty-printed JSON layout; after fixing that stdin check, schema, cited IDs/paths, STATE headings, and absence of bytecode caches passed. No input file changed.
- `python -B -c "import json; from pathlib import Path; report = json.loads(Path('diagnosis.json').read_text()); assert len(report['defects']) == 3; print('PASS: final diagnosis JSON parses with exactly three defects')"`: passed.

## Limits

Local synthetic verification only; no live/production success claimed. Finite assertions do not prove every possible input. Historical r29 cache, polling, and rounding advice does not apply to the r31 route. No operator feedback or model review was requested.

## Next step

Requested fixes and local checks are complete. Hand off the preserved workspace and evidence-linked diagnosis for the operator's frozen checks; no further repair or deployment is authorized in this run.
