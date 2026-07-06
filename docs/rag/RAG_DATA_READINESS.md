# RAG Data Readiness

## Purpose

RAG readiness starts before embeddings. A corpus that is stale, duplicated,
poorly parsed, missing metadata, or access-control ambiguous will produce weak
retrieval no matter which model or vector database is selected.

Use this gate before `docs/retrieval_eval.md`.

## Readiness Flow

```text
source inventory -> parser coverage -> quality checks -> metadata/ACL check
-> gold evidence slices -> retrieval eval -> generation eval -> E2E acceptance
```

## Required Inventory

| Area | Questions |
|------|-----------|
| Sources | Which systems, folders, APIs, or exports feed the corpus? |
| Formats | PDF, HTML, DOCX, XLSX, images, tickets, chats, database rows |
| Owner | Who can approve source inclusion and deletion? |
| Freshness | How often does each source change? |
| Access control | Who may see each document or field? |
| Retention | What must be deleted, archived, or redacted? |
| Language/locale | Languages, encodings, transliteration, terminology |
| Metadata | Required fields for filtering, citations, freshness, ACL, and ontology |

## Data Quality Gate

Block retrieval work until these have an explicit status:

| Check | Required evidence |
|-------|-------------------|
| Parse success rate | Sample parse report by format |
| Empty/near-empty docs | Count and handling rule |
| Duplicate/near-duplicate docs | Count, dedupe policy, canonical source rule |
| Staleness | Max age by source and stale-doc rejection rule |
| Metadata completeness | Required metadata coverage percentage |
| OCR quality | OCR confidence or manual sample for scanned documents |
| Table/form extraction | Field coverage for structured documents |
| PII/regulated data | Redaction, retention, and access-control plan |
| Ontology | Entity names, synonym map, taxonomy, or explicit decision not to use one |

## Stop Conditions

Do not proceed to production RAG when:

- source ownership is unknown
- parse failures are unmeasured
- access-control metadata is missing for restricted data
- stale documents can outrank current documents without detection
- no-answer behavior is undefined
- citations cannot be traced to source documents
- gold query-to-document evidence does not exist

## Artifact Links

- Use `templates/RAG_DATA_READINESS.md` for project-specific readiness.
- Use `docs/rag/DATA_QUALITY_CHECKLIST.md` for a concrete pass/fail checklist.
- Use `docs/rag/RETRIEVAL_EVAL_PLAN.md` for retriever metrics.
- Use `docs/rag/GENERATION_EVAL_PLAN.md` for answer quality.
- Use `docs/rag/RAG_ACCEPTANCE_CRITERIA.md` for release gates.

