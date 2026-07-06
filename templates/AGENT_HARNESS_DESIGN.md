# Agent Harness Design - {{PROJECT_NAME}}

Version: {{VERSION}}
Owner: {{OWNER}}
Last updated: {{DATE}}
Status: draft | approved | deprecated

## Harness Summary

| Field | Value |
|-------|-------|
| Harness name | {{NAME}} |
| Primary workflow | {{WORKFLOW}} |
| Solution shape | deterministic | workflow | bounded agent | higher-autonomy agent | hybrid |
| Runtime tier | T0 | T1 | T2 | T3 |
| Risk level | low | medium | high | regulated |
| Evaluation artifact | {{PATH}} |
| Trace artifact | {{PATH}} |

## Model and Prompt Boundary

| Area | Decision | Evidence |
|------|----------|----------|
| Default model/class | {{MODEL_OR_CLASS}} | {{WHY}} |
| Fallback/escalation | {{RULE}} | {{EVAL_OR_BUDGET_REF}} |
| System policy | {{PROMPT_REF}} | {{VERSION}} |
| Task prompt | {{PROMPT_REF}} | {{VERSION}} |
| Output schema | {{SCHEMA_REF}} | {{VALIDATION}} |
| Prompt cache boundary | {{STABLE_PREFIX / VOLATILE_SUFFIX / N/A}} | {{COST_REF}} |

## Tool Registry

| Tool | Schema/version | Side effect | Idempotent? | Permission class | Retry policy | Audit fields |
|------|----------------|-------------|-------------|------------------|--------------|--------------|
| {{TOOL}} | {{SCHEMA}} | read/write/destructive/spend/send | yes/no | allowed/ask/sandbox/escalate/blocked | {{RULE}} | {{FIELDS}} |

## Memory and State

| State | Scope | Persistence | Owner | Retention | Reset rule |
|-------|-------|-------------|-------|-----------|------------|
| {{STATE_NAME}} | per run / per user / global | none / DB / file / vector / cache | {{OWNER}} | {{RETENTION}} | {{RESET}} |

## Loop and Termination

- Max iterations:
- Timeout:
- Normal termination:
- Forced termination:
- Partial result behavior:
- Non-termination behavior:

## Retry and Recovery

| Failure | Detection | Retry cap | Recovery | Human handoff? | Eval case |
|---------|-----------|-----------|----------|----------------|-----------|
| {{FAILURE}} | {{SIGNAL}} | {{N}} | {{ACTION}} | yes/no | {{CASE_ID}} |

## Permission Policy

| Class | Allowed actions | Examples | Approval required |
|-------|-----------------|----------|-------------------|
| allowed | | | |
| ask | | | |
| sandbox | | | |
| escalate | | | |
| blocked | | | |

## Human Handoff

| Trigger | Question/approval requested | Owner | Trace event |
|---------|-----------------------------|-------|-------------|
| {{TRIGGER}} | {{REQUEST}} | {{OWNER}} | `human_handoff` |

## Trace Requirements

Required events:

- `run_start`
- `model_call`
- `tool_call`
- `tool_observation`
- `permission_decision`
- `retry`
- `recovery`
- `human_handoff`
- `run_end`

Trace schema: {{PATH_TO_TRACE_SCHEMA}}

## Evaluation Contract

| Slice | Metric | Threshold | Eval source |
|-------|--------|-----------|-------------|
| happy_path | task success rate | | |
| ambiguous_input | ask-not-guess rate | | |
| tool_error | recovery success rate | | |
| permission_boundary | unsafe action rate = 0 | | |
| long_loop | termination compliance | | |
| trace_completeness | required fields present | | |
| cost | cost per successful task | | |

## Open Risks

| Risk | Severity | Mitigation | Owner |
|------|----------|------------|-------|
| {{RISK}} | P0/P1/P2/P3 | {{MITIGATION}} | {{OWNER}} |
