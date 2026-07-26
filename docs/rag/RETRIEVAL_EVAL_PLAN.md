# Retrieval Eval Plan

## Purpose

Retrieval eval measures whether the system surfaces the right evidence. It does
not prove the final answer is correct.

RAG Evaluation v2 adds a machine-readable path:

```bash
python tools/rag_eval_validate.py --root . --manifest .playbook/rag_eval_manifest.json
python tools/rag_eval_score.py --root . --manifest .playbook/rag_eval_manifest.json \
  --observations .playbook/rag_eval_observations.jsonl --condition production_candidate \
  --json .playbook-artifacts/rag-eval/result.json --report reports/rag_eval/result.md
python tools/rag_eval_compare.py --root . \
  --baseline .playbook-artifacts/rag-eval/baseline.json \
  --candidate .playbook-artifacts/rag-eval/candidate.json \
  --manifest .playbook/rag_eval_manifest.json \
  --json .playbook-artifacts/rag-eval/comparison.json \
  --report reports/rag_eval/comparison.md
```

`docs/retrieval_eval.md` remains the human-readable summary. Machine results
live under `.playbook-artifacts/rag-eval/` and are linked from the Markdown.

## Stage Model

Do not allow an end-to-end answer score to hide earlier failures.

| Stage | Evaluation focus |
|-------|------------------|
| 0 | Corpus and ingestion readiness |
| 1 | Query understanding, filters, principal/ACL scope, routing |
| 2 | Candidate retrieval: lexical, dense, hybrid, freshness, no-answer, ACL |
| 3 | Reranking and context assembly: coverage, order, duplicates, token budget, citation mapping |
| 4 | Generation, citations, abstention, unsafe answer rate |
| 5 | Harness and end-to-end behavior: calls, files opened/read, consumed results, retries, termination, cost |
| 6 | Online monitoring and drift: route/fallback distribution, no-answer rate, index age, feedback, rollback triggers |

## Dataset

Build a layered, append-only query set with:

| Slice | Purpose |
|-------|---------|
| Simple lookup | Basic document recall |
| Multi-doc | Evidence must come from multiple documents |
| Multi-hop | Query requires chained evidence |
| No-answer | Corpus does not contain enough evidence |
| Freshness | Current document should beat stale document |
| Distractor | Similar but wrong document should be rejected |
| Permission | Restricted document must not appear for unauthorized user |

Dataset layers:

- curated gold seed with representative queries, verified evidence spans,
  no-answer, ACL, and freshness cases;
- synthetic expansion only for coverage/scaffolding, clearly marked by
  provenance and never used alone as empirical proof;
- adversarial cases: semantic distractors, stale/current conflicts,
  contradictory sources, duplicates, missing evidence, prompt injection in
  documents, citation spoofing, unauthorized evidence, multilingual/OCR/table
  failures;
- protected holdout owned by a curator/trusted runner, exposing only sanitized
  status and evidence refs;
- privacy-safe production replay or online samples with time-window and drift
  metadata.

The public stable query set is append-only. Retire a case only with an explicit
record when it is wrong, contaminated, or no longer matches the corpus.

## Baseline Matrix

Text RAG starts with a lexical baseline:

- local file search: grep or equivalent;
- document retrieval: BM25 or equivalent sparse baseline;
- production candidate;
- dense baseline when production uses dense retrieval;
- hybrid/RRF candidate when the hypothesis is complementarity.

This is not a claim that grep universally beats vector search. Dense retrieval
must be compared against a credible lexical baseline for the project corpus,
query distribution, harness, delivery profile, latency, and cost.

Agentic search compares `retriever x harness x delivery profile` only where the
factor isolation answers a real question. At minimum, compare lexical baseline
and production retriever in the same harness/delivery path, and record returned
versus consumed results.

Routed RAG compares flat lexical, flat dense or production flat baseline, hybrid
when applicable, routed candidate, and routed with fallback. GraphRAG compares a
text/flat baseline where possible, graph without attribution, graph plus dedup,
selected perturbation profile, and cost/latency impact.

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

Additional machine metrics include context duplicate rate, forbidden evidence
rate, citation traceability, domain/collection match, route coverage, fallback
rate, wrong-route rate, cross-domain leakage, returned-results-consumed ratio,
artifact open/read success, retry count, timeout rate, cost per attempt/success,
noise degradation, and perturbation sensitivity when applicable.

## Failure Taxonomy

| Failure | Typical cause |
|---------|---------------|
| Missing evidence | Bad parsing, chunking, embedding, filters, or corpus gap |
| Wrong evidence | Duplicates, stale docs, weak metadata, ambiguous query |
| Over-retrieval | Top-k too high, weak reranking, low threshold |
| Under-retrieval | Top-k too low, aggressive filter, poor synonyms |
| Citation mismatch | Chunk/source mapping broken |
| ACL leak | Corpus isolation failure |
| Returned not opened | Agent/harness returned correct result but file/artifact was not opened |
| Opened not used | Agent read correct evidence but failed to integrate it |
| Premature stop | Harness terminated before sufficient retrieval/context consumption |
| Context overflow/truncation | Correct evidence was dropped during assembly |
| Wrong route | Router hid otherwise retrievable gold evidence |

## Release Gate

Retrieval can pass only when:

- required slices have current metrics
- regression is compared against a baseline
- no-answer and ACL slices pass their stop conditions
- latency/cost are recorded
- failures are classified and tracked
- machine artifacts include exact input hashes when used for release evidence
