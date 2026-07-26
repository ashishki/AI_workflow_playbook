# RAG Data Readiness - {{PROJECT_NAME}}

Version: {{VERSION}}
Owner: {{OWNER}}
Date: {{DATE}}
Status: draft | pass | blocked | accepted_with_risk

Maturity: documented | formalized | enforced | tested | empirically_validated

Machine manifest: `.playbook/rag_eval_manifest.json` / n/a
Corpus snapshot ref/hash:
Dataset ref/hash:

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
| chunk/source/span traceability | | |
| corpus snapshot identity | | |
| tombstone/deletion handling | | |

## Gold Evidence Seed

| Query ID | Query | Expected document/span | Slice | Notes |
|----------|-------|------------------------|-------|-------|
| Q01 | | | simple | |
| Q-NA-01 | | none | no-answer | |

## Dataset Layers

| Layer | Status | Evidence / owner |
|-------|--------|------------------|
| Curated gold seed | pending | representative queries, human-verified spans, no-answer, ACL/freshness |
| Synthetic expansion | pending | provenance, generator model/prompt/version, validation status |
| Adversarial set | pending | hard distractors, stale/current, contradictions, duplicates, prompt injection, citation spoof, unauthorized evidence |
| Protected holdout | n/a | curator, trusted runner, sanitized status ref, contamination/rotation policy |
| Production replay / online sample | n/a | privacy-safe refs, labels, time window, drift notes |

## Stop Conditions

| Stop condition | Status | Owner |
|----------------|--------|-------|
| restricted docs lack ACL metadata | pass/fail | |
| citations cannot map to source | pass/fail | |
| stale docs can outrank current docs | pass/fail | |
| no-answer behavior undefined | pass/fail | |
| protected holdout exposed or contaminated | pass/fail/n/a | |
| dataset/corpus hash mismatch | pass/fail | |

## Decision

Decision: pass | blocked | accepted_with_risk

Rationale:

Follow-up tasks:
