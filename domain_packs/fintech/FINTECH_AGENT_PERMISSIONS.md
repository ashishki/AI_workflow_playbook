# Fintech Agent Permissions

## Permission Classes

| Class | Allowed examples | Notes |
|-------|------------------|-------|
| read | Read approved policy docs, invoice metadata, ledger summaries | Respect data classification |
| draft | Draft comparison, reconciliation note, payment instruction | No external send/execute |
| ask | Request missing document or clarification | Record in audit trail |
| approval_required | Submit payment draft, vendor change, exception approval | Human owner decides |
| blocked | Execute payment, change counterparty, bypass KYC/AML, export secrets | Not agent-authorized |

## Tool Policy

Every finance tool must declare side effect, idempotency, permission class,
audit fields, rollback/compensation path, and budget/cost impact.

