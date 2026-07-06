# Data Quality Checklist

## Checklist

| Check | Pass evidence | Status |
|-------|---------------|--------|
| Source inventory complete | Every source has owner, format, update cadence, access scope | pending |
| Parser coverage measured | Parse success rate by format and sample failures recorded | pending |
| Empty docs handled | Empty and near-empty documents counted and excluded or justified | pending |
| Duplicates handled | Exact and near-duplicate policy recorded | pending |
| Freshness policy exists | Max age and stale-doc rejection behavior defined | pending |
| Metadata complete | Required metadata fields meet project threshold | pending |
| ACL metadata present | Restricted documents have enforceable access labels | pending |
| Citation IDs stable | Each chunk maps back to source document and location | pending |
| OCR/table quality sampled | Scanned docs, tables, and forms have sample quality evidence | pending |
| PII/regulated data classified | Redaction, retention, and logging rules documented | pending |
| Language normalized | Encoding, locale, synonym, and terminology issues addressed | pending |
| Gold evidence seeded | Representative query set maps to documents/spans | pending |

## Recommended Thresholds

Adjust thresholds by risk, but record the decision:

| Metric | Default starting target |
|--------|-------------------------|
| Parse success rate | 95 percent or explicit exception list |
| Required metadata completeness | 98 percent for production, 90 percent for prototype |
| Duplicate rate after dedupe | Below 2 percent or documented canonicalization |
| Restricted docs without ACL metadata | 0 |
| Gold query set size | 10 minimum prototype, 50+ for release-significant RAG |

## Evidence Locations

Record evidence paths in the project readiness artifact:

- parser report
- dedupe report
- metadata completeness report
- ACL check
- sample parsed documents
- gold evidence file
- data owner approval

