# Retrieval Eval Plan - {{PROJECT_NAME}}

Version: {{VERSION}}
Owner: {{OWNER}}
Date: {{DATE}}

## Query Set

| ID | Query | Slice | Expected docs/spans | Distractors | Notes |
|----|-------|-------|---------------------|-------------|-------|
| Q01 | | simple | | | |
| Q02 | | multi-doc | | | |
| Q03 | | multi-hop | | | |
| Q-FRESH-01 | | freshness | | | |
| Q-NA-01 | | no-answer | none | | |
| Q-ACL-01 | | permission | | | |

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

## Eval History

| Date | Corpus version | Eval source | Summary | Decision |
|------|----------------|-------------|---------|----------|
| {{DATE}} | | | | |

## Failure Notes

| Failure | Query IDs | Root cause | Fix/test |
|---------|-----------|------------|----------|
| | | | |
