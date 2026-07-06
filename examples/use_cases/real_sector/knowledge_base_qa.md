# Knowledge Base Q&A

## Problem

Employees cannot quickly find current SOP/KB answers and may rely on stale
tribal knowledge.

## AI Opportunity

Read-only RAG Q&A over one approved corpus with citations and
`insufficient_evidence` behavior.

## Data Required

SOP/KB documents, owners, update dates, ACL metadata, source URLs, gold
question-to-document evidence.

## Risk and HITL

Risk: stale answer, missing citation, unauthorized source, hallucination. MVP is
read-only and routes weak evidence to no-answer.

## Evaluation Plan

No-answer accuracy, citation precision, stale-doc rejection, retrieval recall,
faithfulness, p95 latency, cost per successful answer.

## MVP Scope

One corpus, text-only retrieval baseline, citations, no-answer path.

## Production Hardening

Data readiness checks, freshness pipeline, access control, feedback loop,
re-index rollback, and judge calibration if used.

