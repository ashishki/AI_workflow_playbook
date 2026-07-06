# Retrieval Eval Plan

## Purpose

Retrieval eval measures whether the system surfaces the right evidence. It does
not prove the final answer is correct.

## Dataset

Build an append-only query set with:

| Slice | Purpose |
|-------|---------|
| Simple lookup | Basic document recall |
| Multi-doc | Evidence must come from multiple documents |
| Multi-hop | Query requires chained evidence |
| No-answer | Corpus does not contain enough evidence |
| Freshness | Current document should beat stale document |
| Distractor | Similar but wrong document should be rejected |
| Permission | Restricted document must not appear for unauthorized user |

## Metrics

| Metric | What it catches |
|--------|-----------------|
| recall@k / hit@k | Correct document present in top results |
| MRR | Correct evidence appears early |
| citation precision | Retrieved/cited evidence is relevant |
| stale-doc rejection | Stale documents do not win when newer evidence exists |
| no-answer accuracy | `insufficient_evidence` fires when needed |
| ACL leak rate | Restricted evidence is not retrieved across boundaries |
| p95 retrieval latency | Retrieval remains usable under SLA |

## Failure Taxonomy

| Failure | Typical cause |
|---------|---------------|
| Missing evidence | Bad parsing, chunking, embedding, filters, or corpus gap |
| Wrong evidence | Duplicates, stale docs, weak metadata, ambiguous query |
| Over-retrieval | Top-k too high, weak reranking, low threshold |
| Under-retrieval | Top-k too low, aggressive filter, poor synonyms |
| Citation mismatch | Chunk/source mapping broken |
| ACL leak | Corpus isolation failure |

## Release Gate

Retrieval can pass only when:

- required slices have current metrics
- regression is compared against a baseline
- no-answer and ACL slices pass their stop conditions
- latency/cost are recorded
- failures are classified and tracked

