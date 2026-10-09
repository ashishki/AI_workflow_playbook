# Rules

Worked only in this isolated workspace; main was the sole writer. Three read-only analysis workers investigated inventory, checkout and refunds, completed within 180 seconds, and reported no writes. No nested delegation or reviewer work. Changed only three existing source files (one identity/comparison line each), diagnosis.json and STATE.md. Tests, inputs, docs and configs stayed frozen. Used local python with -B; no helper/cache files, network, dependencies, accounts, evaluator access, feedback, commit or push.

# Verification

- `python -B -m src.replay data/current/combined.json`: before repair, metrics were ready 0/reserved 2/refunded 0/rejected 3, revision 2/pending, net 1000. After repair, ready 1/reserved 4/refunded 900/rejected 0, revision 10/paid, net 100; inventory accepted 2/replayed 1 and refunds accepted 2/replayed 1.
- `python -B -m unittest discover -s tests -v`: before repair, 8 tests ran with 4 incident failures; normal and transport checks passed. After repair, all 8 passed.
- `python -B -` with transient stdin assertions: 43 checks passed for scoped identities, immutable conflicts, inventory constraints, numeric revisions and valid newer pending snapshots, summed line quantities, refund eligibility/capture boundaries, rejected retries, and purity/repeatability/canonical equivalence of all five frozen cases. No test files were added.
- Current events and OBS/TRACE records support all three causes in diagnosis.json; excluded ARC-CACHE-29, ARC-POLL-29 and ARC-MONEY-29 describe retired r29 behavior, not r31.

- `python -B -` report validation: first attempt failed on line-by-line parsing of the pretty-printed archive JSON object. After correcting the transient validator, exact JSON schema, all current/stale evidence IDs, three causal source paths and required STATE headings passed; changed source compiled in memory without caches.

# Limits

Local synthetic verification only; no live/production success claimed. No operator rubric or independent review was accessed. Read-only worker behavior was instruction-constrained, not OS-enforced. Adapters and historical source were unchanged.

# Next step

Hand the completed source and reports to the operator for the prescribed frozen behavioral and diagnosis checks. No further edits or external actions are required in this attempt.
