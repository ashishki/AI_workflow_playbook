# Tool Permission Policy

## Permission Classes

| Class | Examples | Default |
|-------|----------|---------|
| Allowed | Read repo files, run safe tests, query read-only metadata | Agent may execute within task scope |
| Ask | New dependency, broad file rewrite, expensive model escalation | Ask user or operator first |
| Sandbox | Untrusted code, risky command, external data transform | Run in isolated environment or dry run |
| Escalate | Secrets, billing, production deploy, customer data export | Human owner approval |
| Blocked | Credential exfiltration, policy bypass, destructive action without rollback | Never execute |

## Tool Catalog Fields

Every LLM-callable tool should declare:

- name and version
- input schema
- side-effect class: read, write, destructive, external send, spend
- idempotency key or reason not idempotent
- required permission class
- retry policy
- audit/trace fields
- rollback or compensation path

## Review Rule

Permission is checked at each tool boundary. A single approval at session start
does not authorize later destructive or higher-blast-radius actions.

