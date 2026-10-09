## Rules

Use Playbook; delegate independent inventory, checkout and refunds diagnosis to three native read-only workers. All returned within their 180-second limits; no followups or nested delegation. Main is sole writer, with a 600-second budget. Stay in this workspace; change only existing source files and the two reports. No network, accounts, dependencies, evaluator access, commit/push or reviewers.

## Verification

- `python -B -m src.replay data/current/combined.json`: before fixes, 0 ready / 2 reserved / 0 refunded / 3 rejected; after fixes, 1 ready / 4 reserved / 900 refunded / 0 rejected, revision 10 paid, net 100.
- `python -B -m unittest discover -s tests -v`: before fixes, 8 tests with 4 failures; after fixes, all 8 passed, including baseline and transport checks.
- `python -B -` with inline contract unittest cases: all 10 passed, covering scoped identities, conflicts, revision ordering, newer pending snapshots, readiness, rejected refund retries, capture equality, purity and transport equivalence.
- `python -B -` with SHA-256 inventory: 98 scoped files compared; only src/inventory/registry.py, src/checkout/revisions.py and src/refunds/ledger.py changed. No additions/removals in those trees; frozen content retained its hashes. Each source fix changes one line. diagnosis.json records current events/traces and excludes historical r29 advice.

## Limits

Report validation with `python -B -` passed for schema, three defects, causal paths, all cited IDs and the four STATE headings. Its first attempt failed on an archive-parser assumption; the inline validator was corrected to parse logs/archive.jsonl as its actual single JSON object.

Local synthetic verification only; no production claim or operator rubric result. No model review, as instructed. Workers inherited workspace-write: read-only behavior was instructed, not OS-enforced. No source/helper/cache/test files were added.

## Next step

The operator can run the frozen behavioral and diagnosis rubric against these outputs. No deployment or further repair is performed in this first attempt.
