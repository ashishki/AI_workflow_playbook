# Latency SLA Template

## Purpose

Latency is part of AI architecture. Agent loops, retrieval, reranking, judges,
and fallback paths must fit the workflow's SLA or be moved to async/batch mode.

## SLA Table

| Workflow | User-facing? | p50 target | p95 target | p99 target | Timeout | Fallback | Owner |
|----------|--------------|------------|------------|------------|---------|----------|-------|
| Example: support answer | yes | 2s | 8s | 15s | 20s | insufficient_evidence | product |
| Example: nightly eval | no | n/a | 30m | 60m | 90m | fail report | eval |

## Latency Budget

| Stage | Target | Notes |
|-------|--------|-------|
| Input validation | | deterministic |
| Retrieval/search | | include rerank if used |
| Model inference | | include retries and streaming policy |
| Tool calls | | include network and rate limits |
| Judge/eval | | avoid synchronous judge unless necessary |
| Human handoff | | not part of automated p95; record separately |

## Review Rule

Any model escalation, reranker, tool call, judge, or agent retry that changes
p95 latency must update this SLA or its project equivalent.

