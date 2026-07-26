# RAG Eval Result

Result ID: `fixture_support_kb_rag_eval:lexical_baseline:baseline_observations`
Status: `pass`
Condition: `lexical_baseline`
Config fingerprint: `e1566f930c8c9a7f9363031a70e72ec404d8acf6530e7032c90194d12e5f5047`

## Metrics

| Metric | Value |
|--------|-------|
| `cost.cost_per_attempt_usd` | `0.0025` |
| `cost.cost_per_success_usd` | `0.0033333333333333335` |
| `generation.citation_traceability` | `1.0` |
| `generation.no_answer_accuracy` | `1.0` |
| `harness.avg_retrieval_call_count` | `1.0` |
| `harness.avg_retry_count` | `0.0` |
| `harness.returned_results_consumed_ratio` | `0.6363636363636364` |
| `harness.timeout_rate` | `0.0` |
| `latency.e2e_p50_ms` | `33.0` |
| `latency.e2e_p95_ms` | `48.25` |
| `latency.retrieval_p50_ms` | `4.0` |
| `latency.retrieval_p95_ms` | `5.6499999999999995` |
| `perturbation.agreement_with_human_labels` | `1.0` |
| `perturbation.answer_change_sensitivity` | `0.9` |
| `perturbation.coverage` | `1` |
| `perturbation.irrelevant_evidence_invariance` | `None` |
| `retrieval.acl_leak_rate` | `0.0` |
| `retrieval.duplicate_context_rate` | `0.0` |
| `retrieval.evidence_span_coverage` | `0.8571428571428571` |
| `retrieval.forbidden_evidence_rate` | `0.125` |
| `retrieval.hit_at_3` | `0.8571428571428571` |
| `retrieval.mrr` | `0.7857142857142857` |
| `retrieval.ndcg_at_3` | `0.804418536224494` |
| `retrieval.precision_at_3` | `0.6428571428571429` |
| `retrieval.recall_at_3` | `0.8571428571428571` |
| `retrieval.stale_doc_rejection` | `1.0` |
| `robustness.answer_accuracy_by_noise` | `{"clean": 0.8571428571428571, "high_noise": 0.0}` |
| `robustness.high_noise_degradation` | `0.8571428571428571` |
| `routing.collection_match_accuracy` | `0.8571428571428571` |
| `routing.cross_domain_leakage_rate` | `0.14285714285714285` |
| `routing.domain_match_accuracy` | `0.8571428571428571` |
| `routing.fallback_rate` | `0.2857142857142857` |
| `routing.no_route_rate` | `0.14285714285714285` |
| `routing.route_coverage` | `0.8571428571428571` |
| `routing.wrong_route_rate` | `0.0` |

## Stop-Ship Findings

none
