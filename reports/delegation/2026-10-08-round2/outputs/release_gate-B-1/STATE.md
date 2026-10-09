# Rules

Release 2.8, eu-central/eu-west, assessment 2026-10-08T12:00:00Z.
Apply four independent gates from TASK.md; any failure means HOLD. Use current
records, latest eligible updates, inclusive performance window, strict thresholds,
and exact integer cents. Legacy GO cannot override current evidence.
Workspace-only main-session work using installed Playbook; no workers, reviewers,
network, accounts, installs, commit or push. Only decision.json, BRIEF.md and this
file were edited; supplied data, tests and money_exact.py are frozen.

# Verification

- `cat AGENTS.md TASK.md` and local Playbook/source reads established the rules.
- `python -B - <<'PY'` source inspection observed 82 performance rows, 93 incident
  rows and 45 safety/cost rows, and captured initial frozen-file SHA256 hashes.
- `python -B - <<'PY'` evaluation wrote HOLD: both latency regions, INC-210/211,
  central recovery and west audit unverified, cost delta 1,234,567 cents.
- A subsequent `python -B - <<'PY'` check recomputed all gates from all source rows
  with sorted updates and Fraction arithmetic. PASS: exact decision/schema,
  sorted unique lists, seven blocking IDs, threshold/deduplication exclusions and
  brief evidence references. PASS: all four source hashes and money_exact.py
  matched their initial hashes.

# Limits

Synthetic local records only; no real customer impact, spending or remediation
verified. Independent review is performed externally by the operator; none was
run or claimed here. No supplied test suite was present in the visible file list.

# Next step

Keep both regions on HOLD. Address latency and open P1 incidents, verify central
recovery/west audit, reduce projected cost to the ceiling, then reassess all gates
with fresh records. Outputs are ready for the operator's external review.
