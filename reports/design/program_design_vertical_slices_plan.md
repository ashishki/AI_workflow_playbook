# Program Design And Vertical Slices Plan

Date: 2026-07-29
Base commit: 5583eca96c4d2d480b5574ed78bea63e0b07ebf0
Branch: master
Scope: AI Workflow Playbook planning-depth and vertical-slice governance layer

## 1. Current Playbook State

The Playbook is already governance-first, deterministic-first, and artifact-first.
The current brief-first flow is:

`PROJECT_BRIEF.md` intake -> human approval -> deterministic initializer -> mode
kit -> task execution -> verification -> risk-based review -> post-verification
release readiness resolver.

`Playbook Mode` already controls adoption overhead and evidence strictness:
`lean-core`, `standard`, and `strict`. Generated projects include
`.playbook/readiness_state.json`, `.playbook/delivery_execution_model.json`,
`.playbook/project_verification.json`, `docs/tasks.md`, task schema validation,
and a post-verification release resolver. Release readiness is intentionally not
a manual state flag.

The task model is a Markdown task block parsed by `tools/playbook_validate.py`
into the strict JSON contract `schemas/task.schema.json`. The parser already has
alias handling, duplicate alias errors, dependency graph validation, context ref
validation, and backward-compatible governance defaults.

The optional Codex exec subagent protocol already separates implementers,
reviewers, fix agents, documentation sync, and human completion authority.
Reviewer roles are read-only and output markers fail closed when required.

Harness Lab already treats runnable comparisons as mechanism demonstrations
unless empirical identity is explicitly required. `HarnessEvalUnit` compatibility
fingerprints and comparison semantics must not be weakened.

## 2. Existing Mechanisms To Reuse

- `templates/PROJECT_BRIEF.md` remains the intake artifact for problem, user,
  outcome, scope, proof metric, constraints, and risk.
- `docs/adoption_modes.md` remains the authority for Playbook Mode and
  proportional governance.
- `tools/init_playbook_project.py` remains the one deterministic copier/scaffolder
  for generated projects and retrofit use. It already preserves existing files
  unless `--force` is explicit.
- `tools/playbook_validate.py` remains the primary deterministic validator.
  Planning validation should extend it instead of introducing a second validator
  family.
- `schemas/task.schema.json` remains the task machine contract.
- `.playbook/readiness_state.json` remains the generated-project readiness state.
  It can be extended with `brief_ready` and `design_required` without making
  `release_ready` a manual state.
- `.playbook/delivery_execution_model.json` remains the authority boundary for
  implementer/reviewer/verifier/completion roles.
- `tools/render_codex_exec_prompt.py` remains the subagent prompt renderer.
- Existing project verification and release readiness contracts remain the only
  route to release readiness.
- Harness Lab companion package remains the runnable place for experiment
  mechanisms. Core Playbook validation must not require it for ordinary tasks.

## 3. Duplicates Or Overlaps Found

- `PROJECT_BRIEF.md` and `templates/ARCHITECTURE.md` already capture product
  fit, problem, risks, runtime, RAG, tool-use, and architecture-level choices.
  The new Feature Design must not duplicate that content. It should reference
  brief/architecture and focus on file tree, interfaces, call stack, invariants,
  failure paths, maintainability risks, and vertical slices.
- Existing "Planning" capability profile in `PLAYBOOK.md` describes application
  behavior where an LLM produces structured plans. It is not the same as
  development Planning Depth. Documentation must disambiguate these.
- Existing heavy-task mode adds evidence rigor for selected tasks. Planning
  Depth should decide how much design happens before implementation, not replace
  heavy-task evidence rules.
- Existing cognition context packets are generic role/scope excerpts. Slice
  context should be a smaller feature/slice packet driven by an instruction
  manifest, not a second cognition system.
- Existing deep review chain should not be run for every low-risk slice. New
  review roles should be targeted by planning depth/risk/slice checkpoint.

## 4. Authoritative Artifacts

- Intake/product authority: `templates/PROJECT_BRIEF.md` and generated
  `docs/PROJECT_BRIEF.md`.
- Mode authority: `docs/adoption_modes.md`.
- Architecture authority: `templates/ARCHITECTURE.md` and generated
  `docs/ARCHITECTURE.md`.
- Task authority: `templates/TASKS.md`, generated `docs/tasks.md`, and
  `schemas/task.schema.json`.
- Feature design authority: new `templates/FEATURE_DESIGN.md`, generated
  `docs/design/<feature-id>.md`, and companion
  `docs/design/<feature-id>.design.json`.
- Feature design machine contract: new `schemas/feature_design.schema.json`.
- Readiness authority: `.playbook/readiness_state.json` validated by
  `schemas/readiness_state.schema.json` and `tools/playbook_validate.py`.
- Delivery authority: `.playbook/delivery_execution_model.json`.
- Release authority: `tools/verify_project.py`,
  `.playbook-artifacts/project_verification.json`, and
  `tools/resolve_release_readiness.py`.
- Context-loading authority: new `templates/INSTRUCTION_MANIFEST.json` and
  `schemas/instruction_manifest.schema.json`.
- Harness extension authority: new changeability schemas and companion
  mechanism fixture; not a normal task gate.

## 5. Minimal Change Proposal

Introduce `Planning Depth` as an orthogonal project/task dimension:

- `oneshot`: no design document required.
- `compact_design`: approved feature design required before implementation.
- `designed_slices`: approved feature design plus vertical slice registry,
  slice task metadata, dependency checks, context packet, and review checkpoint.

Use a companion JSON design registry instead of parsing fenced JSON out of
Markdown. Decision:

`docs/design/F01.md` is the human-readable design. `docs/design/F01.design.json`
is the deterministic registry. This avoids LLM Markdown parsing, keeps validation
simple, and avoids serializing the whole design document twice.

Add deterministic tooling:

- `tools/planning_depth.py`: recommendation rules and CLI.
- `tools/feature_design_lib.py`: shared validation/path/approval helpers.
- `tools/create_feature_design.py`: create Markdown + companion JSON scaffold.
- `tools/validate_feature_design.py`: validate design registry and approval/slice
  rules.
- `tools/render_slice_context.py`: generate
  `.playbook-artifacts/context/<feature-id>/<slice-id>.md` from approved design,
  task, brief excerpts, manifest, and relevant refs.

Extend, not replace:

- `tools/playbook_validate.py --check design` validates active design/task
  coupling.
- `--check readiness` blocks `implementation_ready` when required design is
  missing/unapproved.
- `tools/init_playbook_project.py` writes planning depth metadata, optional design
  scaffold, and instruction manifest. It must not write application code.
- `tools/render_codex_exec_prompt.py` gains design/slice review roles and
  deterministic output markers.

## 6. Compatibility Risks

- Existing historical tasks lack new planning fields. Default them to
  `planning_depth=oneshot` with `planning_depth_source=legacy_default` without
  rewriting historical records.
- High-risk legacy active tasks should warn that a planning-depth migration may
  be needed, rather than fail old repositories immediately.
- Existing readiness schema contains `bootstrap_ready`; replacing it abruptly
  would invalidate older generated projects. Keep `bootstrap_ready` as a
  compatibility alias/state while documenting `brief_ready`.
- `release_ready` remains accepted only for compatibility, but release truth
  still comes from the resolver and exact-HEAD verification.
- `lean-core` must not receive required design artifacts unless planning depth
  explicitly requires them.
- New design checks must fail closed for explicit `compact_design` and
  `designed_slices`, but remain warnings for legacy/adoption-not-bumped projects.
- Path refs must reject absolute paths, `..`, and symlink escapes to avoid design
  refs pointing outside the repository.

## 7. Migration Strategy

- Schema/version note: `playbook.task.v1` remains the task schema. New fields are
  optional and backward-compatible.
- Legacy task default: missing `Planning-Depth` becomes `oneshot` with
  `planning_depth_source=legacy_default`.
- New generated projects write planning-depth-aware templates and
  `.playbook/readiness_state.json` metadata.
- Existing repositories can run initializer in retrofit mode without `--force`;
  existing `AGENTS.md`, repository inventory, and docs are skipped/preserved.
- Explicit adoption/version bump can turn planning warnings into errors by
  choosing `compact_design` or `designed_slices` in active tasks/readiness.
- Design approval must be human/authorized-reviewer provenance in companion JSON;
  `Approved-By: codex` or missing provenance fails.

## 8. Test Strategy

Unit tests:

- planning-depth parser/recommender and override semantics;
- task aliases, duplicate aliases, invalid values, and legacy defaults;
- feature design schema/status/approval rules;
- missing design, missing slice, duplicate slice IDs, cyclic dependencies;
- change budget parser;
- instruction manifest schema and path safety;
- slice context selection and forbidden artifact exclusion;
- Codex prompt roles/output markers and marker parser fail-closed behavior.

Integration tests:

- lean oneshot generated project: no design scaffold, implementation readiness
  allowed after brief/delivery/verification contracts.
- standard compact design: draft blocks implementation readiness; approved design
  allows it; missing design ref blocks.
- strict designed slices: design required, human approval required, missing or
  nonexistent slice blocks, forbidden files drift blocks, missing review marker
  blocks.
- retrofit: existing files are preserved, design proposal/scaffold is created,
  application code is not written.
- backward compatibility: old tasks remain valid; active high-risk legacy task
  produces migration warning.
- release safety: stale verification and fake/self approval still block release.

Verification after each slice will use focused pytest plus relevant
`playbook_validate` checks. Final verification will repeat full baseline commands,
with exact failures reported if frozen toolchain drift remains.

## 9. Files Expected To Change

- `templates/PROJECT_BRIEF.md`
- `templates/TASKS.md`
- `templates/FEATURE_DESIGN.md`
- `templates/INSTRUCTION_MANIFEST.json`
- `templates/READINESS_STATE.json`
- `templates/AGENTS.md`
- `templates/CODEX_PROMPT.md`
- `schemas/task.schema.json`
- `schemas/feature_design.schema.json`
- `schemas/instruction_manifest.schema.json`
- `schemas/readiness_state.schema.json`
- `schemas/changeability_suite.schema.json`
- `schemas/changeability_result.schema.json`
- `tools/playbook_validate.py`
- `tools/init_playbook_project.py`
- `tools/planning_depth.py`
- `tools/feature_design_lib.py`
- `tools/create_feature_design.py`
- `tools/validate_feature_design.py`
- `tools/render_slice_context.py`
- `tools/render_codex_exec_prompt.py`
- `docs/adr/ADR-002-feature-design-companion-json.md`
- `docs/codex_exec_subagent_protocol.md`
- `docs/adoption_modes.md`
- `docs/usage_guide.md`
- `docs/tasks.md`
- `docs/project_fit_guide.md`
- `PLAYBOOK.md`
- `README.md`
- `tools/README.md`
- Harness Lab companion docs/tools/tests under `companion/ai_workflow_harness_lab/`
- `tests/unit/` and `tests/integration/`
- `reports/implementation/PROGRAM_DESIGN_VERTICAL_SLICES_REPORT.md`

## 10. Files Not Expected To Change

- Existing release readiness resolver behavior in
  `tools/resolve_release_readiness.py`, except documentation references if
  needed.
- Existing RAG eval schemas and scorers.
- Existing HarnessEvalUnit compatibility fields.
- Existing task IDs in `docs/tasks.md`.
- Historical implementation reports.
- Runtime hooks.
- CI workflow unless new tests or schema checks require only minimal inclusion.
- Application/runtime code outside Playbook tools, schemas, docs, tests, and
  companion mechanism fixtures.

## 11. Slice Execution Plan

Slice 1 - Contracts:
planning depth enum, feature design schema/template, task schema fields,
parser/validator, tests.

Slice 2 - Brief And Readiness:
brief additions, planning recommendation, design-required readiness state,
approval semantics, tests.

Slice 3 - Slice Registry And Context:
vertical slice registry/dependencies, `render_slice_context`, instruction
manifest foundation, tests.

Slice 4 - Codex And Review:
new reviewer roles, output markers, design/slice review policy, tests.

Slice 5 - Initialization And Retrofit:
generated artifacts, preservation behavior, bootstrap/retrofit flow, integration
tests.

Slice 6 - Changeability Harness:
schemas, synthetic mechanism fixture, basic runner/comparator, maturity docs.

Slice 7 - Documentation And Final Verification:
README/usage/adoption/playbook/tool docs, exact-HEAD report, final verification.
