# Support KB Data Readiness Example

Status: example
Scenario: read-only RAG Q&A over an internal support knowledge base.

## Corpus Inventory

| Source | Owner | Format | Update cadence | Access | Included |
|--------|-------|--------|----------------|--------|----------|
| Support KB | Support Ops | Markdown/HTML | daily | internal support | yes |
| Legacy PDFs | Support Ops | PDF | quarterly | internal support | maybe |
| Ticket exports | Support Ops | CSV/chat | weekly | restricted PII | no for v1 |

## Readiness Findings

| Check | Example result | Decision |
|-------|----------------|----------|
| Parser coverage | Markdown/HTML sample parsed cleanly; PDF sample has table loss | Include Markdown/HTML first |
| Duplicates | FAQ pages duplicated across locales | Add canonical URL metadata |
| Freshness | Article `updated_at` exists | Filter stale docs after max age |
| Metadata | source_id, title, URL, updated_at present; product_area missing | Add product_area during ingestion |
| ACL | v1 corpus is internal support only | No customer-facing access |
| PII | Ticket exports contain PII | Exclude tickets from v1 |
| Gold evidence | 12 query-to-article cases seeded | Expand before release |

## Stop Conditions

- Do not include ticket exports until PII redaction and ACL are proven.
- Do not claim production readiness until stale-doc rejection and no-answer
  behavior pass eval.

