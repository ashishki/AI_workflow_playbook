# Finding {{FINDING_ID}}: {{TITLE}}

---
artifact_kind: finding
project: {{PROJECT_NAME}}
status: open
severity: {{P0 \| P1 \| P2 \| P3}}
canonical: {{true \| false}}
generated: false
opened: {{DATE}}
source_review: {{PATH}}
tags: []
---

## Finding

{{Concrete bug, risk, drift, missing test, or governance violation.}}

## Evidence

| Evidence | Path |
|----------|------|
| Review source | `{{path}}` |
| Test or eval | `{{path_or_command}}` |

## Impact

{{What can break if this remains open.}}

## Required Fix

{{Specific action needed.}}

## Lifecycle

| Date | State | Notes |
|------|-------|-------|
| {{DATE}} | Open | {{notes}} |

