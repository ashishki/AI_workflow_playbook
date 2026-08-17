# DeepSeek Harness Adapter Implementation Report

Status: mechanism implemented; live provider screening pending

## Baseline

- Repository baseline: `8e6aeb0ca936cdabe798a06155662fd17d6e4996`
- Upstream DSH release: `dsh-v0.1.0-rc.7`
- Upstream DSH commit: `99f6f02fecdb7dff40c3fbc9470f5907c29f74ca`

## Implemented

- optional Python SDK adapter for Harness Lab;
- pinned SDK and bundled-runtime identity checks;
- restricted project-owned Cordis profile;
- environment credential scrub during subprocess launch;
- DSH event, notification, session-log, prompt/tool identity, token, tool-call,
  latency, and optional-cost capture;
- Playbook command receipt, HarnessEvalUnit, and EvidenceBundle integration;
- doctor command;
- resumable 12-run baseline/candidate screening;
- rate-limit quarantine with exit code `75`;
- credential pause with exit code `76`;
- comparison, LOC delta, runtime metrics, and advisory recommendation;
- human decision remains external and pending.

## Maturity boundary

Implemented and testable without provider calls:

- profile validation;
- environment scrub;
- adapter event parsing and evidence production;
- rate-limit classification;
- screening orchestration and resume;
- recommendation hard gates.

Not yet established:

- real DeepSeek task-success or cost advantage;
- improvement from Minimal Implementation Policy on DeepSeek;
- equivalence with Codex results;
- stability across future DSH release candidates.

## Required live action

```bash
export DEEPSEEK_API_KEY='...'
python tools/run_deepseek_harness_screening.py --trials 3
```

If rate-limited:

```bash
python tools/run_deepseek_harness_screening.py --trials 3 --resume
```

The final decision must be based on generated evidence, not this report.

## Local verification before branch publication

- DeepSeek adapter/profile/runtime parsing and fake-SDK tests: `5 passed`.
- Rate-limit quarantine/resume test: `1 passed`.
- Existing diff-scope/comparison and selected CLI compatibility tests: `16 passed` and `9 passed` in focused groups.
- Fake empirical screening produced four bundles; all four passed `tools/validate_harness_evidence.py` with zero errors and warnings.
- Harness Lab wheel built with `--no-build-isolation --no-deps`; the restricted Cordis profile was present in the wheel.
- `git diff --check`, Python compilation, and JSON schema syntax checks passed.

The repository-wide validator still reports the same six missing historical
`reports/test_first_pilot/...` references and two cognition warnings present on
the baseline. This change does not claim to repair those unrelated historical
references. Pull-request CI remains the authoritative full-suite check.
