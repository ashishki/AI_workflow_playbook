# RAG Evaluation Research Note, 2026

Status: research note, not authority
Created: 2026-07-26

Canonical implementation authority lives in the ADR, schemas, templates, prompts,
and executable validators. This note records the source-grounded reasoning behind
RAG Evaluation v2.

## Sources

- XGRAG: A Graph-Native Framework for Explaining KG-based Retrieval-Augmented Generation, arXiv:2604.24623, submitted 2026-04-27. Source: https://arxiv.org/abs/2604.24623 and PDF https://arxiv.org/pdf/2604.24623.
- Is Grep All You Need? How Agent Harnesses Reshape Agentic Search, arXiv:2605.15184, PDF source https://arxiv.org/pdf/2605.15184.
- DCD: Domain-Oriented Design for Controlled Retrieval-Augmented Generation, arXiv:2604.07590, v2 revised 2026-06-11. Source: https://arxiv.org/abs/2604.07590 and PDF https://arxiv.org/pdf/2604.07590.

## XGRAG

XGRAG argues that GraphRAG explanations need graph-native perturbations rather
than only token- or text-level attribution. Its pipeline retrieves a graph,
deduplicates semantically equivalent entities, removes or changes graph
components, regenerates answers, and scores how much the output shifts. The paper
specifically distinguishes node removal, edge removal, and synonym injection as
different probes of dependency, and treats the repeated generation cost as part
of the explanation design.

Adopted in Playbook:

- Add a conditional graph/structured-evidence evaluation profile with
  `rag_mode: graph` and `attribution_mode: perturbation`.
- Track node deletion sensitivity, edge deletion sensitivity,
  synonym/paraphrase invariance, entity-dedup ablation, influential component
  ranking, perturbation coverage, invalid perturbations, and regeneration cost.
- Require independent evidence for high-risk attribution claims. Semantic answer
  shift is a causal proxy, not its own ground truth.

Adopted conditionally:

- Graph attribution is available only when the project actually has structured
  evidence such as a graph, typed entity/relation model, or equivalent
  source-linked evidence components.
- Text RAG may borrow perturbation ideas at the evidence-span level: removing
  required gold evidence should degrade or change the answer; adding distractors
  should not; removing irrelevant evidence should not materially affect the
  result.

Rejected:

- Do not add GraphRAG runtime, graph database, graph builder, or repeated LLM
  generation runner to core Playbook.
- Do not treat semantic shift alone as release authority.

## Is Grep All You Need?

The paper studies agentic search across lexical and vector retrieval, custom and
provider-native harnesses, inline and file-based delivery, and increasing
irrelevant surrounding context. It reports that grep often wins in the studied
LongMemEval-like setup, while also emphasizing that harness and delivery path can
invert or erase retrieval advantages. The paper explicitly cautions that it does
not prove grep is universally better than vector search.

Adopted in Playbook:

- Agentic RAG's evaluated unit is `retriever + harness + delivery profile +
  context-consumption loop`, not retriever alone.
- Text RAG requires a lexical baseline: grep for local-file search or BM25/sparse
  equivalent for document retrieval.
- Eval observations must capture harness type/version, delivery profile,
  retrieval calls, returned versus consumed results, opened/read artifacts,
  retries, termination, tokens, latency, cost, and failure stage.
- Noise robustness is first-class: clean, low/medium/high noise, hard semantic
  distractors, and duplicate/near-duplicate distractors.

Caveats:

- The Playbook does not declare grep the default winner.
- Dense, sparse, and hybrid retrieval are compared against the project corpus,
  query distribution, harness, delivery path, and cost/latency envelope.

Rejected:

- No mandatory Unix-only grep dependency for every RAG project.
- No replacement of embedding/vector systems without project-specific evidence.

## DCD

DCD proposes Domain -> Collection -> Document organization and structured-output
routing to restrict the search space before retrieval. The paper's own
discussion notes that explicit routing can make the correct chunk unreachable
when domain or collection classification is wrong. It also reports synthetic or
template-like evaluation data, LLM-as-judge answer scoring, and configuration
complexity for heterogeneous corpora.

Adopted in Playbook:

- Add a conditional routed/topology profile where domain and collection routing
  quality is a first-class stage before candidate retrieval.
- Track domain match, collection match, route coverage, fallback rate,
  wrong-route rate, cross-domain leakage, no-route or ambiguous-route behavior,
  latency/cost, taxonomy drift, and comparisons against flat lexical, flat dense,
  and hybrid baselines.
- Include explicit tests where the correct document exists but the router hides
  it from retrieval.

Activation criteria:

- Use routed topology when stable business/domain boundaries exist, ACLs or
  owners differ by domain, flat retrieval returns cross-domain distractors, route
  errors are costly, or a maintained metadata hierarchy already exists.
- Do not use routed topology when the corpus is small, fully unstructured,
  boundaries are artificial, or taxonomy maintenance costs exceed expected value.

Caveats:

- DCD results do not transfer automatically to arbitrary unstructured corpora.
- LLM-as-judge output remains advisory until calibrated under Playbook judge
  policy.

## 2026 Emphasis Versus Established 2024-2025 Practice

Established practice already includes corpus readiness before embeddings,
separate retrieval and generation eval, gold evidence spans, no-answer cases,
human labels, calibrated judges, and baseline comparisons.

RAG Evaluation v2 adds three newer emphases:

- Harness x retriever x delivery must be evaluated as a combined unit for
  agentic RAG.
- Perturbation-based evidence attribution can explain graph or structured RAG,
  but only as a conditional profile with independent validation for high-risk
  claims.
- Domain topology and route quality are first-class evaluation stages when the
  corpus has real, maintained boundaries.
