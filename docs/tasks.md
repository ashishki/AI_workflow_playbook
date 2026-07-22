# AI Workflow Playbook Tasks

Status: active core framework task graph
Last updated: 2026-07-22

This file tracks framework work for the playbook itself. It is separate from
project adoption tasks in downstream repositories.

## Active Direction

Preserve the playbook as a governance-first, deterministic-first, artifact-first
engineering workflow. Do not turn it into a required runtime, orchestration
server, dynamic workflow framework, or Mythos/Entropy clone.

## Phase ZT-1 - Zero-Trust Execution Consolidation

### AWP-ZT-004: README-First Knowledge Index Gate

Owner: codex
Type: docs protocol
Status: done 2026-06-08

Objective: |
  Add README-first knowledge indexes as lightweight navigation artifacts at
  phase gates, without turning README files into authority or adding a new
  memory runtime.

Acceptance-Criteria:
  - `docs/readme_first_knowledge_index.md` defines when README indexes are
    required and how they relate to canonical artifacts.
  - `templates/README_INDEX.md` provides a concise repo/folder index shape.
  - Orchestrator and reviewer prompts check README index updates at phase
    boundaries or changed subsystem boundaries.
  - Cognition/vault docs state that README indexes are local navigation and the
    vault remains cross-project convenience.

Integration-Points:
  - `docs/readme_first_knowledge_index.md`
  - `templates/README_INDEX.md`
  - `prompts/ORCHESTRATOR.md`
  - `prompts/audit/PROMPT_2_CODE.md`
  - `prompts/audit/PROMPT_3_CONSOLIDATED.md`
  - `docs/cognition/`

Evidence:
  - `docs/readme_first_knowledge_index.md`
  - `templates/README_INDEX.md`
  - `docs/usage_guide.md`
  - `docs/cognition/vault_usage_protocol.md`

### AWP-ZT-001: Runtime Verification Template Integration

Owner: codex
Type: docs template
Status: done 2026-05-29

Objective: |
  Integrate runtime verification records into the default task/review flow for
  risky writes and agent claims.

Acceptance-Criteria:
  - `templates/` includes a concise runtime verification record example.
  - Review checklists require diff/hash/test evidence for claimed risky writes.
  - Docs keep filesystem/repo state as authoritative over model claims.

Integration-Points:
  - `docs/runtime_verification_protocol.md`
  - `docs/filesystem_reality_principle.md`
  - `templates/`
  - `prompts/`

Evidence:
  - `templates/RUNTIME_VERIFICATION_RECORD.md`
  - `templates/tasks_schema.md`
  - `prompts/audit/PROMPT_2_CODE.md`
  - `prompts/audit/PROMPT_3_CONSOLIDATED.md`

### AWP-ZT-002: Agent Claim Verification Checklist

Owner: codex
Type: docs review
Status: done 2026-05-29

Objective: |
  Add explicit reviewer checks for claimed files, claimed tests, claimed
  decisions, and claimed context references.

Acceptance-Criteria:
  - Review prompts ask for evidence behind every material completion claim.
  - Claimed files must exist; claimed tests must have command evidence.
  - Claimed decisions must link to ADRs, decision logs, or review records.

Integration-Points:
  - `prompts/audit/PROMPT_2_CODE.md`
  - `prompts/audit/PROMPT_3_CONSOLIDATED.md`
  - `docs/integrity_verification_jobs.md`

Evidence:
  - `prompts/audit/PROMPT_2_CODE.md`
  - `prompts/audit/PROMPT_3_CONSOLIDATED.md`

### AWP-ZT-003: Bounded Correction Defaults

Owner: codex
Type: docs protocol
Status: done 2026-05-29

Objective: |
  Make bounded correction turns the default for self-repair loops.

Acceptance-Criteria:
  - Task/review docs state the retry limit and escalation rule.
  - Intermediate state must be preserved when retries fail.
  - Autonomous repair loops cannot continue without human decision after the
    configured bound.

Integration-Points:
  - `docs/bounded_correction_turns.md`
  - `PLAYBOOK.md`
  - `prompts/`

Evidence:
  - `docs/bounded_correction_turns.md`
  - `templates/CODEX_PROMPT.md`
  - `templates/tasks_schema.md`
  - `prompts/ORCHESTRATOR.md`

## Phase EL-1 - Evidence Layer

### AWP-EL-001: Playbook-Native Receipt Schemas

Owner: codex
Type: docs protocol
Status: done 2026-07-10

Objective: |
  Define and enforce portable receipt and evidence contracts for command
  execution, failures, run results, and EvidenceBundles without depending on an
  external runtime.

Acceptance-Criteria:
  - CommandReceipt, FailureRecord, RunResult, HarnessEvalUnit, and
    EvidenceBundle schemas exist under `schemas/`.
  - `tools/receipt_run.py` creates real command receipts with stdout/stderr
    artifacts, hashes, exit code, Git state, and no self-assigned verdict.
  - `tools/validate_harness_evidence.py` validates schemas, hashes, references,
    path containment, failure taxonomy, and policy-gate conflicts.

Integration-Points:
  - `docs/runtime_verification_protocol.md`
  - `templates/RUNTIME_VERIFICATION_RECORD.md`
  - `schemas/command_receipt.schema.json`
  - `schemas/failure_record.schema.json`
  - `schemas/run_result.schema.json`
  - `schemas/evidence_bundle.schema.json`
  - `tools/receipt_run.py`
  - `tools/validate_harness_evidence.py`

Verification:
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - `python3 tools/verify_playbook.py --root .`

### AWP-EL-003: Real Command Evaluation Integrity

Owner: codex
Type: tools evaluation
Status: done 2026-07-10

Objective: |
  Harden the companion harness so real command adapter failures, required
  verification failures, invalid bundles, and hard gates cannot be silently
  treated as valid benchmark data.

Acceptance-Criteria:
  - Command adapter result exit code matches the command receipt exit code.
  - Runner creates failure records for non-zero adapter exits, timeouts, scorer
    exceptions, required verification failures, and invalid infrastructure runs.
  - Tasks can declare `required_verification`; the harness runs it after the
    adapter and records a separate receipt.
  - Comparison validates every bundle before reading scorer outputs, computes
    evidence correctness, checks paired compatibility, and warns per task when
    trial count is too low.
  - CLI exposes `--fail-on-invalid-run`, `--fail-on-hard-gate`,
    `--max-policy-violations`, and `--max-false-success-rate`.
  - Evidence artifact refs reject absolute paths and `..` escapes.

Integration-Points:
  - `companion/ai_workflow_harness_lab/src/ai_workflow_harness_lab/receipts.py`
  - `companion/ai_workflow_harness_lab/src/ai_workflow_harness_lab/adapters/command.py`
  - `companion/ai_workflow_harness_lab/src/ai_workflow_harness_lab/runner.py`
  - `companion/ai_workflow_harness_lab/src/ai_workflow_harness_lab/comparison.py`
  - `companion/ai_workflow_harness_lab/src/ai_workflow_harness_lab/evidence.py`
  - `tools/validate_harness_evidence.py`

Verification:
  - `python3 -m pytest companion/ai_workflow_harness_lab/tests/test_cli.py -q`
  - `python3 -m pytest tests/unit/test_receipt_and_evidence.py -q`
  - `python3 tools/verify_playbook.py --root .`

### AWP-EL-002: Diverse Review Principle

Owner: codex
Type: docs review
Status: planned

Objective: |
  Add a narrow principle from Gensyn-style diversity research: high-risk work
  benefits from diverse candidate reasoning and independent referee review.

Acceptance-Criteria:
  - Docs explain role/model diversity as a review/evaluation pattern.
  - Swarm behavior, distributed training, token incentives, and autonomous
    self-optimization remain out of scope.
  - The principle maps to existing META/ARCH/CODE/CONSOLIDATED review roles.

Integration-Points:
  - `PLAYBOOK.md`
  - `docs/provider_routing_policy.md`
  - `prompts/`

Verification:
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - `python3 tools/integrity_check.py --root .`

## Phase TFA-0 - Baseline And Backlog Wiring

### TFA-0.1: Add Test-First Workstream To Canonical Tasks

Owner: codex
Type: docs roadmap
Status: done 2026-07-13
Depends-On: none
Risk-Level: low
Public-Tests-Required: not_required
Critic-Required: not_required
Holdout-Required: not_required
Mutation-Required: not_required
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Add the test-first roadmap phases to the canonical task graph and near-term
  project plan without claiming that their implementations already exist.

Acceptance-Criteria:
  - Canonical tasks cover the protocol, schema/routing, Test Critic, stronger
    oracles, UI evidence, completion authority, calibration, and paired pilot.
  - Every added implementation task has validator-compatible ownership, status,
    dependencies, acceptance criteria, integration points, and verification.
  - The project plan records proportional P1/P2 test-first governance work.

Integration-Points:
  - docs/tasks.md
  - docs/PROJECT_PLAN.md
  - docs/TEST_FIRST_AGENTIC_ROADMAP.md

Verification:
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - `python3 tools/integrity_check.py --root .`

## Phase TFA-1 - First-Class Test-First Protocol

Detailed sequencing and implementation notes live in
`docs/TEST_FIRST_AGENTIC_ROADMAP.md`. All tasks in this workstream remain planned
until their task-specific verification passes.

### TFA-1.1: Add Test-First Protocol Document

Owner: codex
Type: docs protocol
Status: done 2026-07-13
Depends-On: TFA-0.1

Objective: |
  Define a risk-tiered protocol for public executable specifications,
  test-first implementation, bounded repair, and evidence capture.

Acceptance-Criteria:
  - The protocol defines when test-first is required, optional, or not
    applicable.
  - Lean / Standard / Strict modes retain proportionate minimum test
    expectations.
  - Receipts and runtime verification are evidence inputs without claims of
    empirical improvement before pilot evidence exists.

Integration-Points:
  - docs/testing/test_first_protocol.md
  - `PLAYBOOK.md`
  - `README.md`
  - `docs/usage_guide.md`

Verification:
  - `python3 tools/playbook_validate.py --root . --check placeholders`
  - `python3 tools/integrity_check.py --root .`
  - `python3 tools/verify_playbook.py --root .`

### TFA-1.2: Add Implementer TDD Prompt

Owner: codex
Type: prompt
Status: done 2026-07-13
Depends-On: TFA-1.1

Objective: |
  Add a direct implementer prompt for test-first agentic software tasks.

Acceptance-Criteria:
  - The prompt inspects existing tests and follows the required narrow
    test-first loop before broad verification.
  - Prose-only completion claims are forbidden and bounded escalation paths are
    explicit.
  - Orchestrator and downstream prompt templates select the prompt only when
    task governance requires it.

Integration-Points:
  - prompts/IMPLEMENTER_TDD.md
  - `templates/CODEX_PROMPT.md`
  - `prompts/ORCHESTRATOR.md`

Verification:
  - `python3 tools/playbook_validate.py --root . --check placeholders`
  - `python3 tools/integrity_check.py --root .`
  - `python3 tools/verify_playbook.py --root .`

## Phase TFA-2 - Task Metadata And Deterministic Routing

### TFA-2.1: Extend Task Schema With Test Governance Fields

Owner: codex
Type: schema tooling
Status: done 2026-07-14 - human-approved task scope 63f3584234d9
Depends-On: TFA-1.1
Risk-Level: high
Public-Tests-Required: required
Critic-Required: required
Holdout-Required: not_required
Mutation-Required: not_required
Property-Required: not_required
Visual-Contract: not_applicable

Test-governance rationale: the schema/parser contract changes executable task
routing and therefore requires focused public tests and independent review.
Restricted, mutation, property, and visual evidence are not task-applicable:
the change adds a bounded set of enumerated fields/defaults rather than a large
input-space invariant, hidden acceptance surface, critical algorithm, or UI.

Objective: |
  Add backward-compatible risk and test-governance fields to the machine-readable
  task contract.

Acceptance-Criteria:
  - Schema and Markdown parser support risk level, public tests, critic,
    holdout, mutation, property, and visual-contract decisions.
  - Existing task blocks remain valid through conservative defaults.
  - Templates and validator tests demonstrate a lightweight Lean default.

Integration-Points:
  - `schemas/task.schema.json`
  - `tools/playbook_validate.py`
  - `templates/TASKS.md`
  - `docs/tasks.md`
  - `tests/unit/test_playbook_validate.py`
  - `docs/audit/TEST_CRITIC_TFA-2.1_2026-07-13.md`
  - `docs/audit/HUMAN_APPROVAL_TFA-2.1_TFA-4.1_TFA-6.1_2026-07-14.md`

Verification:
  - `python3 -m pytest tests/unit/test_playbook_validate.py -q`
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - `python3 tools/verify_playbook.py --root .`

### TFA-2.2: Add Risk-Tier Routing Rules

Owner: codex
Type: docs prompt
Status: done 2026-07-13
Depends-On: TFA-2.1
Risk-Level: medium
Public-Tests-Required: not_required
Critic-Required: conditional
Holdout-Required: not_required
Mutation-Required: not_required
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Map task risk metadata to deterministic checks, evidence gates, critic review,
  stronger oracles, and human approval.

Acceptance-Criteria:
  - A routing table defines the minimum evidence and gates for each risk tier.
  - Low-risk tasks stay cheap while high/critical tasks require explicit evidence
    mapping and human approval.
  - Orchestrator, phase validation, and consolidated review consume the routing
    fields without ad hoc model judgement.

Integration-Points:
  - docs/testing/test_first_protocol.md
  - `prompts/ORCHESTRATOR.md`
  - `prompts/PHASE1_VALIDATOR.md`
  - `prompts/audit/PROMPT_3_CONSOLIDATED.md`

Verification:
  - `python3 tools/playbook_validate.py --root . --check placeholders`
  - `python3 tools/integrity_check.py --root .`
  - `python3 tools/verify_playbook.py --root .`

## Phase TFA-3 - Independent Test Critic

### TFA-3.1: Add Test Critic Prompt

Owner: codex
Type: prompt review
Status: done 2026-07-13
Depends-On: TFA-1.1, TFA-2.1
Risk-Level: medium
Public-Tests-Required: not_required
Critic-Required: not_required
Holdout-Required: not_required
Mutation-Required: not_required
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Add an independent evidence auditor for oracle gaps, missing cases, public-test
  overfitting, flaky signals, and acceptance-criteria coverage.

Acceptance-Criteria:
  - The prompt defines inputs, structured findings, severity, and anti-patterns.
  - A critic blocks only for deterministic failure, missing required evidence,
    or an explicit stop-ship policy.
  - Consolidated review can consume the critic findings without broad style or
    architecture rewrites.

Integration-Points:
  - prompts/audit/PROMPT_TEST_CRITIC.md
  - `prompts/audit/AUDIT_INDEX.md`
  - `prompts/audit/PROMPT_3_CONSOLIDATED.md`
  - docs/testing/test_first_protocol.md

Verification:
  - `python3 tools/playbook_validate.py --root . --check placeholders`
  - `python3 tools/integrity_check.py --root .`
  - `python3 tools/verify_playbook.py --root .`

### TFA-3.2: Add Test Critic Report Template

Owner: codex
Type: template
Status: done 2026-07-13
Depends-On: TFA-3.1
Risk-Level: low
Public-Tests-Required: not_required
Critic-Required: not_required
Holdout-Required: not_required
Mutation-Required: not_required
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Add a reusable evidence-mapping report for Test Critic findings.

Acceptance-Criteria:
  - The report maps acceptance criteria to tests, receipts, holdout evidence
    where applicable, and unresolved oracle gaps.
  - False-alarm and miss candidates are retained for later calibration.
  - Lean tasks do not require a critic report by default.

Integration-Points:
  - templates/TEST_CRITIC_REPORT.md
  - `templates/EVIDENCE_INDEX.md`

Verification:
  - `python3 tools/playbook_validate.py --root . --check placeholders`
  - `python3 tools/integrity_check.py --root .`

## Phase TFA-4 - Stronger Acceptance Oracles

### TFA-4.1: Add Holdout Acceptance Protocol

Owner: codex
Type: docs evaluation
Status: done 2026-07-14 - human-approved task scope 63f3584234d9
Depends-On: TFA-2.1, TFA-3.1
Risk-Level: high
Public-Tests-Required: not_required
Critic-Required: required
Holdout-Required: not_required
Mutation-Required: not_required
Property-Required: not_required
Visual-Contract: not_applicable

Test-governance rationale: this task changes documentation only; it has no
executable behavior or independent restricted oracle, so holdout applicability
resolves to `not_applicable`.

Objective: |
  Define restricted acceptance tests for merge and phase gates without exposing
  their cases to implementer prompts.

Acceptance-Criteria:
  - The protocol defines when holdouts are required, optional, or not applicable.
  - Storage, access, contamination controls, rotation, receipts, and failure
    handling are explicit.
  - Harness documentation shows how project-specific suites model holdout checks
    without adding secret contents to this repository.

Integration-Points:
  - docs/testing/holdout_acceptance.md
  - `docs/evaluation/CI_EVAL_GATE.md`
  - `docs/agent_harness/HARNESS_EVALUATION_PROTOCOL.md`
  - `companion/ai_workflow_harness_lab/README.md`
  - `docs/audit/TEST_CRITIC_TFA-4.1_2026-07-13.md`
  - `docs/audit/HUMAN_APPROVAL_TFA-2.1_TFA-4.1_TFA-6.1_2026-07-14.md`

Verification:
  - `python3 tools/playbook_validate.py --root . --check placeholders`
  - `python3 tools/integrity_check.py --root .`
  - `python3 tools/verify_playbook.py --root .`

### TFA-4.2: Add Mutation And Property Oracle Guidance

Owner: codex
Type: docs evaluation
Status: done 2026-07-13
Depends-On: TFA-2.1
Risk-Level: medium
Public-Tests-Required: not_required
Critic-Required: conditional
Holdout-Required: not_required
Mutation-Required: not_required
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Define stack-neutral selection and evidence rules for property-based and
  mutation testing on high-value code paths.

Acceptance-Criteria:
  - A decision tree distinguishes public tests, property checks, and mutation
    checks.
  - Minimum evidence includes command, configuration, threshold or rationale,
    receipt, and accepted risk for skipped required checks.
  - Evaluation templates reference stronger oracles only where their risk and
    operational cost justify them.

Integration-Points:
  - docs/testing/property_and_mutation_oracles.md
  - `templates/RETRIEVAL_EVAL_PLAN.md`
  - `templates/ROUTER_EVAL.md`
  - docs/testing/test_first_protocol.md

Verification:
  - `python3 tools/playbook_validate.py --root . --check placeholders`
  - `python3 tools/integrity_check.py --root .`
  - `python3 tools/verify_playbook.py --root .`

## Phase TFA-5 - UI Evidence Protocol

### TFA-5.1: Add UI Verification Protocol

Owner: codex
Type: docs frontend
Status: done 2026-07-13
Depends-On: TFA-2.1
Risk-Level: medium
Public-Tests-Required: not_required
Critic-Required: conditional
Holdout-Required: not_required
Mutation-Required: not_required
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Define a proportional UI evidence stack of behavior checks, visual regression,
  human review, and an optional vision critic.

Acceptance-Criteria:
  - Required UI evidence is defined by risk tier and visual contract.
  - Runtime verification can record screenshots, diffs, console output, and
    stable viewport coverage.
  - Browser tools remain examples rather than mandatory Playbook dependencies.

Integration-Points:
  - docs/testing/ui_verification.md
  - `templates/RUNTIME_VERIFICATION_RECORD.md`
  - `templates/IMPLEMENTATION_CONTRACT.md`
  - `prompts/audit/PROMPT_2_CODE.md`

Verification:
  - `python3 tools/playbook_validate.py --root . --check placeholders`
  - `python3 tools/integrity_check.py --root .`
  - `python3 tools/verify_playbook.py --root .`

## Phase TFA-6 - Completion Authority And Critic Calibration

### TFA-6.1: Add Merge Authority Policy

Owner: codex
Type: docs governance
Status: done 2026-07-14 - human-approved task scope 63f3584234d9
Depends-On: TFA-2.2, TFA-3.1
Risk-Level: high
Public-Tests-Required: not_required
Critic-Required: required
Holdout-Required: not_required
Mutation-Required: not_required
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Map risk-tier evidence and stop-ship rules to task, phase, and merge approval
  authority.

Acceptance-Criteria:
  - The policy maps risk levels to required evidence and human approval.
  - Implementers cannot self-certify completion from prose or self-authored
    verdicts.
  - Failed required tests, missing receipts, failed holdouts, security/compliance
    risk, and unaudited baseline changes have explicit stop-ship treatment.

Integration-Points:
  - docs/merge_authority.md
  - `PLAYBOOK.md`
  - `prompts/ORCHESTRATOR.md`
  - `prompts/audit/PROMPT_3_CONSOLIDATED.md`
  - `docs/audit/TEST_CRITIC_TFA-6.1_2026-07-13.md`
  - `docs/audit/HUMAN_APPROVAL_TFA-2.1_TFA-4.1_TFA-6.1_2026-07-14.md`

Verification:
  - `python3 tools/playbook_validate.py --root . --check placeholders`
  - `python3 tools/integrity_check.py --root .`
  - `python3 tools/verify_playbook.py --root .`

### TFA-6.2: Add Critic Calibration Protocol

Owner: codex
Type: docs evaluation
Status: done 2026-07-13
Depends-On: TFA-3.1, TFA-6.1
Risk-Level: medium
Public-Tests-Required: not_required
Critic-Required: conditional
Holdout-Required: not_required
Mutation-Required: not_required
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Measure Test Critic and final critic behaviour against seeded defects and
  known-good changes.

Acceptance-Criteria:
  - The protocol defines dataset shape, metrics, cadence, and decision
    thresholds by risk tier.
  - Calibration tracks false alarms, misses, severity accuracy, evidence-link
    accuracy, and repair usefulness rather than rewarding more blocks.
  - No benchmark or quality claim is made before recorded calibration and pilot
    evidence exists.

Integration-Points:
  - docs/evaluation/CRITIC_CALIBRATION.md
  - templates/TEST_CRITIC_REPORT.md
  - `companion/ai_workflow_harness_lab/README.md`

Verification:
  - `python3 tools/playbook_validate.py --root . --check placeholders`
  - `python3 tools/integrity_check.py --root .`
  - `python3 tools/verify_playbook.py --root .`

## Phase TFA-7 - Empirical Pilot

### TFA-7.1: Add Paired Pilot Plan

Owner: codex
Type: evaluation
Status: done 2026-07-15 - approved and executed for shishki_bot_v1
Depends-On: TFA-1.2, TFA-2.2, TFA-3.2, TFA-4.1, TFA-4.2, TFA-5.1, TFA-6.2
Risk-Level: high
Public-Tests-Required: not_required
Critic-Required: required
Holdout-Required: not_required
Mutation-Required: not_required
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Define a paired experiment comparing the current workflow with the test-first
  workflow in one or two real repositories.

Acceptance-Criteria:
  - The plan names project fixtures, minimum trial counts, metrics, budget, data
    retention, and human approval boundaries.
  - Mechanism validation is separated from productivity and quality claims.
  - No empirical improvement claim is made before the paired pilot produces
    reviewable evidence.

Integration-Points:
  - docs/evaluation/TEST_FIRST_PILOT_PLAN.md
  - `docs/evaluation/PLAYBOOK_EMPIRICAL_VALIDATION.md`
  - `companion/ai_workflow_harness_lab/README.md`
  - `docs/audit/TEST_CRITIC_TFA-7.1_2026-07-13.md`
  - `reports/test_first_pilot/shishki_bot_v1/PILOT_REGISTRY.md`
  - `reports/test_first_pilot/shishki_bot_v1/CRITIC_REVIEW.md`
  - `reports/test_first_pilot/shishki_bot_v1/APPROVAL_REQUEST_2026-07-15.md`
  - `reports/test_first_pilot/shishki_bot_v1/runs/shishki-tfa7-20260715/approval_record.md`

Verification:
  - `python3 tools/playbook_validate.py --root . --check placeholders`
  - `python3 tools/integrity_check.py --root .`
  - `python3 tools/verify_playbook.py --root .`

### TFA-7.2: Run And Record Pilot Results

Owner: human + codex
Type: evaluation evidence
Status: done 2026-07-15 - adjudicated; no improvement claim supported
Depends-On: TFA-7.1, TFA-7.2A, TFA-7.2B, TFA-7.2C
Risk-Level: high
Public-Tests-Required: not_required
Critic-Required: required
Holdout-Required: not_required
Mutation-Required: not_required
Property-Required: not_required
Visual-Contract: not_applicable

Execution note: the approved external runner completed one 12-execution schedule
for `shishki-tfa7-20260715`. Six blind review reports were frozen before
protected unblinding. Adjudication admitted all six pairs: baseline 2 wins,
playbook 1 win, and 3 ties. The adoption decision rejects using TFA-7 to promote
the test-first additions as empirically better or default.

Objective: |
  Execute the paired pilot and record auditable results rather than narrative
  conclusions.

Acceptance-Criteria:
  - Pilot runs produce command receipts, harness bundles, or equivalent evidence.
  - Results include wins and failures and support an explicit adoption decision.
  - Gaps found during the pilot become follow-up task records.

Integration-Points:
  - reports/test_first_pilot/
  - docs/evaluation/TEST_FIRST_PILOT_RESULTS.md
  - `docs/tasks.md`
  - `reports/test_first_pilot/shishki_bot_v1/PREFLIGHT_2026-07-15.md`
  - `reports/test_first_pilot/shishki_bot_v1/runs/shishki-tfa7-20260715/`
  - `reports/test_first_pilot/shishki_bot_v1/review/shishki-tfa7-20260715/`
  - `reports/test_first_pilot/shishki_bot_v1/review/shishki-tfa7-20260715/adjudication_report.json`

Verification:
  - Project-specific commands recorded in docs/evaluation/TEST_FIRST_PILOT_PLAN.md.
  - `find reports/test_first_pilot -name bundle.json -print0 | xargs -0 -n1 python3 tools/validate_harness_evidence.py`
  - `python3 tools/verify_playbook.py --root .`

### TFA-7.3: Preregister Larger Pilot Before Any Improvement Claim

Owner: human + codex
Type: evaluation planning
Status: planned
Depends-On: TFA-7.2
Risk-Level: high
Public-Tests-Required: not_required
Critic-Required: required
Holdout-Required: conditional
Mutation-Required: conditional
Property-Required: conditional
Visual-Contract: not_applicable

Objective: |
  Define the next empirical pilot only if the project still needs a test-first
  improvement claim after TFA-7 rejected promotion from the six-pair result.

Acceptance-Criteria:
  - The plan includes independent role separation, more tasks or repositories,
    preregistered precision or power rationale, and explicit claim thresholds.
  - The TFA-7 `shishki_bot_ci_v1` result is treated as prior evidence, not as a
    positive adoption result.
  - No documentation or prompt claims TDD/test-first improves outcomes until a
    supportive adjudicated pilot exists.

Integration-Points:
  - docs/evaluation/TEST_FIRST_PILOT_PLAN.md
  - docs/evaluation/TEST_FIRST_PILOT_RESULTS.md
  - docs/evaluation/PLAYBOOK_EMPIRICAL_VALIDATION.md
  - reports/test_first_pilot/

Verification:
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - Independent human approval before any new model-run budget.

### TFA-7.2A: Select And Approve Real Project Fixtures

Owner: human + codex
Type: evaluation preparation
Status: done 2026-07-15 - approved in completed run record
Depends-On: TFA-7.1
Risk-Level: high
Public-Tests-Required: not_required
Critic-Required: required
Holdout-Required: not_required
Mutation-Required: not_required
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Select at least one real repository and two representative tasks, then freeze
  their approved snapshots, provenance, routing, scorers, and data classification.

Acceptance-Criteria:
  - Repository/data owners approve named immutable snapshots and task provenance.
  - The fixture registry contains every field required by the paired pilot plan.
  - Generic mechanism fixtures are not represented as real-project evidence.

Integration-Points:
  - docs/evaluation/TEST_FIRST_PILOT_PLAN.md
  - `reports/test_first_pilot/shishki_bot_v1/PILOT_REGISTRY.md`
  - `companion/ai_workflow_harness_lab/suites/shishki_bot_ci_v1/`
  - `reports/test_first_pilot/shishki_bot_v1/APPROVAL_REQUEST_2026-07-15.md`
  - `reports/test_first_pilot/shishki_bot_v1/runs/shishki-tfa7-20260715/approval_record.md`

Verification:
  - Human repository/data approval references are recorded.
  - `.venv/bin/harness-lab validate-suite "$PILOT_SUITE"`

### TFA-7.2B: Approve Pilot Execution Boundary

Owner: human
Type: evaluation governance
Status: done 2026-07-15 - approved and executed once
Depends-On: TFA-7.1
Risk-Level: high
Public-Tests-Required: not_required
Critic-Required: required
Holdout-Required: not_required
Mutation-Required: not_required
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Approve the paired budget, external runner, provider/model parameters,
  permissions, redaction, retention, and protected-evidence access boundary.

Acceptance-Criteria:
  - Named owners approve ceilings sufficient for both arms of every admitted pair.
  - Credentials and protected labels remain outside repository and agent context.
  - Retention, deletion, incident, and protocol-amendment handling are recorded.

Integration-Points:
  - docs/evaluation/TEST_FIRST_PILOT_PLAN.md
  - `tools/test_first_pilot_codex_adapter.py`
  - `tools/run_test_first_pilot.sh`
  - `reports/test_first_pilot/shishki_bot_v1/APPROVAL_REQUEST_2026-07-15.md`
  - `reports/test_first_pilot/shishki_bot_v1/runs/shishki-tfa7-20260715/`
  - external approval and retention record

Verification:
  - Human budget, runner, data, and protected-access approval references are recorded.

### TFA-7.2C: Freeze Project Scorers And Pilot Ledger

Owner: human + codex
Type: evaluation preparation
Status: done 2026-07-15 - frozen and approved; review packages prepared
Depends-On: TFA-7.2A, TFA-7.2B
Risk-Level: high
Public-Tests-Required: not_required
Critic-Required: required
Holdout-Required: conditional
Mutation-Required: conditional
Property-Required: conditional
Visual-Contract: not_applicable

Objective: |
  Freeze independent scorers, protected wrappers, expected failure taxonomy,
  condition-blind adjudication, and the append-only event ledger before execution.

Acceptance-Criteria:
  - Scorer and prompt digests, metric denominators, missing-value rules, and pair
    admission rules are preregistered.
  - Required project-task routes have executable owners and evidence destinations.
  - The ledger can observe verifier attempts, first green, final model-side
    gates, heuristic repair candidates, and the non-interactive intervention
    policy; exact repair turns remain unknown without later adjudication.

Integration-Points:
  - docs/evaluation/TEST_FIRST_PILOT_PLAN.md
  - docs/evaluation/CRITIC_CALIBRATION.md
  - `reports/test_first_pilot/shishki_bot_v1/PILOT_REGISTRY.md`
  - `schemas/test_first_pilot_event.schema.json`
  - `companion/ai_workflow_harness_lab/suites/shishki_bot_ci_v1/`

Verification:
  - Project-specific scorer and protected-wrapper checks are recorded.
  - Independent human/critic review records no unresolved stop-ship gap.

## Phase PI-1 - Portfolio Integration

### AWP-PI-001: Portfolio Operating Guide

Owner: codex
Type: docs portfolio
Status: planned

Objective: |
  Document how AI Workflow Playbook, Entropy Core, Workflow-To-Agent Studio,
  Training OS, Radar, Telegram Research Agent, and Telegram Trader Intelligence
  fit together.

Acceptance-Criteria:
  - Guide names the source-of-truth repo for each responsibility.
  - It distinguishes framework, product, utility, paused, and archived projects.
  - It does not make Obsidian, Entropy, or Mythos mandatory dependencies.

Integration-Points:
  - `docs/PROJECT_PLAN.md`
  - `docs/cognition_layer_integrity.md`
  - `engineering-cognition-vault`

Verification:
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - `python3 tools/integrity_check.py --root .`

### AWP-PI-002: Lightweight Adoption Path

Owner: codex
Type: docs migration
Status: done 2026-06-09

Objective: |
  Define a lighter adoption path for projects that only need task state,
  verification records, and review checklists.

Acceptance-Criteria:
  - Migration notes list minimal, standard, and strict adoption sets.
  - Existing paused/reference projects can use minimal mode.
  - Strict mode remains available for high-risk agent/tooling systems.

Integration-Points:
  - `docs/usage_guide.md`
  - `docs/project_fit_guide.md`
  - `templates/`

Implementation-Notes: |
  Added `docs/adoption_modes.md` and updated README, PLAYBOOK, usage guide,
  Orchestrator, and Phase 1 Validator to treat Lean / Standard / Strict as
  real mode-specific paths rather than one full artifact set with softer
  language.

Verification:
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - `python3 tools/integrity_check.py --root .`

### AWP-PI-003: Solution Reference Catalog And Dynamic Workflow Policy

Owner: codex
Type: docs reference
Status: done 2026-06-09

Objective: |
  Preserve useful external references such as Hermes, Mythos, Entropy, Gensyn,
  Cybos, Claude dynamic workflows, and public workflow examples without making
  them mandatory playbook dependencies.

Acceptance-Criteria:
  - Dynamic workflows are described as optional executable orchestration
    references, not base-path requirements.
  - External references are cataloged by problem solved, useful pattern,
    authority level, and URL.
  - Public workflows require review before adaptation.
  - The playbook keeps generic principles in the base path and points advanced
    runtime/proof/swarm patterns to the reference catalog.

Integration-Points:
  - `docs/dynamic_workflow_reference_policy.md`
  - `reference/solution_references.md`
  - `README.md`
  - `reference/optional_skills.md`

Verification:
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - `python3 tools/integrity_check.py --root .`

### AWP-PI-004: AI Cost Budget Guardrails

Owner: codex
Type: docs governance
Status: done 2026-06-09

Objective: |
  Make AI/model cost a first-class workflow constraint across bootstrap,
  validation, orchestration, review, and external research references.

Acceptance-Criteria:
  - Cost budget policy defines when inline budget is enough and when
    downstream docs/COST_BUDGET.md is required.
  - Strategist and bootstrap commands collect AI/model budget before generating
    the selected mode's starter package.
  - Phase 1 Validator and Orchestrator flag missing budgets, model escalation,
    retry/fan-out expansion, and dynamic workflow cost drift.
  - Provider-agnostic telemetry has a JSONL entry contract and rollup command
    for CI/review thresholds.
  - Downstream projects have a provider-boundary adapter template and
    `cost:telemetry` task type.
  - External research sources are cited in the cost guardrails research file.

Integration-Points:
  - `docs/cost_budget_guardrails.md`
  - `templates/COST_BUDGET.md`
  - `templates/COST_TELEMETRY_ENTRY.json`
  - `templates/COST_TELEMETRY_ADAPTER.md`
  - `schemas/cost_telemetry_entry.schema.json`
  - `tools/cost_rollup.py`
  - `docs/cost_telemetry_protocol.md`
  - `reference/cost_guardrails_research.md`
  - `prompts/STRATEGIST.md`
  - `prompts/PHASE1_VALIDATOR.md`
  - `prompts/ORCHESTRATOR.md`

Verification:
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - `python3 tools/cost_rollup.py --input /tmp/missing-cost.jsonl --output /tmp/ai_cost_rollup.md`

### AWP-PI-005: AI Cost Architecture And Router Evaluation

Owner: codex
Type: docs governance
Status: done 2026-06-19

Objective: |
  Move cost controls beyond budget policy by adding an enforceable AI cost
  architecture artifact for workload classes, cache layout, batch lanes,
  routing maturity, cascades, and cost-per-successful-task.

Acceptance-Criteria:
  - `docs/ai_cost_architecture.md` defines when cost architecture is required
    and separates architecture boundaries from provider/model routing details.
  - `docs/cache_context_layout.md` defines stable-prefix and volatile-suffix
    prompt caching rules.
  - `templates/COST_ARCHITECTURE.md` and `templates/ROUTER_EVAL.md` provide
    downstream project artifacts.
  - Provider routing policy includes a maturity ladder and gates dynamic
    routing/cascades behind project eval evidence.
  - Strategist, Phase 1 Validator, Orchestrator, strategy review, code review,
    and consolidated review prompts check cost architecture and router eval
    requirements.
  - Usage docs and templates expose the new artifacts during new-project and
    retrofit setup.

Integration-Points:
  - `docs/ai_cost_architecture.md`
  - `docs/cache_context_layout.md`
  - `docs/provider_routing_policy.md`
  - `docs/cost_budget_guardrails.md`
  - `templates/COST_ARCHITECTURE.md`
  - `templates/ROUTER_EVAL.md`
  - `templates/ARCHITECTURE.md`
  - `templates/IMPLEMENTATION_CONTRACT.md`
  - `templates/COST_BUDGET.md`
  - `templates/tasks_schema.md`
  - `docs/usage_guide.md`
  - `reference/cost_guardrails_research.md`
  - `prompts/STRATEGIST.md`
  - `prompts/PHASE1_VALIDATOR.md`
  - `prompts/ORCHESTRATOR.md`
  - `prompts/PROMPT_S_STRATEGY.md`
  - `prompts/audit/PROMPT_2_CODE.md`
  - `prompts/audit/PROMPT_3_CONSOLIDATED.md`

Verification:
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - `python3 tools/integrity_check.py --root .`

### AWP-PI-006: External Skill Security Gate

Owner: codex
Type: docs governance
Status: done 2026-06-19

Objective: |
  Add a bounded security gate for third-party and cross-project agent skills so
  skills cannot enter project or global agent context without source,
  capability, scan, signature/hash, install-scope, and risk-triage evidence.

Acceptance-Criteria:
  - `docs/external_skill_security_policy.md` defines the external skill trust
    gate and maps SkillSpector/NVIDIA trust-pipeline patterns into playbook
    artifacts.
  - `templates/EXTERNAL_SKILL_TRUST_RECORD.md` provides a downstream evidence
    artifact for source pin/signature/hash, capabilities, scan evidence,
    findings triage, install scope, architecture impact, and approval.
  - Optional skill registry includes an External Skill Security Gate descriptor.
  - Task schema includes `Type: skill:security`.
  - Orchestrator, Phase 1 Validator, CODE review, consolidated review,
    Strategist, adoption docs, and templates check external skill trust records
    before install/update/enablement.
  - External references cite SkillSpector, NVIDIA skill trust docs, and the
    Agent Skills in the Wild paper as evidence for mandatory vetting.

Integration-Points:
  - `docs/external_skill_security_policy.md`
  - `templates/EXTERNAL_SKILL_TRUST_RECORD.md`
  - `templates/skills/external_skill_security_skill.md`
  - `reference/optional_skills.md`
  - `reference/solution_references.md`
  - `templates/IMPLEMENTATION_CONTRACT.md`
  - `templates/tasks_schema.md`
  - `templates/PROJECT_BRIEF.md`
  - `docs/adoption_modes.md`
  - `docs/usage_guide.md`
  - `README.md`
  - `prompts/STRATEGIST.md`
  - `prompts/PHASE1_VALIDATOR.md`
  - `prompts/ORCHESTRATOR.md`
  - `prompts/audit/PROMPT_2_CODE.md`
  - `prompts/audit/PROMPT_3_CONSOLIDATED.md`

Verification:
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - `python3 tools/skill_security_gate.py --root . --discover-agent-skills`

### AWP-PI-007: Bootstrap And Guardrail Automation

Owner: codex
Type: tools automation
Status: done 2026-06-19

Objective: |
  Close the remaining procedural gaps by adding deterministic helpers for
  project bootstrap, external skill security CI enforcement, and provider-
  neutral AI cost telemetry adapter scaffolding.

Acceptance-Criteria:
  - `tools/init_playbook_project.py` initializes Lean / Standard / Strict
    downstream projects without overwriting existing files by default.
  - `tools/skill_security_gate.py` discovers agent skill directories, requires
    trust records, invokes SkillSpector when skills are present, parses JSON
    scan output, writes optional SARIF, and blocks unresolved high-risk findings.
  - `templates/cost_adapters/python/telemetry_adapter.py` provides a concrete
    provider-neutral adapter for writing cost telemetry JSONL entries from
    common provider/gateway usage objects.
  - CI template and playbook repo workflow run the new deterministic checks.
  - Usage docs, tools docs, roadmap, and known-gaps sections describe the new
    practical path and remaining optional provider-specific work.

Integration-Points:
  - `tools/init_playbook_project.py`
  - `tools/skill_security_gate.py`
  - `templates/TASKS.md`
  - `templates/cost_adapters/`
  - `.github/workflows/playbook-checks.yml`
  - `ci/ci.yml`
  - `docs/usage_guide.md`
  - `docs/external_skill_security_policy.md`
  - `docs/cost_telemetry_protocol.md`
  - `tools/README.md`
  - `PLAYBOOK.md`

Verification:
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - `python3 -m py_compile tools/*.py`

### AWP-PI-008: Codex Exec Subagent Task Loop Protocol

Owner: codex
Type: tools protocol review
Status: done 2026-07-22
Risk-Level: medium
Critic-Required: conditional

Objective: |
  Formalize the optional task-loop profile where a main Playbook agent invokes
  isolated `codex exec` subagents for deep review, Test Critic, privacy review,
  scoped fixes, and documentation sync before commit and push.

Acceptance-Criteria:
  - The protocol distinguishes Codex Direct bootstrap from the optional
    task-loop subagent profile.
  - Standard/Strict generated projects receive the protocol, role prompts, and
    prompt renderer.
  - Review roles are read-only; fix and doc-sync roles are scoped write roles;
    no subagent commits, pushes, self-reviews, or grants human approval.
  - Usage docs show reusable `codex exec` commands for Test Critic, privacy
    review, fixes, and doc sync.
  - Renderer tests prove task, review policy, result markers, and sandbox hints
    appear in generated prompts.

Integration-Points:
  - `docs/codex_exec_subagent_protocol.md`
  - `tools/render_codex_exec_prompt.py`
  - `prompts/PROMPT_FIX_FROM_REVIEW.md`
  - `prompts/PROMPT_DOC_SYNC_AFTER_TASK.md`
  - `prompts/audit/PROMPT_0_META.md`
  - `prompts/audit/PROMPT_1_ARCH.md`
  - `prompts/audit/PROMPT_2_CODE.md`
  - `prompts/audit/PROMPT_3_CONSOLIDATED.md`
  - `prompts/audit/PROMPT_PRIVACY_REVIEW.md`
  - `tools/init_playbook_project.py`
  - `docs/usage_guide.md`
  - `README.md`
  - `prompts/ORCHESTRATOR.md`
  - `reports/test_first_pilot/shishki_bot_v1/ASSET_MANIFEST.sha256`

Verification:
  - `.venv/bin/python -m pytest tests/unit/test_render_codex_exec_prompt.py -q`
  - `.venv/bin/python -m pytest tests/integration/test_initializer.py -q`
  - `.venv/bin/python tools/playbook_validate.py --root . --check tasks --check placeholders --check readiness --check delivery --check references`
  - `python3 -m py_compile tools/render_codex_exec_prompt.py tests/unit/test_render_codex_exec_prompt.py`
  - `.venv/bin/python -m pytest tests/unit/test_test_first_pilot_assets.py::test_frozen_asset_manifest_matches_full_execution_closure -q`
