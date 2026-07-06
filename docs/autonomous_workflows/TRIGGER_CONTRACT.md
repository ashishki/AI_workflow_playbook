# Trigger Contract

## Required Fields

```yaml
trigger_contract:
  routine_name:
  trigger_type: manual | cron | webhook | event
  schedule_or_event:
  input_schema:
  idempotency_key:
  replay_protection:
  auth_or_signature:
  max_queue_delay:
  timeout:
  cancellation:
  retry_policy:
  fallback_policy:
  budget:
  owner:
```

## Trigger Rules

- Cron routines need owner, timezone, missed-run behavior, and overlap policy.
- Webhooks need signature verification, replay protection, and payload
  redaction.
- Event routines need dead-letter handling and idempotency keys.
- Manual routines need operator role and approval record when actions are risky.

