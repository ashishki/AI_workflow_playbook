# RAG Eval Tool Adapters

Status: reference guide

Core Playbook RAG eval depends only on Python stdlib, `jsonschema`, and
`pytest` for tests. External scorer outputs are optional hashed artifacts.

## Canonical External Scorer Output

Every adapter should produce or reference a JSON artifact with:

- tool and version;
- model, prompt version, and rubric version when applicable;
- dataset ID/version/hash;
- timestamp;
- cost;
- metric names mapped to the RAG stage model;
- raw artifact ref with SHA-256;
- status: `advisory`, `calibrated`, or `invalid`.

External scorers do not assign `release_ready`, `accepted`, or
`human_approved`.

## Tool Mapping

| Tool | Useful stages | Input mapping | Output mapping | Caveats |
|------|---------------|---------------|----------------|---------|
| Ragas | generation faithfulness, answer relevance, context precision/recall | query, retrieved context, answer, citations, optional reference | external scorer artifact with metric values and judge/model prompt identity | Judge bias and metric semantics must be calibrated before blocking use |
| DeepEval | generation, citation entailment, custom rubrics, regression suites | case JSONL converted to test cases plus observation answer/context | hashed JSON output with test IDs, scores, model/rubric metadata | Do not make package a core dependency; blocking requires calibration |
| ARES | retrieval/generation quality with labeled data | dataset/corpus refs and model outputs | stage metrics plus dataset/sample identity | Requires project-owned setup and labels; output remains an external artifact |
| BEIR | retrieval baselines | corpus/query/qrels export from cases and expected evidence | retrieval metrics such as nDCG, recall, MRR | Good for sparse/dense baselines; not an agent harness or generation evaluator |
| LangSmith | traces, online/eval runs, judge outputs | observation fields mapped from traces: calls, tokens, latency, cost, artifacts | exported JSON with run IDs, scorer versions, hashes | Vendor lock-in risk; raw traces may contain sensitive data |
| OpenAI Evals | custom eval/judge workflows | manifest/cases translated to eval config; observations or generated outputs scored externally | JSON result artifact with model/prompt/rubric/calibration refs | Optional only; no API calls in core CI |
| Project-owned custom scorer | any stage | direct consumption of manifest/cases/observations | canonical external scorer output | Must document version, code hash, metric definitions, and failure semantics |

## Judge Authority

Before calibration, LLM-as-judge output is advisory. Blocking authority requires
the judge policy fields in `.playbook/rag_eval_manifest.json`, human-labeled
sample evidence, false-pass/false-fail analysis, zero stop-ship false negatives
for the declared sample, disagreement slices, recalibration triggers, and cost
accounting.

Do not give hidden expected answers to a judge that is scoring pure
faithfulness against retrieved context.
