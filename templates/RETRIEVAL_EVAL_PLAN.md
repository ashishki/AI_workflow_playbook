# Retrieval Eval Plan - {{PROJECT_NAME}}

Version: {{VERSION}}
Owner: {{OWNER}}
Date: {{DATE}}

Machine manifest: `.playbook/rag_eval_manifest.json` / n/a
Current baseline result:
Current candidate result:
Current comparison:

## Evaluated Unit

| Field | Decision |
|-------|----------|
| RAG shape | fixed_pipeline | agentic_search | routed | graph | hybrid |
| Production retriever | |
| Lexical baseline | grep | BM25 | sparse equivalent | justified exception |
| Harness type/version | fixed_pipeline | custom_agent | provider_native_cli | workflow_runner |
| Delivery profile | inline | file | progressive_disclosure |
| Context-consumption loop | n/a | declared |
| Corpus/dataset/config identity | manifest refs/hashes |
| No-answer policy | |
| Optional routing profile | off | on with activation criteria |
| Optional graph attribution profile | off | perturbation with independent oracle |

Agentic RAG evaluated unit is retriever + harness + delivery profile +
context-consumption loop. Do not evaluate retriever alone and claim agentic
quality.

## Stage Metrics

| Stage | Metrics / evidence |
|-------|--------------------|
| 0 Corpus/ingestion | parser coverage, duplicates, metadata/ACL, freshness, snapshot hash |
| 1 Query/routing | route coverage, domain/collection match, fallback, wrong-route, route latency/cost |
| 2 Candidate retrieval | hit@k, recall@k, precision@k, MRR, nDCG@k, no-answer, ACL, freshness |
| 3 Rerank/context | context precision/recall, duplicate context, token budget, citation mapping |
| 4 Generation | faithfulness, completeness, citation correctness/completeness, abstention |
| 5 Harness/E2E | calls, artifacts opened/read, returned vs consumed, retries, termination, cost/success |
| 6 Online/drift | no-answer rate, route/fallback distribution, index age, correction rate, rollback triggers |

## Query Set

| ID | Query | Slice | Expected docs/spans | Distractors | Notes |
|----|-------|-------|---------------------|-------------|-------|
| Q01 | | simple | | | |
| Q02 | | multi-doc | | | |
| Q03 | | multi-hop | | | |
| Q-FRESH-01 | | freshness | | | |
| Q-NA-01 | | no-answer | none | | |
| Q-ACL-01 | | permission | | | |

Minimum diagnostic seed may be 10 representative queries. Release or empirical
claims require a project-specific sample requirement. Small-N improvements are
descriptive, not statistically established. Stochastic paths need repeated
trials and paired per-case comparison.

## Baseline Matrix

| Condition | Required? | Purpose | Result ref |
|-----------|-----------|---------|------------|
| Lexical baseline | required for text RAG unless justified exception | grep/BM25/sparse point of comparison | |
| Production candidate | required | current system | |
| Dense baseline | required when production uses dense retrieval | isolate embedding/index value | |
| Hybrid/RRF candidate | conditional | test complementarity | |
| Routed candidate/fallback | conditional | test topology and recovery | |
| Graph + perturbation | conditional | test structured evidence attribution and cost | |

Do not choose architecture from one final-answer score.

## Metrics

| Metric | Threshold | Baseline | Current | Regression? |
|--------|-----------|----------|---------|-------------|
| recall@3 / hit@3 | | | | |
| recall@5 / hit@5 | | | | |
| MRR | | | | |
| citation precision | | | | |
| no-answer accuracy | | | | |
| stale-doc rejection | | | | |
| ACL leak rate | 0 | | | |
| p95 retrieval latency | | | | |
| returned-results-consumed ratio | | | | |
| wrong-route rate | | | | |
| cross-domain leakage rate | 0 for restricted slices | | | |
| perturbation sensitivity / invariance | conditional | | | |

## Noise and Robustness

| Scenario | Cases | Expected behavior | Result |
|----------|-------|-------------------|--------|
| clean corpus | | baseline | |
| low noise | | small/no degradation | |
| medium noise | | controlled degradation | |
| high noise | | degradation reported by stage | |
| hard semantic distractors | | no wrong answer from distractor | |
| duplicate/near-duplicate distractors | | no duplicate context dominance | |

## Conditional Routing

Activate routed/domain topology only when real business/domain boundaries, ACLs
or owners, maintained metadata hierarchy, costly route errors, or persistent
cross-domain distractors justify it.

Record domain match, collection match, route coverage, fallback, wrong-route,
cross-domain leakage, no-route/ambiguous behavior, route latency/cost,
taxonomy/version drift, and comparison to flat lexical/dense/hybrid baselines.
Include a case where the correct document exists but the wrong route hides it.

## Conditional Perturbation / Attribution

For graph or structured evidence RAG, record node deletion sensitivity, edge
deletion sensitivity, synonym/paraphrase invariance, entity-dedup ablation,
influential component ranking, perturbation budget, regeneration cost, and
agreement with human or independent attribution labels.

For text RAG, test required evidence deletion, irrelevant evidence deletion,
distractor insertion, and minimal sufficient evidence on a curated sample.
Semantic answer shift is a causal proxy, not ground truth.

## Stronger Oracle Checks

Template presence does not make these gates mandatory. Resolve
`Property-Required` and `Mutation-Required` through
`docs/testing/property_and_mutation_oracles.md` and record only applicable
deterministic retrieval/evaluator semantics, not stochastic answer quality.

| Gate | Resolved decision / predicate | Target | Exact command | Config / version | Threshold or rationale | Receipt / result | Exception |
|------|-------------------------------|--------|---------------|------------------|------------------------|------------------|-----------|
| Property | | ACL non-leakage, no-answer, fresh-over-stale, distractor rejection, or source mapping | | | | | |
| Mutation | | ACL/freshness/no-answer filters, ranking/threshold, or evaluator logic | | | | | |

## Eval History

| Date | Corpus version | Eval source | Summary | Decision |
|------|----------------|-------------|---------|----------|
| {{DATE}} | | | | |

## Failure Notes

| Failure | Query IDs | Root cause | Fix/test |
|---------|-----------|------------|----------|
| | | | |
