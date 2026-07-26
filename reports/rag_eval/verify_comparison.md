# RAG Eval Comparison

Status: `pass`
Compatible: `True`

## Metric Deltas

| Metric | Baseline | Candidate | Delta | Severity |
|--------|----------|-----------|-------|----------|
| `retrieval.hit_at_3` | `0.8571428571428571` | `1.0` | `0.1428571428571429` | `none` |
| `retrieval.mrr` | `0.7857142857142857` | `0.8571428571428571` | `0.0714285714285714` | `none` |
| `retrieval.acl_leak_rate` | `0.0` | `0.0` | `0.0` | `none` |
| `generation.no_answer_accuracy` | `1.0` | `1.0` | `0.0` | `none` |
| `routing.domain_match_accuracy` | `0.8571428571428571` | `1.0` | `0.1428571428571429` | `none` |
| `harness.returned_results_consumed_ratio` | `0.6363636363636364` | `0.6363636363636364` | `0.0` | `none` |
| `latency.e2e_p95_ms` | `48.25` | `60.849999999999994` | `12.599999999999994` | `none` |

## Findings

none
