# RAG Data Readiness - {{PROJECT_NAME}}

Version: {{VERSION}}
Owner: {{OWNER}}
Date: {{DATE}}
Status: draft | pass | blocked | accepted_with_risk

## Corpus Inventory

| Source | Owner | Format | Volume | Update cadence | Access scope | Retention | Included? |
|--------|-------|--------|--------|----------------|--------------|-----------|-----------|
| {{SOURCE}} | | | | | | | yes/no |

## Parser Coverage

| Format | Parser | Sample size | Success rate | Known failures | Decision |
|--------|--------|-------------|--------------|----------------|----------|
| PDF | | | | | |
| DOCX | | | | | |
| HTML | | | | | |
| XLSX/CSV | | | | | |

## Data Quality

| Check | Result | Evidence |
|-------|--------|----------|
| empty/near-empty docs | | |
| duplicate/near-duplicate docs | | |
| stale docs | | |
| metadata completeness | | |
| ACL metadata completeness | | |
| OCR/table quality | | |
| PII/regulated data classification | | |
| language/encoding normalization | | |
| ontology/synonym coverage | | |

## Gold Evidence Seed

| Query ID | Query | Expected document/span | Slice | Notes |
|----------|-------|------------------------|-------|-------|
| Q01 | | | simple | |
| Q-NA-01 | | none | no-answer | |

## Stop Conditions

| Stop condition | Status | Owner |
|----------------|--------|-------|
| restricted docs lack ACL metadata | pass/fail | |
| citations cannot map to source | pass/fail | |
| stale docs can outrank current docs | pass/fail | |
| no-answer behavior undefined | pass/fail | |

## Decision

Decision: pass | blocked | accepted_with_risk

Rationale:

Follow-up tasks:
