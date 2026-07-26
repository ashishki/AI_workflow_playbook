# ADR-001: RAG Evaluation v2

Status: accepted
Date: 2026-07-26

## Context

The existing Playbook RAG profile documents corpus readiness, retrieval eval,
generation eval, and RAG acceptance criteria. It intentionally keeps the
Playbook as a governance and evidence control plane, not a RAG runtime.

The missing capability is a portable, machine-readable, CI-friendly way to prove
what was evaluated, with exact input identities, deterministic stage metrics,
baseline/candidate comparison, stop-ship gates, and compatibility with
EvidenceBundle and HarnessEvalUnit evidence.

## Decision

Introduce RAG Evaluation v2 as a provider-neutral control-plane extension:

- Versioned JSON Schemas define manifests, cases, observations, results, and
  comparisons.
- Core CLI tools validate contracts, compute deterministic metrics, and compare
  baseline versus candidate results without network calls or model providers.
- External scorers and LLM-as-judge systems integrate through hashed artifacts;
  they do not become core dependencies.
- Text RAG must declare a lexical baseline or a justified exception.
- Agentic RAG is evaluated as `retriever + harness + delivery profile +
  context-consumption loop`, consistent with `HarnessEvalUnit`.
- Routed/domain topology and graph perturbation attribution remain conditional
  profiles, not default architecture.

## Rationale

Machine-readable contracts make RAG evidence reproducible and reviewable. A
Markdown eval plan is useful for human context, but it cannot reliably enforce
input hashes, dataset identity, judge calibration, regression thresholds, or
stop-ship semantics.

The core scorer is provider-neutral because the Playbook must run in CI without
API keys, network calls, paid models, or vendor lock-in. Deterministic metrics
such as hit@k, recall@k, MRR, nDCG@k, ACL leakage, stale evidence handling,
routing accuracy, harness consumption, latency percentiles, and comparison
deltas are sufficient to prove the mechanism.

Lexical baselines are required for text RAG because dense retrieval should not be
accepted without a sparse/lexical point of comparison. This is not a claim that
grep or BM25 always wins; it is a baseline discipline rule.

Routed and graph eval remain conditional because topology and perturbation add
configuration and cost. They are valuable when the corpus has real domain
boundaries or structured evidence, and over-engineering when those conditions do
not hold.

## Consequences

Projects can run an offline RAG eval smoke path in CI and attach result/comparison
artifacts to EvidenceBundle-style evidence. Result artifacts may report
`pass | fail | invalid | diagnostic`, but they never report `release_ready`,
`accepted`, or `human_approved`.

LLM judges remain advisory until calibration evidence exists. A blocking judge
must have model ID, prompt/rubric identity, human sample, agreement, false-pass,
false-fail, and stale-calibration policy recorded.

## Backward Compatibility

Existing `docs/retrieval_eval.md` remains the human-readable canonical summary.
Machine results live separately under `.playbook-artifacts/rag-eval/` and
project reports under `reports/rag_eval/`. The initializer adds the RAG eval kit
only when `--with-rag-eval` is passed.

Lean-Core remains lightweight. Standard/Strict projects that opt in receive
schemas, tools, a manifest scaffold, and verifier checks. Existing non-RAG
bootstrap output is not changed except for copied tool capability when the
project explicitly opts in.

## Out of Scope

- Production vector databases, embedding services, hosted dashboards, or generic
  RAG platforms.
- Mandatory GraphRAG, mandatory routed RAG, mandatory Ragas/DeepEval/ARES/BEIR/
  LangSmith/OpenAI Evals dependencies.
- Networked or paid model calls in required CI.
- Synthetic benchmark generation that claims empirical product proof.
- Any single composite score that hides safety, retrieval, generation, latency,
  cost, or stop-ship findings.
