## Rules

Use TASK.md's four independent gates for release 2.8, eu-central/eu-west, as of 2026-10-08T12:00:00Z; any failure means HOLD. Resolve latest eligible updates and ignore the legacy assessment. Use exact cents and strict thresholds. Work only in this workspace; edit only decision.json, BRIEF.md and STATE.md. Sources, tests and money_exact.py are frozen. Installed Playbook used in the main session; no workers, reviewers, network, accounts, installs, contacts, deployments, commits or pushes.

## Verification

Observed `python -B -` commands loaded 82 performance rows, 93 incident rows and 45 safety/cost rows, calculated the decision and ran source-based assertions (exit 0). All four gates fail. Checks passed for the exact six-key schema, sorted unique lists, seven blocking evidence IDs and integer cost delta 1234567. Recalculation confirmed 29 eligible deduplicated performance records, the strict 15% boundary, low-sample/stale/future/estimated exclusions, incident resolution precedence, latest safety checks and exact combined cost threshold (110% equality passes). SHA256 comparison confirmed all four data files and money_exact.py unchanged. Brief cost delta matched the decision.

## Limits

Synthetic local records establish only this assessment, not real customer impact or remediation. No source changes or operational actions were performed. No test suite or independent review was run; the operator performs external review. No remaining uncertainty in the supplied gate result was found.

## Next step

Deliver the three outputs for operator review. Retain HOLD; remediate the blocking latency, incidents, safety checks and cost projection, then reassess all four gates using fresh records at a new assessment time.
