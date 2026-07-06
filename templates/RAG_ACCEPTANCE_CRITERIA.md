# RAG Acceptance Criteria - {{PROJECT_NAME}}

Version: {{VERSION}}
Owner: {{OWNER}}
Date: {{DATE}}

## Release Criteria

| Area | Criterion | Evidence | Status |
|------|-----------|----------|--------|
| data readiness | readiness artifact status is pass or accepted_with_risk | | pending |
| retrieval | required slices meet thresholds | | pending |
| generation | faithfulness/citation/no-answer checks pass | | pending |
| E2E workflow | user-facing scenario meets success metric | | pending |
| latency | p95 under SLA | | pending |
| cost | cost per successful task under budget | | pending |
| monitoring | freshness, no-answer, latency, feedback signals exist | | pending |
| rollback | re-index/fallback/disable path exists | | pending |

## Stop-Ship Checks

| Check | Must be | Status |
|-------|---------|--------|
| restricted evidence leak | 0 | |
| unsupported answer in high-risk slice | 0 | |
| stale document beats current evidence | 0 unless accepted by owner | |
| citation mismatch | 0 for launch-critical claims | |
| uncalibrated judge blocks release | false | |

## Decision

Decision: release | block | release_with_risk_acceptance

Approver:

Risk acceptance if any:
