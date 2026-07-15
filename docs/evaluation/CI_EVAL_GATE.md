# CI Evaluation Gate

## Purpose

CI eval gates make the playbook's evaluation-first rule enforceable. Keep gates
optional and capability-scoped; do not force every project into heavy eval on
every commit.

## Gate Types

| Gate | Use when | Failure means |
|------|----------|---------------|
| Seeded regression | Known unsafe or previously fixed cases exist | P0/P1 depending on severity |
| Holdout acceptance | `Holdout-Required` resolves to required | Failed, missing, stale, invalid, flaky, or contaminated evidence blocks merge/phase advance |
| Capability eval | RAG, tool-use, agentic, planning, or compliance profile is active | Profile artifact is stale or below threshold |
| Cost budget | Telemetry exists and budget has thresholds | Cost boundary exceeded |
| Judge calibration | LLM judge is blocking or release-significant | Judge cannot be trusted for that gate |
| Data readiness lint | RAG corpus ingestion changed | Corpus is not ready for retrieval eval |
| Trace completeness | Agent/harness behavior changed | Runtime evidence is insufficient for review |

## Minimum CI Shape

```yaml
eval_gates:
  seeded_regression:
    command: "python -m pytest tests/eval/test_seeded_regressions.py -q"
    required_for: "all AI behavior changes"
  holdout_acceptance:
    command_source: "project-owned protected command alias"
    trigger: "merge, phase, release, or manual protected job"
    required_for: "resolved Holdout-Required: required"
    public_status: "coarse result + suite version/digest + sanitized evidence ref"
  rag_data_readiness:
    command: "python -m pytest tests/eval/test_rag_data_readiness.py -q"
    required_for: "rag:ingestion"
  judge_calibration:
    command: "python -m pytest tests/eval/test_judge_calibration.py -q"
    required_for: "blocking LLM judges"
  cost_rollup:
    command: "python tools/cost_rollup.py --strict --require-file"
    required_for: "declared cost thresholds"
```

## Gate Design Rules

- Make the smallest reliable gate blocking.
- Keep expensive E2E eval on schedule, release, or manual workflow when needed.
- Store the baseline in the corresponding eval artifact.
- Require an `Eval Source` and date for every metric row.
- Fail closed for missing artifacts when the profile is active.
- A required holdout accepts only current `pass` evidence for the exact
  commit/diff and suite digest. An optional holdout remains advisory.
- Distinguish an implementation `fail` from an `invalid` infrastructure,
  credential, scorer, or evidence run; neither satisfies a required gate.
- Keep raw holdout cases, logs, and bundles restricted. Public CI output contains
  only coarse status, suite version/digest, and a sanitized evidence reference.
- Treat judge calibration as stale after judge model, prompt, rubric, or label
  distribution changes.
