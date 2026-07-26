# Documentation Index

Status: navigation index, not authority

Canonical authority remains in the named documents, schemas, tools, prompts,
and evidence artifacts linked below.

## RAG Evaluation v2

- `docs/research/rag-eval-2026.md` - source-grounded research note.
- `docs/adr/ADR-001-rag-evaluation-v2.md` - architecture decision.
- `docs/rag/RAG_DATA_READINESS.md` - Stage 0 corpus and ingestion readiness.
- `docs/rag/RETRIEVAL_EVAL_PLAN.md` - stage model, baseline matrix, harness/delivery, routing, robustness, perturbation.
- `docs/rag/GENERATION_EVAL_PLAN.md` - generation, citations, abstention, judge policy.
- `docs/rag/RAG_ACCEPTANCE_CRITERIA.md` - stop-ship rules and maturity language.
- `docs/rag/RAG_EVAL_TOOL_ADAPTERS.md` - external scorer adapter guidance.
- `schemas/rag_eval_manifest.schema.json`,
  `schemas/rag_eval_case.schema.json`,
  `schemas/rag_eval_observation.schema.json`,
  `schemas/rag_eval_result.schema.json`, and
  `schemas/rag_eval_comparison.schema.json` - machine-readable contracts.
- `tools/rag_eval_validate.py`, `tools/rag_eval_score.py`, `tools/rag_eval_compare.py` - offline deterministic CLI tools.

Mechanism fixtures and examples are not empirical product evidence.
