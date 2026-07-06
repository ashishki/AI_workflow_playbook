# Agent Trace Schema - {{PROJECT_NAME}}

Version: {{VERSION}}
Owner: {{OWNER}}
Last updated: {{DATE}}

## JSONL Event Schema

```json
{
  "schema_version": "1.0",
  "run_id": "string",
  "span_id": "string",
  "parent_span_id": "string|null",
  "timestamp": "ISO-8601",
  "event_type": "run_start|model_call|tool_call|tool_observation|permission_decision|retry|recovery|human_handoff|run_end",
  "agent_role": "string",
  "task_id": "string|null",
  "input_ref": "string|null",
  "output_ref": "string|null",
  "tool_name": "string|null",
  "tool_call_id": "string|null",
  "permission_decision": "allowed|ask|sandbox|escalate|blocked|null",
  "retry_count": "integer",
  "recovery_action": "string|null",
  "cost_usd": "number|null",
  "latency_ms": "integer|null",
  "status": "success|failure|blocked|partial",
  "error_class": "string|null",
  "redaction_applied": "boolean"
}
```

## Required Fields by Event

| Event | Required fields |
|-------|-----------------|
| run_start | run_id, timestamp, agent_role, task_id |
| model_call | run_id, span_id, model/class, input_ref, output_ref, cost_usd, latency_ms |
| tool_call | run_id, span_id, tool_name, tool_call_id, permission_decision |
| tool_observation | run_id, parent_span_id, tool_call_id, output_ref, status |
| permission_decision | run_id, span_id, permission_decision, reason |
| retry | run_id, parent_span_id, retry_count, error_class |
| recovery | run_id, parent_span_id, recovery_action, status |
| human_handoff | run_id, span_id, reason, owner, decision_ref |
| run_end | run_id, status, cost_usd, latency_ms |

## Redaction Rule

Sensitive input/output payloads are stored by reference only. Trace rows should
not include secrets, raw PII, or regulated data.
