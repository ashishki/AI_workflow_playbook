# Know Your Agent Policy

## Purpose

KYA records who owns an agent, what it may do, what it may never do, and how its
actions are audited.

## KYA Record

| Field | Required |
|-------|----------|
| Agent name/version | yes |
| Business owner | yes |
| Technical owner | yes |
| Workflow scope | yes |
| Approved tools | yes |
| Permission classes | yes |
| Transaction/action limits | yes |
| Data access scope | yes |
| Human approval triggers | yes |
| Audit log fields | yes |
| Disable switch | yes |
| Last eval/calibration | yes |

## Forbidden Defaults

- No production payment authority by default.
- No hidden agent identity.
- No broad account access.
- No unbounded retry of financial actions.
- No final compliance or credit decision without human/legal-approved policy.

