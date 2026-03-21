# Retrieval Evaluation — {{PROJECT_NAME}}

<!--
Copy to docs/retrieval_eval.md in your project when RAG Profile = ON.
Update this file whenever retrieval logic changes (chunking, embedding, ranking, evidence assembly).
Retrieval quality is evaluated separately from code quality — a green test suite does not imply good retrieval.
-->

Version: {{N}}
Last updated: {{DATE}}
Changed by: {{TASK_ID}} — {{TASK_TITLE}}

---

## Evaluation Dataset

| ID | Query | Expected top document(s) | Notes |
|----|-------|--------------------------|-------|
| Q01 | {{query}} | {{doc_id or title}} | {{e.g., canonical answer, section}} |
| Q02 | | | |
| Q-NA-01 | {{query with no good answer}} | — (should return insufficient_evidence) | no-answer test case |

<!--
Maintain at least 10 representative queries covering:
- Typical successful retrievals
- Edge cases (ambiguous queries, partial matches)
- Queries that should trigger insufficient_evidence (no-answer cases)
Keep the dataset append-only. Add new queries; do not remove old ones.
-->

---

## Baseline Metrics

_Recorded at: {{DATE}} after {{TASK_ID}}_

| Metric | Value | Notes |
|--------|-------|-------|
| hit@3 | | Fraction of queries where correct doc is in top 3 results |
| hit@5 | | Fraction of queries where correct doc is in top 5 results |
| MRR | | Mean Reciprocal Rank across query set |
| Citation precision | | Fraction of cited docs that are relevant to the query |
| No-answer accuracy | | Fraction of no-answer queries correctly returning insufficient_evidence |
| Median retrieval latency | | p50 latency for the retrieve stage (ms) |
| p95 retrieval latency | | p95 latency for the retrieve stage (ms) |

<!--
Metrics do not need to be computed programmatically on every run.
A manual spot-check against the query set is acceptable for early phases.
Automate when the corpus and query set are stable.
-->

---

## Current Metrics

_Recorded at: {{DATE}} after {{TASK_ID}}_

| Metric | Previous | Current | Delta | Regression? |
|--------|----------|---------|-------|-------------|
| hit@3 | | | | |
| hit@5 | | | | |
| MRR | | | | |
| Citation precision | | | | |
| No-answer accuracy | | | | |
| Median retrieval latency | | | | |
| p95 retrieval latency | | | | |

---

## Regression Notes

<!--
Record any metrics that regressed and why.
If a regression is acceptable (e.g., latency increased due to reranking that improved quality),
document the trade-off explicitly.
If a regression is not acceptable, add a retrieval finding to CODEX_PROMPT.md ## RAG State.
-->

{{none | description of regressions and their justification}}

---

## No-Answer Behavior Quality

Did no-answer queries correctly trigger `insufficient_evidence`?

| Query ID | Result | Expected | Pass? |
|----------|--------|----------|-------|
| Q-NA-01 | | insufficient_evidence | |

Notes: {{any patterns or failure modes observed}}

---

## Evidence / Citation Correctness

For a sample of successful queries, verify that the assembled evidence matches the source:

| Query ID | Citation present? | Source matches? | Notes |
|----------|-------------------|-----------------|-------|
| Q01 | | | |
| Q02 | | | |

---

## Open Retrieval Findings

<!--
Record retrieval-specific issues here. Copy to CODEX_PROMPT.md ## RAG State > Open retrieval findings.
Format matches the Open Findings format in CODEX_PROMPT.md.
-->

none

---

## Evaluation History

<!--
Append a one-line summary after each evaluation run.
-->

| Date | Task | hit@3 | MRR | No-answer acc. | Note |
|------|------|-------|-----|----------------|------|
| {{DATE}} | {{TASK_ID}} | — | — | — | initial baseline |
