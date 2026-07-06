# Secrets Management Checklist

## Checklist

| Check | Required evidence |
|-------|-------------------|
| Secrets source declared | Environment, vault, CI secret, or managed identity |
| No secret in prompts/traces | Redaction rule and sample check |
| Least privilege | Routine-specific credential scope |
| Rotation owner | Named owner and rotation interval |
| Webhook verification | HMAC/signature or equivalent |
| Secret access logged | Audit event or platform evidence |
| Local/dev secrets separated | No production credential in local fixtures |
| Failure redaction | Error messages do not leak credentials |

## Rule

Agents and routines receive references to secrets, not secret values, unless the
runtime has a documented secure injection boundary.

