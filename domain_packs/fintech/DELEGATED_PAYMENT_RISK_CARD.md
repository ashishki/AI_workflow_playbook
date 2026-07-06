# Delegated Payment Risk Card

## Risk Summary

Delegated payments are high-risk and regulated. Treat every payment-capable
agent as requiring explicit authority, limits, confirmation, audit, and rollback
or compensation planning.

## Required Controls

| Control | Requirement |
|---------|-------------|
| Payment authority | Human approval before send/execute |
| Limits | Per transaction, per day, per user, per agent, per counterparty |
| Counterparty validation | Deterministic validation against approved master data |
| Confirmation | Distinct UI/path, not a prompt-only flag |
| Audit | Actor, agent, tool, amount, currency, counterparty, reason, trace ID |
| Idempotency | Payment instruction idempotency key |
| Retry | No blind retry of payment execution |
| Rollback | Reversal/void/compensation path or explicit "irreversible" warning |
| Monitoring | anomaly, duplicate, failed payment, approval latency |

## Stop Conditions

- Agent can execute payment without human approval.
- Counterparty or amount is model-generated without deterministic validation.
- Audit log cannot reconstruct who approved what.
- Retry can duplicate payment.
- Secrets or account credentials appear in traces/prompts.

