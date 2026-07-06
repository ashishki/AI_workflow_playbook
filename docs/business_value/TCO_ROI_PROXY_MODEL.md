# TCO and ROI Proxy Model

## Purpose

Use proxy economics for early decisions without pretending they are audited ROI.

## TCO Components

| Component | Include |
|-----------|---------|
| Build | Engineering, data prep, eval setup |
| Inference | Production calls, retries, fallback |
| Evaluation | Eval runs, judges, human labels |
| Operations | Monitoring, incident response, support |
| Integration | APIs, auth, data pipelines, migrations |
| Governance | Reviews, audits, compliance evidence |
| Human review | Approval, correction, disagreement handling |

## ROI Proxy

```yaml
roi_proxy:
  minutes_saved_per_item:
  items_per_month:
  cycle_time_delta:
  error_rate_delta:
  throughput_delta:
  service_delta:
  cost_per_successful_task:
  confidence: low | medium | high
  caveat:
```

Do not convert proxy ROI into a sales claim without production evidence.

