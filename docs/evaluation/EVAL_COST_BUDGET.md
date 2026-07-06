# Eval Cost Budget

## Purpose

Evaluation has its own cost surface. Budget it separately from production
inference so teams do not silently drop eval runs when they become expensive.

## Cost Components

| Component | Examples | Measurement |
|-----------|----------|-------------|
| Dataset creation | Human labels, synthetic seed generation, fixture extraction | minutes, dollars, item count |
| Eval inference | Candidate runs, baseline runs, retries | tokens, calls, cost |
| Judge inference | LLM-as-judge scoring, pairwise comparison | tokens, calls, cost |
| Deterministic validation | Test runtime, parser jobs, corpus lint | CI minutes |
| Human review | Labeling, disagreement review, release approval | minutes per item |
| Storage/artifacts | Traces, reports, snapshots | size, retention |

## Budget Fields

```yaml
eval_cost_budget:
  owner:
  window: per_pr | per_release | monthly
  max_eval_inference_cost_usd:
  max_judge_cost_usd:
  max_human_review_minutes:
  max_ci_minutes:
  required_eval_slices:
    - seeded_regression
    - capability_baseline
    - high_risk_failures
  downgrade_policy: "manual approval required"
```

## Cost-Quality Rule

Do not replace deterministic validators with an LLM judge to save engineering
time unless the judge is calibrated and the total cost includes false-pass risk,
human review, and rework.

## Review Questions

- Is the eval run sized to the risk of the change?
- Are judge costs separated from candidate inference costs?
- Is human review included when the judge is advisory?
- Are failed cheap attempts included in cost per successful task?
- Does the project know which eval slices are allowed to run asynchronously?

