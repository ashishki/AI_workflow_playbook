# Fintech Agentic Finance Pack

Status: optional domain extension
Risk posture: regulated / high-blast-radius by default

## Purpose

This pack provides fintech-specific prompts, policies, and risk cards for
agentic finance scenarios. It is not core playbook policy and should not be used
as market research without domain/legal review.

## Domain Themes

| Theme | Use |
|-------|-----|
| Agentic finance | Bounded assistant workflows for finance operations |
| Corporate agents | Internal treasury, reconciliation, procurement, and reporting support |
| Delegated payments | Draft/prepare/route payment instructions with strict limits |
| Know Your Agent (KYA) | Identify agent, owner, permissions, limits, and audit trail |
| Compliance by design | Permissions, confirmation, audit, retention, and evidence from Phase 1 |

## Required Controls

- Human confirmation for payment, transfer, credit, account, or compliance action
- Transaction limits by agent, user, workflow, and period
- Strong audit log with trace ID and permission decision
- Explicit tool permissions and blocked actions
- Judge advisory-only unless calibrated and non-final for regulated decisions
- No model-only authority over eligibility, credit, compliance, or payments

## Use Case Seeds

| Use case | Minimum shape | Human authority |
|----------|---------------|-----------------|
| Invoice reconciliation assistant | Workflow + extraction | Accountant approves |
| Corporate payment draft agent | Bounded tool-use | Treasurer approves |
| KYC document checklist assistant | RAG/extraction | Compliance approves |
| Spend policy copilot | RAG + deterministic rules | Finance owner approves exceptions |

