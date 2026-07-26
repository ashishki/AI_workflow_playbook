# Implementation Journal

Status: append-only framework implementation notes

## 2026-07-26 - RAG Evaluation v2 Baseline

Task: RAG Evaluation v2: harness-aware, topology-aware, perturbation-aware evaluation
Branch: `feat/rag-eval-v2`
Base commit: `ee487b2d2c83301933aff8a8b5ecb78050623346`

Baseline commands before edits:

| Command | Exit code | Result |
|---------|-----------|--------|
| `python -m pytest -q` | 127 | Pre-existing environment issue: `/bin/bash: line 1: python: command not found` |
| `python tools/playbook_validate.py --root .` | 127 | Pre-existing environment issue: `/bin/bash: line 1: python: command not found` |
| `python tools/verify_playbook.py --root .` | 127 | Pre-existing environment issue: `/bin/bash: line 1: python: command not found` |
| `git status --short` | 0 | Clean before edits |
| `git rev-parse HEAD` | 0 | `ee487b2d2c83301933aff8a8b5ecb78050623346` |

Additional local-venv baseline, used only to classify repository behavior because `python` is absent:

| Command | Exit code | Result |
|---------|-----------|--------|
| `.venv/bin/python --version` | 0 | `Python 3.12.3` |
| `.venv/bin/python -m pytest -q` | 1 | 135 passed, 2 failed; failures are pre-existing frozen Codex/toolchain drift in `tests/unit/test_test_first_pilot_permissions.py` and `tests/unit/test_test_first_pilot_toolchain.py` |
| `.venv/bin/python tools/playbook_validate.py --root .` | 0 | `errors=0 warnings=2`; warnings are pre-existing missing cognition refs |
| `.venv/bin/python tools/verify_playbook.py --root .` | 1 | `required_failures=1`; failure is the same pre-existing pytest toolchain drift |

Classification: the baseline is not fully green before RAG Eval v2. The scoped RAG implementation will not repair frozen Codex/toolchain drift unless it becomes a direct blocker for RAG contracts.

## 2026-07-26 - RAG Evaluation v2 Scoped Verification

Scope: RAG Evaluation v2 contracts, tools, initializer integration, generated
project matrix, docs/prompts/templates, and offline example.

Pre-commit verification commands:

| Command | Exit code | Result |
|---------|-----------|--------|
| `.venv/bin/python -m pytest tests/unit/test_rag_eval_tools.py tests/unit/test_playbook_validate.py tests/integration/test_initializer.py -q` | 0 | 53 passed |
| `.venv/bin/python tools/playbook_validate.py --root . --check rag` | 0 | `errors=0 warnings=0` |
| `.venv/bin/python tools/playbook_validate.py --root .` | 0 | `errors=0 warnings=2`; warnings are pre-existing cognition reference gaps |
| `.venv/bin/python -m py_compile tools/init_playbook_project.py tools/playbook_validate.py tools/verify_playbook.py tools/rag_eval_lib.py tools/rag_eval_validate.py tools/rag_eval_score.py tools/rag_eval_compare.py` | 0 | Compile pass |
| `.venv/bin/python tools/build_test_first_pilot_manifest.py --check` | 0 | Frozen asset manifest pass after adding RAG schemas/tools/tests |
| `.venv/bin/python -m pytest -q` | 1 | 162 passed, 2 failed; remaining failures are pre-existing frozen Codex/toolchain drift |
| `.venv/bin/python tools/verify_playbook.py --root .` | 1 | `required_failures=1`; verifier RAG checks pass, pytest fails for the same pre-existing drift |

Example commands:

| Command | Exit code | Result |
|---------|-----------|--------|
| `.venv/bin/python tools/rag_eval_score.py --root . --manifest examples/rag_eval/minimal/manifest.json --observations examples/rag_eval/minimal/baseline_observations.jsonl --condition lexical_baseline --json examples/rag_eval/minimal/baseline_result.json --report examples/rag_eval/minimal/baseline_result.md` | 0 | baseline result `pass` |
| `.venv/bin/python tools/rag_eval_score.py --root . --manifest examples/rag_eval/minimal/manifest.json --observations examples/rag_eval/minimal/candidate_observations.jsonl --condition production_candidate --json examples/rag_eval/minimal/candidate_result.json --report examples/rag_eval/minimal/candidate_result.md` | 0 | candidate result `pass` |
| `.venv/bin/python tools/rag_eval_compare.py --root . --baseline examples/rag_eval/minimal/baseline_result.json --candidate examples/rag_eval/minimal/candidate_result.json --manifest examples/rag_eval/minimal/manifest.json --json examples/rag_eval/minimal/comparison.json --report examples/rag_eval/minimal/comparison.md` | 0 | comparison result `pass` |

Maturity: machine-readable RAG eval contracts and offline
scoring/comparison are tested for mechanism. No claim is made that these
fixtures improve a particular production RAG system without project-specific
empirical evidence.
