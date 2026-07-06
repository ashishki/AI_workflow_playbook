# Eval Lab Harness Benchmark Card

Status: example
Purpose: show how Eval-Ground-Truth-Lab could compare harness configurations.

## Benchmark Intent

Compare a baseline harness and candidate harness while holding task set,
environment, scorer, and budget visible.

| Area | Baseline | Candidate |
|------|----------|-----------|
| Model/class | same class | same class unless testing model route |
| Prompt | v1 | v2 |
| Tool registry | read-only + test runner | read-only + test runner |
| Memory | none | structured trace summary |
| Recovery | one retry | one retry + explicit failure class |
| Permissions | allowed/ask/block | allowed/ask/sandbox/escalate/block |
| Dataset | seeded challenge set | same |
| Scorer | deterministic first, judge advisory | same |
| Budget | same max calls/cost | same |

## Required Outputs

- harness version in run metadata
- trace completeness score
- cost per successful task
- failure taxonomy by slice
- judge calibration status if judge participates

