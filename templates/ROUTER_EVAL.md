# Router Evaluation

Status: draft
Owner:
Last updated:

Use this artifact when a project wants dynamic routing, model cascades, or
automatic escalation beyond static role-based model selection.

## Routing Scope

- Routing maturity level: L5 dynamic router | L6 cascade with verifier
- Workloads covered:
- Workloads explicitly excluded:
- Human approval boundary:

## Traffic Sample

```yaml
traffic_sample:
  size:
  source: production_shadow | eval_set | replay_logs | synthetic
  collection_window:
  known_biases:
```

## Candidate Models

| Model/Class | Role | Allowed Workloads | Cost Assumption | Latency Assumption |
|-------------|------|-------------------|-----------------|--------------------|
| frontier | | | | |
| mid | | | | |
| cheap | | | | |

## Metrics

```yaml
metrics:
  quality_floor: "no more than 2% below baseline"
  latency_p95_ms:
  cost_reduction_target: ">=25%"
  cache_hit_rate_delta: "not worse than -10%"
  escalation_rate_max:
  unsupported_languages:
    - ru
    - ka
```

## Baseline

| Baseline Route | Quality | Cost USD | p95 Latency ms | Cache Hit Rate |
|----------------|---------|----------|----------------|----------------|
| static role-based | | | | |

## Router Results

| Router Candidate | Quality Delta | Cost Delta | p95 Latency | Cache Hit Delta | Escalation Rate | Verdict |
|------------------|---------------|------------|-------------|-----------------|-----------------|---------|
| | | | | | pass/fail |

## Cascade Calibration

Required when L6 cascades are used.

| Judge | Eval Set | False Negative Rate | False Positive Rate | Threshold | Verdict |
|-------|----------|---------------------|---------------------|-----------|---------|
| | | | | | |

Rules:

- cheap model self-judgment is not accepted unless calibrated on this eval set
- failed cheap attempts count toward total cost
- verifier cost counts toward total cost
- escalation threshold must come from the measured cost/quality curve

## Stale Router Policy

Retrain or re-evaluate when:

- new model is added
- model pricing changes
- prompt/cache layout changes
- traffic distribution changes
- unsupported language share changes
- eval quality regresses above threshold
- cache hit rate drops below threshold

## Decision

- Router approved: yes | no
- Approved level: L5 | L6 | lower level only
- Approval date:
- Reviewer:
- Follow-up tasks:
