# Playbook Tools

These tools are deterministic helpers for cognition, integrity, and AI cost
telemetry. They do not require Obsidian, a vector database, or network access.

## Initialize a Project

```bash
python3 tools/init_playbook_project.py ../my-project \
  --mode lean-core \
  --project-name "My Project" \
  --operational-pain "Agents need a reproducible verification scaffold." \
  --current-workaround "Manual copying of playbook files." \
  --first-proof-metric "Generated project verification exits zero." \
  --verify-argv '["{python}", "-m", "pytest", "-q"]' \
  --install-claude-hooks
```

The initializer copies a proportional Lean-Core / Standard / Strict kit into a
downstream repository. It does not overwrite existing files unless `--force` is
passed. The initializer requires concrete `--operational-pain`,
`--current-workaround`, and `--first-proof-metric` values; `unknown`, `TBD`,
`TODO`, and empty values are blocked. Use `--install-claude-hooks` to safely
merge `.claude/settings.json`, copy hook scripts, set executable permissions,
and run a hook smoke test. A failed hook smoke test returns a non-zero exit.
Without that flag hooks are available but not claimed as active enforcement.
Project verification must be declared with one or more structured
`--verify-argv` JSON arrays; shell strings are not parsed into executable checks.
Use `--external-skill NAME` to create a trust-record stub before any third-party
skill is installed or enabled.

Planning Depth can be declared with `--planning-depth oneshot|compact_design|designed_slices`.
Use `--planning-depth recommend` with risk/profile flags such as
`--risk-level high`, `--user-visible-feature`, `--api-change`, or
`--persistence-change` to apply deterministic recommendation rules. Retrofit
use can add `--retrofit` to record `.playbook/repository_inventory.json` and
`docs/playbook_retrofit_plan.md` without rewriting application code.

## Plan Feature Design

```bash
python3 tools/feature_workflow.py --root . plan --task T14
python3 tools/feature_workflow.py --root . select-plan --task T14
python3 tools/feature_workflow.py --root . draft --task T14 --feature-id F01
python3 tools/feature_workflow.py --root . review --task T14 --feature-id F01 --role auto
python3 tools/feature_workflow.py --root . approve --feature-id F01
```

For the four Feature Workflow reviewer roles (`product_design_review`,
`program_design_review`, `slice_review`, `maintainability_review`), execute the
`suggested_command` written by `feature_workflow review`: it uses
`tools/run_codex_role.py run` as the governed default. Supply the model and
reasoning effort required by the target repository's review policy; do not
silently fall back to a hand-written direct `codex exec` when the runner fails.

Feature Design uses paired artifacts: `docs/design/F01.md` for human design and
`docs/design/F01.design.json` for deterministic metadata, approval provenance,
and slice registry. Approval is hash-bound and interactive; the tools never
self-approve a design.

## Render Slice Context

```bash
python3 tools/feature_workflow.py --root . next --feature-id F01
python3 tools/feature_workflow.py --root . start --task T14 --feature-id F01 --slice-id F01-S1
python3 tools/feature_workflow.py --root . context --task T14 --feature-id F01 --slice-id F01-S1
python3 tools/feature_workflow.py --root . check --task T14 --feature-id F01 --slice-id F01-S1
python3 tools/feature_workflow.py --root . accept-slice --task T14 --feature-id F01 --slice-id F01-S1
```

The slice packet is written under `.playbook-artifacts/context/` and includes
only the approved feature design, current slice, relevant brief/architecture
refs, allowed/forbidden files, verification commands, and manifest-selected
contract excerpts.

Use `--execution-profile audited_rounds` only for a long slice that needs
bounded Manage -> Execute -> Audit rounds. The default remains `direct_codex`;
the protocol is in `docs/audited_execution_protocol.md`.

## Check Maintainability Signals

```bash
python3 tools/check_maintainability.py --root . --task T01
```

This reports measurable advisory/stop-ship signals such as changed file count,
change-budget overflow, forbidden-file drift, and approved-slice scope drift. It
does not emit an aggregate maintainability score.

## Build a Manifest

```bash
python3 tools/cognition_index.py --root . --output generated/cognition/index.json
```

The manifest scans canonical markdown-oriented project surfaces, classifies artifact kinds, extracts headings and links, and records content hashes.

## Build a Context Packet

```bash
python3 tools/context_packet_builder.py \
  --manifest generated/cognition/index.json \
  --role reviewer \
  --scope "retrieval eval regression" \
  --output docs/context-packets/reviewer-retrieval-regression.md
```

Packets are generated markdown. They cite canonical source files and should stay bounded to the role and scope.

## Check Reference Integrity

```bash
python3 tools/integrity_check.py --root .
```

The checker is read-only. It verifies common playbook references such as
`Context-Refs`, `docs/EVIDENCE_INDEX.md` artifact paths, cognition manifest
paths, and generated context packet citations. Use `--strict-generated` when a
project intentionally commits generated packets and wants missing packet
references to fail CI.

## Roll Up AI Cost Telemetry

```bash
python3 tools/cost_rollup.py \
  --input docs/ai_cost_telemetry.jsonl \
  --output reports/ai_cost_rollup.md \
  --strict
```

The rollup reads provider-agnostic JSONL entries matching
`schemas/cost_telemetry_entry.schema.json`, then summarizes cost by run, task,
model, and agent role. Use `--max-total-cost`, `--max-run-cost`, and
`--require-file` when `docs/COST_BUDGET.md` declares enforceable thresholds.

## Check External Skill Security

```bash
python3 tools/skill_security_gate.py \
  --root . \
  --discover-agent-skills \
  --require-scanner \
  --sarif
```

The gate discovers skills under `.codex/skills`, `.claude/skills`, and
`skills`, requires `docs/security/skills/{skill-name}/TRUST_RECORD.md`, and
runs `skillspector scan` when skills are present. Repositories with no external
skills pass without requiring SkillSpector.

## Render Codex Exec Subagent Prompts

```bash
python3 tools/render_codex_exec_prompt.py \
  --root . \
  --task T03 \
  --role test_critic \
  --output-path docs/verification/T03_test_critic.md
```

The renderer builds task-scoped prompts for the optional Codex exec subagent
profile. It reads `docs/tasks.md`, `docs/REVIEW_POLICY.md`,
`.playbook/delivery_execution_model.json`, project verification config, review
reports, and copied role prompts. Use it when a main agent dispatches isolated
`codex exec` children for deep review, Test Critic, privacy review, scoped
fixes, or documentation sync. Review roles are read-only; write roles remain
task-scoped and never commit, push, or grant human approval.
