# gdev-agent Harness Card

Status: example
Purpose: illustrate bounded support-triage agent harness design without making
the agent more autonomous.

## Summary

| Area | Example decision |
|------|------------------|
| Workflow | Telegram/support ticket triage into structured draft and approval queue |
| Solution shape | Bounded tool-using agent |
| Runtime | T1 worker or n8n-owned workflow, depending on deployment |
| Human authority | Risky or low-confidence cases require approval before send/action |
| Eval artifact | `eval/harness_regression.jsonl` in the downstream repo |

## Harness Boundary

| Area | Example |
|------|---------|
| Model | One approved tool-use capable model class; escalation only for low confidence |
| Prompt | Input guard, extraction prompt, output guard, structured output schema |
| Tools | Ticket lookup, classification, draft response, approval queue update |
| Memory/state | No open-ended memory; request ID, audit state, approval state only |
| Retry/recovery | Retry schema errors once; tool failures go to pending manual review |
| Permissions | Read ticket; write draft; cannot send/customer-impact without approval |
| Trace | guard outcome, tool calls, confidence, approval decision, cost, latency |
| HITL | Risky flag, low confidence, policy stress, malformed input |
| Termination | End after draft queued, blocked input, or manual handoff |

## Eval Slices

| Slice | Example cases |
|-------|---------------|
| ambiguous ticket | Missing customer intent -> ask/handoff |
| prompt injection | User asks agent to ignore policy -> blocked |
| low confidence | Confidence below threshold -> approval queue |
| risky action | Refund/delete/send -> human approval |
| malformed input | Bad payload -> validation error |
| policy stress | Sensitive or abusive content -> guard path |

## Review Note

This example is intentionally bounded. The improvement path is better traces,
evals, and approval behavior, not broader autonomy.

