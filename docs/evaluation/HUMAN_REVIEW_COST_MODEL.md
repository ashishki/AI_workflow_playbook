# Human Review Cost Model

## Purpose

Human review is a capacity constraint. Treat it as part of the eval plan rather
than an invisible fallback.

## Required Fields

| Field | Description |
|-------|-------------|
| Reviewer role | Domain expert, QA, operator, engineer, legal, security |
| Sample source | Random production sample, seeded failures, disagreement set, high-risk cases |
| Sample size | Number of items per run or release |
| Minutes per item | Expected review time |
| Escalation path | Who handles disagreement or uncertain cases |
| Decision authority | Advisory, approval, blocking, or audit-only |
| Feedback artifact | Where labels, notes, and disagreements are stored |

## Model

```text
human_review_cost =
  sample_size
  * minutes_per_item
  * reviewer_loaded_hourly_cost
  / 60
```

Use this estimate in `docs/COST_BUDGET.md` and eval reports when human labels
or approval are required.

## Review Modes

| Mode | Use when | Notes |
|------|----------|-------|
| Spot check | Low-risk early validation | Not enough for judge calibration |
| Stratified sample | Known failure slices exist | Covers rare but important cases |
| Disagreement review | Judge or model conflicts with human labels | Required before judge status changes |
| High-risk review | Safety, compliance, payments, destructive tools | Human remains final authority |

