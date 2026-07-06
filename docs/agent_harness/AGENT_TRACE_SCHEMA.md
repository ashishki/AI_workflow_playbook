# Agent Trace Schema

## Purpose

Agent traces are review and eval evidence. They must show what the agent saw,
decided, called, retried, recovered, spent, and handed off.

## JSONL Shape

Each line is one event. Keep sensitive data redacted before storage.

```json
{
  "schema_version": "1.0",
  "run_id": "run_001",
  "span_id": "span_001",
  "parent_span_id": null,
  "timestamp": "2026-01-01T00:00:00Z",
  "event_type": "model_call",
  "agent_role": "triage_agent",
  "task_id": "T01",
  "input_ref": "artifacts/run_001/input.redacted.json",
  "output_ref": "artifacts/run_001/output.redacted.json",
  "tool_name": null,
  "tool_call_id": null,
  "permission_decision": "allowed",
  "retry_count": 0,
  "recovery_action": null,
  "cost_usd": 0.012,
  "latency_ms": 840,
  "status": "success",
  "error_class": null,
  "redaction_applied": true
}
```

## Required Event Types

| Event | Required when |
|-------|---------------|
| `run_start` | Every run |
| `model_call` | Every LLM inference |
| `tool_call` | Before tool execution |
| `tool_observation` | After tool execution |
| `permission_decision` | Before side-effecting or restricted action |
| `retry` | Every retry attempt |
| `recovery` | Fallback, partial result, or dead-letter path |
| `human_handoff` | User/operator approval or clarification needed |
| `run_end` | Every terminal state |

## Completeness Rule

If a reviewer cannot reconstruct the agent's decision path, tool side effects,
permission decisions, and terminal state from traces and artifacts, the run is
not valid eval evidence.

