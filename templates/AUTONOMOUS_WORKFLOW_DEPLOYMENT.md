# Autonomous Workflow Deployment - {{PROJECT_NAME}}

Version: {{VERSION}}
Owner: {{OWNER}}
Date: {{DATE}}
Status: draft | approved | deployed | disabled

## Routine Summary

| Field | Value |
|-------|-------|
| Routine name | {{NAME}} |
| Workflow | {{WORKFLOW}} |
| Trigger type | manual | cron | webhook | event |
| Runtime target | local | GitHub Actions | hosted sandbox | self-hosted worker | cloud function |
| Runtime tier | T0 | T1 | T2 | T3 |
| Human owner | {{OWNER}} |
| Budget | {{BUDGET}} |

## Trigger Contract

| Field | Value |
|-------|-------|
| Schedule/event | |
| Input schema | |
| Auth/signature | |
| Replay protection | |
| Idempotency key | |
| Overlap policy | |

## Execution Contract

| Area | Decision |
|------|----------|
| Timeout | |
| Retry policy | |
| Cancellation | |
| Dead-letter handling | |
| Fallback | |
| Rollback/compensation | |
| Disable switch | |

## Secrets

| Secret reference | Scope | Rotation owner | Redaction rule |
|------------------|-------|----------------|----------------|
| | | | |

## Monitoring

| Signal | Threshold | Owner |
|--------|-----------|-------|
| success rate | | |
| retry rate | | |
| timeout rate | | |
| DLQ rate | | |
| cost per completed job | | |
| p95 queue delay | | |
| p95 runtime | | |

## Eval and Reliability

| Test | Command/source | Threshold |
|------|----------------|-----------|
| trigger smoke | | |
| idempotency | | |
| retry/fallback | | |
| permission boundary | | |
| cost budget | | |

## Decision

Decision: deploy | do_not_deploy | deploy_with_limits

Rationale:
