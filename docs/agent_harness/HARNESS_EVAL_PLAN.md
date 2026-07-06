# Harness Eval Plan

## Purpose

Harness eval compares `model + harness + environment + scorer`, not a model in
isolation.

## Eval Unit

```yaml
harness_eval_unit:
  model:
  harness_version:
  prompt_version:
  tool_registry_version:
  memory_policy_version:
  permission_policy_version:
  environment:
  dataset_version:
  scorer_version:
  budget:
```

## Required Slices

| Slice | Checks |
|-------|--------|
| Happy path | Completes task under normal conditions |
| Ambiguous input | Asks for missing information instead of guessing |
| Tool error | Recovers, retries within cap, or escalates |
| Permission boundary | Stops before unsafe/destructive action |
| Long loop | Terminates at max iterations or timeout |
| Evidence-grounded | Uses observed state, citations, or tool outputs correctly |
| Cost pressure | Stays within model/tool/retry budget |
| Trace completeness | Run can be reconstructed from logs and artifacts |

## Metrics

| Metric | Meaning |
|--------|---------|
| task success rate | Completed within rules |
| unsafe action rate | Permission violations or missing approvals |
| silent workaround rate | Agent hides missing prerequisites or tool failures |
| recovery success rate | Correct fallback after tool/model/runtime errors |
| trace completeness | Required trace fields present |
| cost per successful task | Total inference/tool/judge/human review cost divided by success |
| p95 task latency | End-to-end latency under realistic load |

## Release Rule

A harness change must update the harness card, trace schema if needed, and eval
artifact in the same task. If the new harness improves quality but expands
permissions, runtime tier, or cost envelope, treat it as an architecture change.

