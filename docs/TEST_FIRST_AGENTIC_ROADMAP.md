# Test-First Agentic SWE Roadmap

Status: proposed implementation roadmap
Source: `deep-research-report(1).md`
Created: 2026-07-13

## Purpose

This roadmap turns the deep-research recommendations into an executable task
plan for evolving AI Workflow Playbook toward a stricter test-first agentic SWE
method.

The goal is not to turn the Playbook into a runtime or orchestration server.
The goal is to add a stronger, artifact-first test governance layer:

- implementers work from public executable specs where risk justifies it
- task metadata carries risk and test-governance decisions
- deterministic gates remain the primary source of truth
- critics audit evidence and oracle gaps, not vibes
- hidden, mutation/property, and UI visual checks are used only where they pay
  for their operational cost

## Current Baseline

Already present in this repository:

- governance-first Playbook docs, prompts, phase gates, hooks, and adoption
  modes
- task schema and deterministic task validation
- command receipts, failure records, run results, harness eval units, and
  EvidenceBundle schemas
- `tools/receipt_run.py`, `tools/validate_harness_evidence.py`,
  `tools/playbook_validate.py`, and `tools/verify_playbook.py`
- companion harness lab with baseline-vs-Playbook evaluation mechanics
- existing planned task `AWP-EL-002: Diverse Review Principle`

Main gaps identified by the research report:

- test-first discipline is not yet a first-class implementer protocol
- task schema does not encode risk/test governance fields
- no dedicated independent Test Critic prompt exists
- holdout acceptance, mutation/property gates, UI visual proof, and critic
  calibration are not first-class Playbook layers
- merge/phase completion authority is implied across existing docs, but there
  is no focused policy that maps evidence to stop-ship decisions

## Implementation Rules For The Next Agent Session

Use this file as the backlog, not as permission to do everything at once.

Before starting a task:

1. Read `docs/tasks.md`, `docs/PROJECT_PLAN.md`, `deep-research-report(1).md`,
   and this roadmap.
2. Run `python3 tools/playbook_validate.py --root . --check tasks`.
3. Keep changes scoped to the selected roadmap task and its direct integration
   points.
4. Do not add a required server, database, UI, or always-on agent runtime.
5. Preserve Lean / Standard / Strict proportionality.
6. Treat new critic prompts as advisory/evidence-auditing layers unless a task
   explicitly wires them to deterministic gates.

Verification environment: activate the repository `.venv` before running the
listed `python3` commands. In this workspace the system interpreter does not
provide pytest; `python3` in the commands below means the interpreter selected
by the activated project environment. `.venv/bin/python` is the equivalent
explicit form.

After each task:

1. Run the task's verification commands.
2. Run `python3 tools/verify_playbook.py --root .` unless the task explicitly
   explains why a narrower check is enough.
3. Update `docs/tasks.md` only when the implementation task itself is complete
   and verified.

## Phase TFA-0 - Baseline And Backlog Wiring

Objective: add this workstream to the canonical task graph without pretending
the new method is already implemented.

### TFA-0.1: Add Test-First Workstream To `docs/tasks.md`

Owner: codex
Type: docs roadmap
Risk: low
Dependencies: none

Objective:
  Add planned task blocks for the phases in this roadmap to `docs/tasks.md`,
  using the existing task-block style and validator-compatible fields.

Files:
  - `docs/tasks.md`
  - `docs/PROJECT_PLAN.md`

Implementation notes:
  - Add a new phase after the current Evidence Layer / Diverse Review work.
  - Keep this roadmap as the detailed source; `docs/tasks.md` should contain
    concise canonical task records.
  - Update `docs/PROJECT_PLAN.md` near-term roadmap to mention test-first
    evolution as a P1/P2 governance enhancement.

Acceptance criteria:
  - `docs/tasks.md` contains planned tasks for TDD protocol, task schema
    fields, Test Critic, evidence-to-gate mapping, holdout tests,
    mutation/property guidance, UI verification, critic calibration, and merge
    authority.
  - Every new task has owner, phase, type, status, objective, acceptance
    criteria, integration points, and verification.
  - No task claims implemented status.

Verification:
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - `python3 tools/integrity_check.py --root .`

## Phase TFA-1 - First-Class Test-First Protocol

Objective: make the implementer loop explicit before adding heavier gates.

### TFA-1.1: Add Test-First Protocol Document

Owner: codex
Type: docs protocol
Risk: medium
Dependencies: TFA-0.1

Objective:
  Create the canonical Playbook protocol for public executable specs,
  RED-GREEN-REFACTOR-style implementation, bounded repair, and evidence
  capture.

Files:
  - `docs/testing/test_first_protocol.md`
  - `PLAYBOOK.md`
  - `README.md`
  - `docs/usage_guide.md`

Implementation notes:
  - Keep it risk-tiered. Low-risk docs/config work should not require full TDD.
  - Define what counts as an executable spec: unit tests, integration tests,
    property checks, contract tests, fixtures, CLI smoke checks, or UI behavior
    tests.
  - Require failing public tests before implementation only when semantics are
    being added or changed and the risk tier justifies it.
  - State that public tests are inner-loop specs, not final proof.

Acceptance criteria:
  - The protocol defines when test-first is required, optional, or not
    applicable.
  - The protocol maps Lean / Standard / Strict adoption modes to minimum test
    expectations.
  - The protocol references receipts and runtime verification as evidence.
  - README/PLAYBOOK mention the protocol without claiming empirical improvement
    before TFA-7 pilot evidence exists.

Verification:
  - `python3 tools/playbook_validate.py --root . --check placeholders`
  - `python3 tools/integrity_check.py --root .`
  - `python3 tools/verify_playbook.py --root .`

### TFA-1.2: Add Implementer TDD Prompt

Owner: codex
Type: prompt
Risk: medium
Dependencies: TFA-1.1

Objective:
  Add a focused implementer prompt for test-first agentic SWE tasks.

Files:
  - `prompts/IMPLEMENTER_TDD.md`
  - `templates/CODEX_PROMPT.md`
  - `prompts/ORCHESTRATOR.md`

Implementation notes:
  - The prompt should tell the implementer to inspect existing tests first,
    add or update public tests before implementation when required, run the
    smallest useful test, then broaden verification.
  - The prompt must forbid declaring completion from prose-only evidence.
  - The prompt should include escalation rules for missing requirements,
    impossible tests, flaky tests, and bounded correction exhaustion.
  - Do not instruct active Codex Direct sessions to spawn nested Codex.

Acceptance criteria:
  - `prompts/IMPLEMENTER_TDD.md` exists and is usable as a direct prompt.
  - Orchestrator/template docs point to it when task metadata requires
    test-first implementation.
  - The prompt asks for command receipts or exact verification output paths
    where available.

Verification:
  - `python3 tools/playbook_validate.py --root . --check placeholders`
  - `python3 tools/integrity_check.py --root .`
  - `python3 tools/verify_playbook.py --root .`

## Phase TFA-2 - Task Metadata And Deterministic Routing

Objective: let validators and orchestrators route test governance without
ad hoc LLM judgement.

### TFA-2.1: Extend Task Schema With Test Governance Fields

Owner: codex
Type: schema tooling
Risk: high
Dependencies: TFA-1.1

Objective:
  Extend the task contract with explicit fields for risk and test-governance
  requirements.

Files:
  - `schemas/task.schema.json`
  - `tools/playbook_validate.py`
  - `templates/TASKS.md`
  - `docs/tasks.md`
  - `tests/unit/test_playbook_validate.py`

Suggested fields:
  - `risk_level`: `low | medium | high | critical`
  - `public_tests_required`: `not_required | conditional | required`
  - `critic_required`: `not_required | conditional | required`
  - `holdout_required`: `not_required | conditional | required`
  - `mutation_required`: `not_required | conditional | required`
  - `property_required`: `not_required | conditional | required`
  - `visual_contract`: `not_applicable | optional | required`

Implementation notes:
  - Preserve compatibility with existing task blocks by giving conservative
    defaults in the parser.
  - Avoid making all historical tasks invalid.
  - Add validator coverage for the new fields and aliases.
  - If field names change during implementation, update this roadmap or record
    the decision in a nearby note.

Acceptance criteria:
  - Schema validates task records with the new fields.
  - Parser accepts equivalent markdown field names such as `Risk-Level` and
    `Public-Tests-Required`.
  - Existing `docs/tasks.md` remains valid.
  - Template tasks show the new fields without making Lean tasks heavy by
    default.

Verification:
  - `python3 -m pytest tests/unit/test_playbook_validate.py -q`
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - `python3 tools/verify_playbook.py --root .`

### TFA-2.2: Add Risk-Tier Routing Rules

Owner: codex
Type: docs prompt
Risk: medium
Dependencies: TFA-2.1

Objective:
  Document how task risk and metadata choose deterministic checks, critic
  review, holdout gates, mutation/property checks, and UI visual evidence.

Files:
  - `docs/testing/test_first_protocol.md`
  - `prompts/ORCHESTRATOR.md`
  - `prompts/PHASE1_VALIDATOR.md`
  - `prompts/audit/PROMPT_3_CONSOLIDATED.md`

Implementation notes:
  - Keep the default cheap for low-risk tasks.
  - Make high/critical tasks require evidence mapping and human approval.
  - Cross-vendor review should be optional for high-risk work, not a default
    requirement.

Acceptance criteria:
  - The routing table defines minimum gates by risk tier.
  - Orchestrator and consolidated review prompts check the new fields.
  - Phase 1 validation warns about missing project verification baselines.

Verification:
  - `python3 tools/playbook_validate.py --root . --check placeholders`
  - `python3 tools/integrity_check.py --root .`
  - `python3 tools/verify_playbook.py --root .`

## Phase TFA-3 - Independent Test Critic

Objective: add a structured critic that audits tests and evidence rather than
acting as an uncalibrated final judge.

### TFA-3.1: Add Test Critic Prompt

Owner: codex
Type: prompt review
Risk: medium
Dependencies: TFA-1.1, TFA-2.1

Objective:
  Create an independent Test Critic prompt focused on oracle gaps, missing
  cases, overfitting to public tests, flaky signals, and evidence mapping.

Files:
  - `prompts/audit/PROMPT_TEST_CRITIC.md`
  - `prompts/audit/AUDIT_INDEX.md`
  - `prompts/audit/PROMPT_3_CONSOLIDATED.md`
  - `docs/testing/test_first_protocol.md`

Implementation notes:
  - The critic should receive task metadata, diff summary, public test results,
    receipts, and relevant acceptance criteria.
  - The critic should output structured findings: blocker, concern, accepted
    risk, or no finding.
  - The critic may block only by pointing to deterministic failures, missing
    required evidence, or explicit stop-ship policy.

Acceptance criteria:
  - Prompt has clear inputs, outputs, severity taxonomy, and anti-patterns.
  - It explicitly avoids style-only rewrites and broad architecture review.
  - Consolidated review can consume its findings.

Verification:
  - `python3 tools/playbook_validate.py --root . --check placeholders`
  - `python3 tools/integrity_check.py --root .`
  - `python3 tools/verify_playbook.py --root .`

### TFA-3.2: Add Test Critic Report Template

Owner: codex
Type: template
Risk: low
Dependencies: TFA-3.1

Objective:
  Add a reusable report artifact for Test Critic outputs.

Files:
  - `templates/TEST_CRITIC_REPORT.md`
  - `templates/EVIDENCE_INDEX.md`

Acceptance criteria:
  - Template maps acceptance criteria to public tests, hidden/holdout tests
    where applicable, receipts, and unresolved oracle gaps.
  - Template records false-alarm and miss candidates for later calibration.
  - Evidence index can link to critic reports without making them required for
    every Lean task.

Verification:
  - `python3 tools/playbook_validate.py --root . --check placeholders`
  - `python3 tools/integrity_check.py --root .`

## Phase TFA-4 - Stronger Acceptance Oracles

Objective: add optional-but-first-class guidance for hidden, property, and
mutation checks on high-value code paths.

### TFA-4.1: Add Holdout Acceptance Protocol

Owner: codex
Type: docs evaluation
Risk: high
Dependencies: TFA-2.1, TFA-3.1

Objective:
  Define how projects maintain hidden or restricted acceptance tests for merge
  and phase gates without leaking them into implementer prompts.

Files:
  - `docs/testing/holdout_acceptance.md`
  - `docs/evaluation/CI_EVAL_GATE.md`
  - `docs/agent_harness/HARNESS_EVALUATION_PROTOCOL.md`
  - `companion/ai_workflow_harness_lab/README.md`

Implementation notes:
  - Keep this as a protocol and template. Do not add secret test contents to
    this public repository.
  - Distinguish public tests for inner-loop implementation from holdout tests
    for phase/merge confidence.
  - Include contamination controls: do not paste holdout cases into agent
    prompts, and do not expose expected outputs unnecessarily.

Acceptance criteria:
  - Protocol defines when holdouts are required, optional, and not applicable.
  - Protocol explains storage, access, rotation, receipts, and failure handling.
  - Harness docs explain how project-specific suites can model holdout checks.

Verification:
  - `python3 tools/playbook_validate.py --root . --check placeholders`
  - `python3 tools/integrity_check.py --root .`
  - `python3 tools/verify_playbook.py --root .`

### TFA-4.2: Add Mutation And Property Oracle Guidance

Owner: codex
Type: docs evaluation
Risk: medium
Dependencies: TFA-2.1

Objective:
  Add stack-neutral guidance for when to use property-based and mutation
  testing as stronger oracle-quality checks.

Files:
  - `docs/testing/property_and_mutation_oracles.md`
  - `templates/RETRIEVAL_EVAL_PLAN.md`
  - `templates/ROUTER_EVAL.md`
  - `docs/testing/test_first_protocol.md`

Implementation notes:
  - Keep the guidance stack-neutral but give examples: Hypothesis for Python,
    Stryker for JS/TS, Mutmut for Python, jq/JSON schema checks for data
    contracts.
  - Require these checks only for critical algorithms, state transitions,
    security/compliance-sensitive behavior, model routing, retrieval semantics,
    and agent termination/retry logic.
  - Explain that line coverage is not a sufficient oracle.

Acceptance criteria:
  - Guidance includes a decision tree for public tests vs property checks vs
    mutation checks.
  - It defines minimum evidence: command, config, threshold or rationale,
    receipt, and risk acceptance for skipped checks.
  - Existing eval templates reference stronger oracle checks where relevant.

Verification:
  - `python3 tools/playbook_validate.py --root . --check placeholders`
  - `python3 tools/integrity_check.py --root .`
  - `python3 tools/verify_playbook.py --root .`

## Phase TFA-5 - UI Evidence Protocol

Objective: make frontend verification explicit without relying only on DOM tests
or a vision-language critic.

### TFA-5.1: Add UI Verification Protocol

Owner: codex
Type: docs frontend
Risk: medium
Dependencies: TFA-2.1

Objective:
  Define the Playbook UI evidence stack: behavior tests, visual regression
  baselines, human visual review, and optional vision critic.

Files:
  - `docs/testing/ui_verification.md`
  - `templates/RUNTIME_VERIFICATION_RECORD.md`
  - `templates/IMPLEMENTATION_CONTRACT.md`
  - `prompts/audit/PROMPT_2_CODE.md`

Implementation notes:
  - Put Playwright screenshot baselines, Percy, and Chromatic in examples, not
    mandatory core dependencies.
  - Require stable viewport lists, dynamic-content masking/styling, and clear
    baseline-update rules.
  - Vision critic should be framed as a third layer for hard-to-formalize visual
    fidelity, not as a replacement for screenshot diffs.

Acceptance criteria:
  - Protocol defines required UI evidence by risk tier.
  - Runtime verification template can record screenshots, visual diffs, browser
    console output, and viewport coverage.
  - Code review prompt checks for behavior-vs-visual coverage gaps.

Verification:
  - `python3 tools/playbook_validate.py --root . --check placeholders`
  - `python3 tools/integrity_check.py --root .`
  - `python3 tools/verify_playbook.py --root .`

## Phase TFA-6 - Completion Authority And Critic Calibration

Objective: make final readiness depend on evidence and calibrated review, not
agent confidence.

### TFA-6.1: Add Merge Authority Policy

Owner: codex
Type: docs governance
Risk: high
Dependencies: TFA-2.2, TFA-3.1

Objective:
  Define who or what can mark a task, phase, or merge ready under different
  risk levels.

Files:
  - `docs/merge_authority.md`
  - `PLAYBOOK.md`
  - `prompts/ORCHESTRATOR.md`
  - `prompts/audit/PROMPT_3_CONSOLIDATED.md`

Implementation notes:
  - Completion authority should be human approval after deterministic gates for
    most cases.
  - Critic findings are advisory unless they cite deterministic failure,
    missing required evidence, explicit stop-ship conditions, or calibrated
    high-risk policy.
  - Define stop-ship rules for missing receipts, failed required tests, hidden
    gate failure, security/compliance risk, and unaudited baseline updates.

Acceptance criteria:
  - Policy maps risk levels to required evidence and approval authority.
  - Policy clearly states that an implementer cannot self-certify completion
    from prose.
  - Orchestrator and consolidated review prompts enforce the policy.

Verification:
  - `python3 tools/playbook_validate.py --root . --check placeholders`
  - `python3 tools/integrity_check.py --root .`
  - `python3 tools/verify_playbook.py --root .`

### TFA-6.2: Add Critic Calibration Protocol

Owner: codex
Type: docs evaluation
Risk: medium
Dependencies: TFA-3.1, TFA-6.1

Objective:
  Define how Test Critic and final critic performance should be measured on
  seeded defects and known-good changes.

Files:
  - `docs/evaluation/CRITIC_CALIBRATION.md`
  - `templates/TEST_CRITIC_REPORT.md`
  - `companion/ai_workflow_harness_lab/README.md`

Implementation notes:
  - Track false alarms, misses, severity accuracy, evidence-link accuracy, and
    repair usefulness.
  - Do not optimize for "more blocks"; optimize for calibrated precision and
    recall on the selected risk tier.
  - Include a small seeded-defect-bank structure but do not invent benchmark
    claims before pilots run.

Acceptance criteria:
  - Calibration protocol defines dataset shape, metrics, run cadence, and
    decision thresholds.
  - Test Critic template captures enough metadata to feed calibration.
  - Harness docs explain how a project-specific suite can include seeded
    defects.

Verification:
  - `python3 tools/playbook_validate.py --root . --check placeholders`
  - `python3 tools/integrity_check.py --root .`
  - `python3 tools/verify_playbook.py --root .`

## Phase TFA-7 - Empirical Pilot

Objective: verify that the new method improves project outcomes rather than
only adding ceremony.

### TFA-7.1: Add Paired Pilot Plan

Owner: codex
Type: evaluation
Risk: high
Dependencies: TFA-1 through TFA-6

Objective:
  Define a paired experiment comparing the current Playbook workflow against
  the test-first workflow in one or two real repositories.

Files:
  - `docs/evaluation/TEST_FIRST_PILOT_PLAN.md`
  - `docs/evaluation/PLAYBOOK_EMPIRICAL_VALIDATION.md`
  - `companion/ai_workflow_harness_lab/README.md`

Metrics:
  - public test pass rate
  - holdout pass rate
  - mutation score on selected critical modules
  - property-check failures caught before merge
  - critic false-alarm rate
  - critic miss rate on seeded defects
  - average repair turns
  - time-to-green
  - rollback/reopen rate after merge
  - UI behavior pass rate and visual defects caught pre-merge, where applicable

Acceptance criteria:
  - Pilot plan names required project fixtures and minimum trial counts.
  - Plan separates mechanism validation from claims about real productivity or
    quality improvement.
  - Plan includes budget, data retention, and human approval boundaries.
  - No README/marketing claim says the new method is empirically better until
    pilot results exist.

Verification:
  - `python3 tools/playbook_validate.py --root . --check placeholders`
  - `python3 tools/integrity_check.py --root .`
  - `python3 tools/verify_playbook.py --root .`

### TFA-7.2: Run And Record Pilot Results

Owner: human + codex
Type: evaluation evidence
Risk: high
Dependencies: TFA-7.1

Objective:
  Execute the paired pilot and record results as evidence, not narrative.

Files:
  - `reports/test_first_pilot/`
  - `docs/evaluation/TEST_FIRST_PILOT_RESULTS.md`
  - `docs/tasks.md`

Acceptance criteria:
  - Pilot runs produce command receipts, harness bundles, or equivalent
    evidence artifacts.
  - Results include both wins and failures.
  - Adoption decision is recorded: default, Strict-only, optional, or rejected.
  - Follow-up tasks are created for gaps discovered during the pilot.

Verification:
  - project-specific pilot commands from `TEST_FIRST_PILOT_PLAN.md`
  - `python3 tools/validate_harness_evidence.py --bundle <bundle>`
  - `python3 tools/verify_playbook.py --root .`

## Suggested Execution Order

1. TFA-0.1
2. TFA-1.1
3. TFA-1.2
4. TFA-2.1
5. TFA-2.2
6. TFA-3.1
7. TFA-3.2
8. TFA-6.1
9. TFA-4.1
10. TFA-4.2
11. TFA-5.1
12. TFA-6.2
13. TFA-7.1
14. TFA-7.2

Reasoning:
  First add the cheap loop and metadata. Then add critic and completion policy.
  Only after that add heavier holdout, mutation/property, UI, and calibration
  layers. The pilot comes last because it should measure a coherent workflow,
  not isolated docs.

## First Prompt For A New Agent Session

Use this prompt to begin implementation in a fresh session:

```text
You are working in the AI Workflow Playbook repository.

Goal: implement the next task from `docs/TEST_FIRST_AGENTIC_ROADMAP.md`.

Start with TFA-0.1 unless it is already complete and verified.

Read:
- `docs/TEST_FIRST_AGENTIC_ROADMAP.md`
- `deep-research-report(1).md`
- `docs/tasks.md`
- `docs/PROJECT_PLAN.md`
- `schemas/task.schema.json`
- `tools/playbook_validate.py`

Constraints:
- Do not add a required runtime, server, database, or UI.
- Keep Lean / Standard / Strict proportionality.
- Do not mark research recommendations as empirically proven until pilot
  evidence exists.
- Make narrow, validator-compatible changes.

Before editing, report the exact task you selected and the files you will
touch.

After editing, run the verification commands listed in the selected task and
summarize results with file links.
```
