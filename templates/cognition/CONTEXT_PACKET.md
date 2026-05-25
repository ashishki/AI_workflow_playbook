# Context Packet - {{PROJECT_NAME}} - {{ROLE}}

---
artifact_kind: context_packet
project: {{PROJECT_NAME}}
role: {{ROLE}}
scope: {{SCOPE}}
source_manifest: {{SOURCE_MANIFEST}}
generated: {{true \| false}}
canonical: false
created: {{DATE}}
---

## Scope

{{Task, review, regression, architecture change, or research question.}}

## Role

{{strategist \| orchestrator \| implementer \| reviewer \| researcher \| postmortem-writer}}

## Canonical Artifacts

| Artifact | Path | Why included |
|----------|------|--------------|
| {{artifact}} | `{{path}}` | {{reason}} |

## Included Context

{{Short excerpts or facts that materially change action.}}

## Excluded Context

{{What was intentionally excluded to keep the packet bounded.}}

## Decision Lineage

{{ADR and decision log links.}}

## Evidence

{{Tests, eval rows, evidence index rows, review reports.}}

## Open Findings

{{Relevant findings and current lifecycle state.}}

## Eval Gates

{{Applicable eval artifacts, baseline, current result, and exact eval source.}}

## Next Action

{{The next bounded action for the receiving role.}}

