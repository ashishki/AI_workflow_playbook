## Rules

Used Playbook diagnosis/verification and controlled delegation. Three native read-only inventory, checkout and refund workers returned within 180 seconds; no nested delegation, followups or reviewers. Main alone wrote three causal source expressions and the two permitted reports. Work stayed in this isolated workspace, with local stdlib Python using `-B`; no network, accounts, dependencies, evaluator access, commit or push. The 600-second main budget was respected.

## Verification

- `python -B -m unittest discover -s tests -v`: initially 4 failures among 8 tests; after fixes, all 8 passed, including the healthy baseline and transport checks.
- `python -B -m src.replay data/current/combined.json`: initially revision 2/pending, 2 reserved units and 3 rejected refunds; after fixes revision 10/paid/ready, 4 reserved units, 900 refunded, no rejections and net 100.
- `python -B -` with an in-memory contract-check script: 57 assertions passed, covering scoped identities, conflicts, stock/release guards, revision/order/timestamp behavior, readiness, logical/refused refund retries, capture boundaries, purity and transport equivalence. No helper/test/input files added.
- `python -B -` with SHA-256 snapshot scripts: among 98 scoped source and frozen files, only the three causal source files changed; no additions/removals, frozen inputs/tests/docs/config/skills intact. Current triggering events and supporting traces, plus excluded historical IDs and their inapplicability, are recorded in diagnosis.json.

- `python -B -` with the report-validation script: exact diagnosis schema, three causal paths, current and excluded historical evidence IDs, and all four STATE headings passed.

## Limits

Local synthetic evidence only; no production success claimed. Focused checks are not exhaustive. No operator feedback, external evaluation or reviewer was used for this first attempt. Native read-only worker restrictions were instructions, not OS-enforced isolation; observed file changes stayed within the main writer's scope.

## Next step

Hand the completed source and reports to the operator for the prescribed frozen behavioral/diagnosis checks; no deployment or further repair performed here.
