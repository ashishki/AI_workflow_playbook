# RAG Acceptance Criteria

## Production Gate

RAG is release-ready only when data, retrieval, generation, and end-to-end
criteria are all satisfied for the declared risk level.

## Criteria Table

| Area | Minimum criterion |
|------|-------------------|
| Data readiness | Source inventory, parser coverage, metadata, freshness, ACL, and PII checks are current |
| Retrieval | Required query slices meet threshold and no stop-ship failures are open |
| Generation | Faithfulness, citation correctness, no-answer behavior, and unsafe-answer checks pass |
| E2E | User-facing workflow meets success, latency, cost, and human override targets |
| Monitoring | Freshness, retrieval latency, no-answer rate, and feedback path are observable |
| Rollback | Re-index, model fallback, or answer-disable path exists |

## Stop-Ship Failures

Treat these as blockers:

- unauthorized restricted document retrieved
- answer fabricates claims without evidence in a high-risk workflow
- stale document wins when freshness is required
- citation points to a source that does not support the claim
- no-answer path is missing or bypassed
- corpus update/re-index cannot be rolled back
- judge is blocking without calibration

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

