# Rules

Work confined to this workspace. Only decision.json, BRIEF.md and STATE.md edited. Source data and money_exact.py frozen. No network, accounts, installs, commit/push, workers or reviewers. Assessment: release 2.8, eu-central/eu-west, 2026-10-08T12:00:00Z. Any failed gate means HOLD; latest eligible updates govern, and cost arithmetic uses exact integer cents.

# Verification

- `rg --files --hidden -g '!.git/**'`: inspected supplied workspace inventory; no test files listed.
- `python -B - <<'PY'`: evaluated all 82 performance, 93 incident and 45 safety/cost rows. Result: all four gates fail; HOLD with seven blocking evidence IDs and cost_delta_minor 1234567.
- The same Python command passed assertions for the exact expected six-key decision, JSON readback, sorted unique lists, integer-cent cost comparison and unchanged SHA-256 hashes of supplied sources/instructions/helper.

# Limits

Synthetic records only, bounded by the assessment cutoff. No deployment, live validation or external review performed. The operator handles independent review; no additional review is required for this text-only work.

# Next step

Keep both regions on HOLD. Resolve latency and P1 incident blockers, verify central recovery and west audit, reduce the combined cost projection to the cap, then reassess all four gates with current records.
