# Test-First Pilot Preflight - Not Run

Date: 2026-07-13
Environment: repository workspace, Asia/Tbilisi
Record type: local mechanism-evidence preflight only
Real-model/network execution: not attempted

## Outcome

The project-specific paired pilot was not runnable. No approved project suite,
real fixture, budget, external runner approval, model registry, protected
evidence setup, or project scorer was available. This record does not satisfy a
pilot trial or adoption gate.

## Commands Executed

### Generic Suite Structure

```bash
.venv/bin/harness-lab validate-suite companion/ai_workflow_harness_lab/suites/playbook_core_v1
```

Exit: 0. Observed suite ID `playbook_core_v1`, version `1.0.0`, tasks 5.

### Existing Bundle Integrity

```bash
find reports/playbook_eval -name bundle.json -print0 | sort -z | \
  xargs -0 -n1 .venv/bin/harness-lab verify-bundle
```

Exit: 0. Ten existing bundles returned `verify-bundle: ok`.

```bash
find reports/playbook_eval -name bundle.json -print0 | sort -z | \
  xargs -0 -n1 python3 tools/validate_harness_evidence.py
```

Exit: 0. Ten existing bundles returned zero errors and zero warnings. Receipt
counts by sorted bundle were `0, 4, 0, 0, 0, 0, 2, 1, 0, 0`.

The preflight used the positional bundle path. The validator also supports the
roadmap-compatible `--bundle PATH` alias; that compatibility was added after the
initial preflight audit and is covered by a focused unit test. Both forms select
the same validation path and neither changes the evidence verdict.

### Artifact Digests And Installed Commands

```bash
sha256sum companion/ai_workflow_harness_lab/suites/playbook_core_v1/suite.json \
  reports/playbook_eval/comparison/comparison_report.json
command -v codex
command -v .venv/bin/harness-lab
```

Exit: 0.

| Artifact/command | Observed value |
|------------------|----------------|
| Generic suite manifest SHA-256 | `4c7b8de8b6bc4487a1c7e742719c1e7ab05006cf9eca9e031c888c313f127ecc` |
| Mechanism comparison SHA-256 | `8fdfb86e7f16960dfe854413889f9c33466ce26575450e5f5e1ce9dc10e2bb1a` |
| Codex executable | `/home/ashishki/.nvm/versions/node/v22.22.1/bin/codex` |
| Harness executable | `.venv/bin/harness-lab` |

## Evidence Boundary

The checked artifacts predate this pilot and use the scripted adapter. There is
one trial per condition/task and the comparison contains
`single_run_stability_warning: true`. They verify only that the local evidence
format and validation mechanism work. No files under `reports/playbook_eval/`
were rerun, overwritten, or copied into a pilot comparison set.

Valid real-project pilot runs: 0.
Empirical claims supported: none.
