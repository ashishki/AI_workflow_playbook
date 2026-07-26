# RAG Acceptance Criteria

## Production Gate

RAG is release-ready only when data, retrieval, generation, and end-to-end
criteria are all satisfied for the declared risk level.

Machine-readable RAG eval results may be `pass`, `fail`, `invalid`, or
`diagnostic`. They never assign release approval. Human or project governance
remains completion authority.

## Criteria Table

| Area | Minimum criterion |
|------|-------------------|
| Data readiness | Source inventory, parser coverage, metadata, freshness, ACL, and PII checks are current |
| Retrieval | Required query slices meet threshold and no stop-ship failures are open |
| Generation | Faithfulness, citation correctness, no-answer behavior, and unsafe-answer checks pass |
| E2E | User-facing workflow meets success, latency, cost, and human override targets |
| Monitoring | Freshness, retrieval latency, no-answer rate, and feedback path are observable |
| Rollback | Re-index, model fallback, or answer-disable path exists |
| Machine provenance | Manifest, cases, observations, result, and comparison refs include exact paths and SHA-256 hashes |
| Baseline comparison | Release-significant RAG changes compare current candidate against a compatible baseline |

## Stop-Ship Failures

Treat these as blockers:

- unauthorized restricted document retrieved
- answer fabricates claims without evidence in a high-risk workflow
- stale document wins when freshness is required
- citation points to a source that does not support the claim
- no-answer path is missing or bypassed
- corpus update/re-index cannot be rolled back
- judge is blocking without calibration
- protected holdout is exposed or contaminated
- result hashes, corpus hashes, or dataset hashes do not match
- invalid eval run is treated as pass
- E2E answer score hides retrieval or routing failure
- routed RAG leaks across domain or ACL boundary
- graph attribution claim relies only on self-referential answer shift
- release-significant RAG change lacks baseline comparison
- production claim is based only on generic or synthetic mechanism fixture

## Acceptance Record

Every release-significant RAG change should record:

- corpus version or hash
- query set version
- retrieval metrics
- generation metrics
- E2E workflow result
- cost and p95 latency
- open failures and risk acceptance
- reviewer and date

## Maturity Language

- Documented: human-readable plan and acceptance criteria exist.
- Formalized: manifest/cases/observations/result/comparison contracts exist.
- Enforced: validators and regression gates run deterministically.
- Tested: offline fixtures prove schema, scorer, comparator, and stop-ship
  behavior.
- Empirically validated: project-specific representative data, labels, baseline
  comparison, and governance approval support a production claim.

Do not call a project empirically validated because schemas, generic fixtures,
or validators pass.
