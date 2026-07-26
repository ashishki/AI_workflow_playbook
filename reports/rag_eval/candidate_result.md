# RAG Eval Result

Result ID: `fixture_support_kb_rag_eval:production_candidate:candidate_observations`
Status: `pass`
Condition: `production_candidate`
Config fingerprint: `97c4b6683718b316bccb6fe2f9560065522fa282126be46c217c7b7f064048be`

## Metrics

| Metric | Value |
|--------|-------|
| `cost.cost_per_attempt_usd` | `0.00475` |
| `cost.cost_per_success_usd` | `0.00475` |
| `generation.citation_traceability` | `1.0` |
| `generation.no_answer_accuracy` | `1.0` |
| `harness.avg_retrieval_call_count` | `1.0` |
| `harness.avg_retry_count` | `0.0` |
| `harness.returned_results_consumed_ratio` | `0.6363636363636364` |
| `harness.timeout_rate` | `0.0` |
| `latency.e2e_p50_ms` | `47.5` |
| `latency.e2e_p95_ms` | `60.849999999999994` |
| `latency.retrieval_p50_ms` | `11.5` |
| `latency.retrieval_p95_ms` | `15.299999999999999` |
| `perturbation.agreement_with_human_labels` | `1.0` |
| `perturbation.answer_change_sensitivity` | `0.95` |
| `perturbation.coverage` | `1` |
| `perturbation.irrelevant_evidence_invariance` | `None` |
| `retrieval.acl_leak_rate` | `0.0` |
| `retrieval.duplicate_context_rate` | `0.0` |
| `retrieval.evidence_span_coverage` | `1.0` |
| `retrieval.forbidden_evidence_rate` | `0.125` |
| `retrieval.hit_at_3` | `1.0` |
| `retrieval.mrr` | `0.8571428571428571` |
| `retrieval.ndcg_at_3` | `0.8945513581632737` |
| `retrieval.precision_at_3` | `0.7142857142857143` |
| `retrieval.recall_at_3` | `1.0` |
| `retrieval.stale_doc_rejection` | `1.0` |
| `robustness.answer_accuracy_by_noise` | `{"clean": 1.0, "high_noise": 1.0}` |
| `robustness.high_noise_degradation` | `0.0` |
| `routing.collection_match_accuracy` | `1.0` |
| `routing.cross_domain_leakage_rate` | `0.14285714285714285` |
| `routing.domain_match_accuracy` | `1.0` |
| `routing.fallback_rate` | `0.0` |
| `routing.no_route_rate` | `0.0` |
| `routing.route_coverage` | `1.0` |
| `routing.wrong_route_rate` | `0.0` |

## Stop-Ship Findings

none
