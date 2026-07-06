# Inference Decision Tree

## Purpose

Choose API-first, self-hosted, or hybrid inference from workload needs, risk,
SLA, data boundaries, and eval cost. Do not optimize serving internals before
the system has a measured workload.

## Decision Tree

```text
Need regulated/local-only data processing?
  yes -> self-hosted or private deployment candidate
  no  -> continue

Need custom model weights, custom kernels, or speculative decoding control?
  yes -> self-hosted candidate after benchmark
  no  -> continue

Need fast delivery, broad model capability, or low ops burden?
  yes -> API-first
  no  -> continue

Is workload high-volume, stable, and price-sensitive with measurable eval set?
  yes -> compare API vs self-hosted TCO
  no  -> API-first or hybrid

Does workload contain both sensitive batch jobs and ordinary interactive use?
  yes -> hybrid
```

## Comparison Criteria

| Area | API-first | Self-hosted | Hybrid |
|------|-----------|-------------|--------|
| Time to value | Fast | Slower | Medium |
| Ops burden | Low | High | Medium/high |
| Model breadth | High | Depends on deployment | Mixed |
| Data control | Provider boundary | Stronger local control | Workload-specific |
| Serving optimization | Limited | Full control | Selective |
| Cost predictability | Usage-based | Infra + utilization | Mixed |
| Eval requirement | Required | Required plus serving benchmark | Required per route |

## Rule

Self-hosting is an architecture decision only after workload, eval, latency, and
cost-per-successful-task are measurable.

