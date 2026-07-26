# Minimal RAG Eval Example

This is an offline mechanism demonstration, not a real benchmark.

It includes a lexical baseline, a production-candidate condition, simple lookup,
no-answer, freshness, ACL, distractor/noise, one routed case, and one graph
perturbation observation.

Run from the repository root:

```bash
python tools/rag_eval_validate.py --root . --manifest examples/rag_eval/minimal/manifest.json --observations examples/rag_eval/minimal/candidate_observations.jsonl
python tools/rag_eval_score.py --root . --manifest examples/rag_eval/minimal/manifest.json --observations examples/rag_eval/minimal/baseline_observations.jsonl --condition lexical_baseline --json examples/rag_eval/minimal/baseline_result.json --report examples/rag_eval/minimal/baseline_result.md
python tools/rag_eval_score.py --root . --manifest examples/rag_eval/minimal/manifest.json --observations examples/rag_eval/minimal/candidate_observations.jsonl --condition production_candidate --json examples/rag_eval/minimal/candidate_result.json --report examples/rag_eval/minimal/candidate_result.md
python tools/rag_eval_compare.py --root . --baseline examples/rag_eval/minimal/baseline_result.json --candidate examples/rag_eval/minimal/candidate_result.json --manifest examples/rag_eval/minimal/manifest.json --json examples/rag_eval/minimal/comparison.json --report examples/rag_eval/minimal/comparison.md
```

Expected summary:

- baseline result: `pass`
- candidate result: `pass`
- comparison result: `pass`
- candidate improves hit@3 and MRR on this synthetic fixture
- latency/cost deltas are reported but do not override quality gates

Do not use these cases as production evidence. Replace the dataset, corpus
snapshot, observations, thresholds, and holdout policy with project-specific
curated or production-replay evidence before making empirical claims.
