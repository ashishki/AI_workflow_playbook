# Rules

Use Playbook with one implementation agent and one writer; no native workers or reviewers, per AGENTS.md. Work only in this isolated workspace. Change existing src/**/*.py, diagnosis.json and STATE.md only. Frozen tests/data/docs/config/skills remain unchanged. No network, accounts, dependencies, evaluator access, operator feedback, commit or push. All local Python commands used -B; no helper or cache files were added.

# Verification

- `python -B -m src.replay data/current/combined.json`: before changes, metrics were ready_orders=0, reserved_units=2, refunded_minor=0, rejected_refunds=3. After changes: 1, 4, 900, 0 respectively; order revision=10, status=paid, ready=true, net_minor=100. Inventory accepted/replayed=2/1; refunds accepted/replayed=2/1.
- `python -B -m unittest discover -s tests -v`: initially 8 tests with 4 incident failures; baseline and transport checks passed. After changes all 8 passed.
- `python -B -` with inline unittest cases: all 11 checks passed for identity scope, payload conflicts, stock/release safety, revision order/ties/newer pending snapshots, summed line requirements, capture boundaries, rejected retries, format equivalence, repeatability and input preservation. No test files changed.
- Final `python -B -` inspection and comparison against pre-edit SHA-256 hashes: diagnosis schema/evidence checks passed; only src/inventory/registry.py, src/checkout/revisions.py, src/refunds/ledger.py, diagnosis.json and STATE.md changed, with no added or removed files in the inspected source/test/data/doc/log/trace/config and root-file scope.

# Limits

Results establish local synthetic r31 behavior only, not live or production success. No independent model review or operator rubric was run; both are outside this first-attempt task. The three source files each have one causal line changed. Historical r29 cache, poll-time and rounding advice was excluded using current records and routes. Work completed within the 600-second budget.

# Next step

Use the repaired local replay and diagnosis for the operator's frozen checks. No further action or production deployment was performed.
