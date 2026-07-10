# Current State Implementation Map

Generated from local `HEAD` before tracked implementation changes.

## Existing Validators And Consumers

- `tools/integrity_check.py`: checks selected backtick references and `docs/tasks.md` `Context-Refs`; consumed by `.github/workflows/playbook-checks.yml` and generated project templates.
- `tools/skill_security_gate.py`: validates external skill trust records and optional SkillSpector output; consumed by root workflow and initializer output.
- `tools/cost_rollup.py`: rolls up provider-neutral cost telemetry JSONL; consumed by smoke workflow only.
- `python -m py_compile tools/*.py`: root workflow compiles helpers.
- No canonical `verify_playbook.py` existed.
- No deterministic task block parser or task schema validator existed.
- No evidence bundle validator existed.

## Existing Schemas

- `schemas/cost_telemetry_entry.schema.json`
- `schemas/context_packet.schema.json`
- `schemas/cognition_frontmatter.schema.json`
- `schemas/retrieval_manifest.schema.json`

Missing authoritative schemas at baseline:

- `schemas/task.schema.json`
- `schemas/command_receipt.schema.json`
- `schemas/failure_record.schema.json`
- `schemas/run_result.schema.json`
- `schemas/evidence_bundle.schema.json`
- `schemas/harness_eval_unit.schema.json`

## Existing Tests

- `tests/` and `src/eval_ground_truth_lab/` directories exist but contain no tracked test files.
- Baseline system `python3 -m pytest -q` failed because pytest was unavailable.
- Baseline venv replay found zero tests and exited 5.

## Existing Hooks And Installation

- Hook scripts exist under `hooks/`: `guard_files.sh`, `guard_phase_boundary.sh`, `enforce_codex_exec.sh`, `log_bash.sh`, `save_checkpoint.sh`.
- `templates/.claude/settings.json` references those hooks.
- `tools/init_playbook_project.py` copies hooks for Standard/Strict but has no safe `.claude/settings.json` merge path and no `--install-claude-hooks` smoke test.

## Existing CI

- `.github/workflows/playbook-checks.yml` compiles tools, validates JSON, smoke-tests initializer, runs skill gate, cost rollup, and integrity check.
- It does not run `pytest` or a canonical verification command.
- `ci/ci.yml` is a generated project template with large commented examples and an active SkillSpector-required step that may fail generated projects without scanner setup.

## Existing Harness/Eval Documents

- `docs/agent_harness/AGENT_HARNESS_DESIGN.md`: harness boundary.
- `docs/agent_harness/HARNESS_EVAL_PLAN.md`: harness evaluation plan.
- `templates/HARNESS_BENCHMARK_CARD.md`: manually filled comparison card.
- `examples/harness/*`: example cards.

Confirmed duplication: design and eval plan overlap as normative harness protocol documents, but no runnable consumer exists.

## Current Initializer Output

- Lean: common files plus `docs/CONTRACT_LITE.md`, `AGENTS.md`, and `docs/LEAN_REVIEW_CHECKLIST.md`.
- Standard: common files plus full playbook docs, prompts, hooks, and CI template.
- Strict: Standard plus cost architecture flag.

Lean is lighter than Standard, but no explicit `Lean-Core` mode exists and common output still includes cost/security docs that are advanced for the minimal path.

## Confirmed Gaps To Fix

- README overstates “hard guarantees” for prompt-only or hook-available controls.
- Task schema is documented but not machine-enforced.
- `docs/tasks.md` is a framework task graph and does not conform to a single enforced contract.
- Runtime verification template allows manual `status: passed`.
- Phase boundary hook validates marker presence, not independent review substance.
- Capability/harness eval is documented, not executable.
- Hooks are available but not safely installed by initializer flag.
- Root CI does not run pytest or canonical verification.
- No independent command receipt or evidence bundle validation.
- No reproducible baseline-vs-Playbook mechanism.

## Planned File Changes

ADD:

- Root validation, receipt, evidence, and verification tools.
- Root tests under `tests/unit`, `tests/integration`, `tests/hooks`, and `tests/fixtures`.
- Evidence and task schemas under `schemas/`.
- Companion package under `companion/ai_workflow_harness_lab/`.
- Empirical validation documentation and generated scripted demonstration report.

MODIFY:

- `README.md`
- `docs/architecture_layers.md`
- `docs/tasks.md`
- `templates/TASKS.md`
- `templates/RUNTIME_VERIFICATION_RECORD.md`
- `templates/HARNESS_BENCHMARK_CARD.md`
- `tools/init_playbook_project.py`
- `.github/workflows/playbook-checks.yml`
- `ci/ci.yml`

MERGE:

- `docs/agent_harness/AGENT_HARNESS_DESIGN.md`
- `docs/agent_harness/HARNESS_EVAL_PLAN.md`

DELETE:

- Remove duplicate normative harness protocol documents after migration, or replace them with short redirect notes if references require compatibility.

KEEP:

- Existing governance docs, prompts, hooks, and optional cost/security tooling unless an executable consumer supersedes a duplicated rule.
