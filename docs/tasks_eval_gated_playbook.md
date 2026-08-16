# Evaluation-Gated Playbook Workstream

Status: active execution backlog
Created: 2026-08-16
Base commit: `2474ac816a15491bd260b2f80ad89a9e642d8228`

This workstream turns Harness Lab from an optional demonstration surface into a
controlled evidence source for Playbook changes.

It does **not** require an empirical model run for every commit. Every change
must declare the level of evidence it needs, and changes that alter agent
behavior must not become a default recommendation without baseline/candidate
evidence.

Until `EVG-1.1` lands, the evaluation fields described below are roadmap fields,
not valid fields in the canonical task schema. Do not add them to ordinary
`docs/tasks.md` task blocks before the schema/parser migration is complete.

## Target Operating Loop

```text
change hypothesis
→ evaluation requirement
→ pinned baseline
→ candidate implementation
→ deterministic or empirical evidence
→ comparison
→ human/policy decision
→ merge/default-promotion gate
→ retained regression assets
```

## Evidence Levels

- `none`: formatting, typo, link, or pure archival movement with no behavioral
  effect.
- `deterministic`: schemas, parsers, validators, path safety, state transitions,
  release logic, hashes, and ordinary code whose outcome has a deterministic
  oracle.
- `mechanism`: a new lifecycle or harness mechanism whose execution semantics
  must be demonstrated, without claiming real-model benefit.
- `empirical`: prompts, `AGENTS.md`, context packets, model/tool routing,
  reviewer behavior, execution profiles, or any other change intended to alter
  coding-agent behavior.

## Decision Outcomes

- `promote`: evidence supports the change and it may become the default.
- `accept_without_claim`: the change may merge for correctness or maintenance,
  but no quality/productivity improvement may be claimed and it must not become
  a recommended default on that basis.
- `inconclusive`: evidence is valid but insufficient or too noisy.
- `reject`: a hard gate regressed or the hypothesis failed materially.

## Global Hard Gates

No target-metric improvement may compensate for regression in:

- task success;
- required verification;
- false completion;
- policy violations;
- path/symlink containment;
- security or hidden trust-boundary cases;
- human approval and evidence integrity;
- exact-commit release truthfulness.

Do not reduce this workstream to one aggregate quality score.

## Required Order

```text
EVG-0.1
→ EVG-1.1
→ EVG-1.2
→ EVG-1.3
→ EVG-2.1 + EVG-2.2
→ EVG-2.3
→ EVG-3.1 / EVG-3.2 / EVG-3.3 / EVG-3.4
→ EVG-4.1
→ EVG-4.2
```

Do not start broad cleanup before `EVG-0.1` is green. Do not promote an
agent-behavior change before `EVG-2.3` produces a valid decision.

---

## Phase EVG-0 — Truthful Baseline

### EVG-0.1: Separate Portable Core From Environment Pilots

Owner: codex
Type: verification tooling
Status: planned
Depends-On: none
Risk-Level: high
Public-Tests-Required: required
Critic-Required: required
Holdout-Required: not_required
Mutation-Required: conditional
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Make the canonical Playbook verification gate honestly green on a supported
  portable environment while retaining host-specific Codex/toolchain pilots as
  explicit, non-authoritative optional evidence.

Acceptance-Criteria:
  - Every current check is classified as `portable_core` or
    `environment_pilot` with a documented prerequisite.
  - The default canonical verifier executes all portable-core checks and fails
    on any required portable-core failure.
  - Environment pilots run only when their exact prerequisites are present.
  - A skipped environment pilot is reported as `not_run`/`not_applicable`, never
    as passing capability evidence.
  - Frozen pilot fixtures are not rewritten merely to make the gate green.
  - Missing `/usr/bin/bwrap`, Codex-version mismatch, and equivalent host drift
    no longer make the portable core permanently red.
  - Exact-HEAD verification produces a current machine-readable result and
    current status report.

Metrics:
  - portable required failures;
  - environment pilots executed/skipped/failed;
  - canonical verification wall-clock time;
  - number of tests or gates weakened: zero.

Integration-Points:
  - `tools/verify_playbook.py`
  - `tools/playbook_validate.py`
  - frozen pilot tests and manifests
  - `.github/workflows/playbook-checks.yml`
  - current verification reports

Verification:
  - `.venv/bin/python -m pytest -q`
  - `.venv/bin/python tools/playbook_validate.py --root .`
  - `.venv/bin/python tools/verify_playbook.py --root .`
  - negative fixture: portable failure still fails the canonical gate
  - negative fixture: skipped environment pilot is not counted as positive evidence
  - `git diff --check`

Non-Goals:
  - Do not delete a real invariant because the current host cannot execute it.
  - Do not introduce a second general-purpose test runner.

---

## Phase EVG-1 — Evaluation Requirement And Decision Gate

### EVG-1.1: Add Evaluation Metadata To The Task Contract

Owner: codex
Type: schema tooling
Status: planned
Depends-On: EVG-0.1
Risk-Level: high
Public-Tests-Required: required
Critic-Required: required
Holdout-Required: not_required
Mutation-Required: not_required
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Extend the task contract with a minimal, backward-compatible declaration of
  what evidence a Playbook change requires.

Acceptance-Criteria:
  - Task schema, Markdown parser, templates, and validator support:
    `Evaluation-Requirement`, `Evaluation-Suite`,
    `Evaluation-Baseline-Ref`, `Evaluation-Primary-Metrics`,
    `Evaluation-Guardrail-Metrics`, `Evaluation-Min-Trials`, and
    `Evaluation-Decision-Ref`.
  - `Evaluation-Requirement` is one of `none`, `deterministic`, `mechanism`, or
    `empirical`.
  - New active behavior-changing tasks must declare the requirement explicitly.
  - Historical completed tasks remain readable without being silently
    reinterpreted as empirically proven.
  - Duplicate aliases, invalid enum values, empty required suite refs, and
    non-positive trial counts fail closed.
  - Existing tasks are migrated through a documented staged compatibility path,
    not by bulk-adding meaningless placeholder values.

Integration-Points:
  - `schemas/task.schema.json`
  - `tools/playbook_validate.py`
  - `templates/TASKS.md`
  - task parsing tests
  - `docs/tasks.md` after the schema is valid

Verification:
  - focused parser/schema tests
  - legacy-task compatibility fixture
  - negative tests for unknown fields, duplicate aliases, invalid requirement,
    and zero trials
  - `.venv/bin/python tools/playbook_validate.py --root . --check tasks`
  - `.venv/bin/python tools/verify_playbook.py --root .`

### EVG-1.2: Add A Deterministic Evaluation Policy Resolver

Owner: codex
Type: policy tooling
Status: planned
Depends-On: EVG-1.1
Risk-Level: high
Public-Tests-Required: required
Critic-Required: required
Holdout-Required: not_required
Mutation-Required: conditional
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Recommend and validate the evidence level from task metadata and changed
  artifact classes without using an LLM as the policy authority.

Acceptance-Criteria:
  - The resolver classifies at least:
    - typo/link/archive-only changes as `none` or lightweight `deterministic`;
    - schemas, parsers, validators, hashes, paths, and release logic as
      `deterministic`;
    - new lifecycle/harness mechanics as `mechanism`;
    - prompts, `AGENTS.md`, context packets, reviewer behavior, model/tool
      routing, and execution-profile defaults as `empirical`.
  - Output contains the recommended requirement, reasons, detected facts,
    unknown facts, and any human override with rationale.
  - An override to a weaker level requires human provenance and a reason.
  - The resolver performs no model or network calls.
  - The policy is versioned and included in evaluation decision identity.

Integration-Points:
  - task parser and changed-path inventory
  - Feature Workflow planning/status output
  - review policy
  - future unified CLI mapping

Verification:
  - table-driven policy tests covering every change class
  - negative test: prompt/AGENTS behavior change cannot silently resolve to
    `none` or `deterministic`
  - negative test: unsupported downgrade without reason is blocked
  - full portable-core verification

### EVG-1.3: Add One Change-Evaluation Decision Artifact And Gate

Owner: codex
Type: evidence tooling
Status: planned
Depends-On: EVG-1.2
Risk-Level: critical
Public-Tests-Required: required
Critic-Required: required
Holdout-Required: required
Mutation-Required: conditional
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Consume existing deterministic verification or Harness Lab evidence and
  resolve whether a change may be promoted, accepted without a claim, treated
  as inconclusive, or rejected.

Acceptance-Criteria:
  - Exactly one new decision contract is introduced; existing EvidenceBundle,
    HarnessEvalUnit, comparison, receipt, and verification schemas are reused.
  - The decision records task ID, requirement level, pinned baseline ref,
    candidate commit, suite/version, identity fingerprint, evidence refs/hashes,
    target metrics, guardrail metrics, hard-gate outcomes, decision, rationale,
    and human/policy provenance.
  - The resolver never launches paid/model work; it validates and consumes
    already-created evidence.
  - Evidence is stale when candidate commit, suite, identity, prompt/context,
    scorer, permissions, or referenced hashes change.
  - `empirical` promotion requires compatible baseline/candidate units, minimum
    trials, current evidence, green hard gates, and human acceptance.
  - `accept_without_claim` may permit a correctness/maintenance merge but cannot
    support a productivity/quality claim or default recommendation.
  - `inconclusive` and `reject` cannot be relabeled by manually editing one
    status field.
  - `playbook_validate --check evaluation` and the completion/release path block
    missing or stale required decisions.

Integration-Points:
  - `schemas/` — one decision schema
  - `tools/resolve_change_evaluation.py` or equivalent existing resolver path
  - `tools/playbook_validate.py`
  - Feature Workflow completion gate
  - release-readiness resolver
  - EvidenceBundle/comparison validation

Verification:
  - deterministic task with green receipts resolves successfully
  - mechanism task without mechanism evidence is blocked
  - empirical task without paired bundles is blocked
  - incompatible HarnessEvalUnit identity is blocked
  - changed candidate commit makes the decision stale
  - tampered metric/evidence hash is blocked
  - hard-gate regression resolves to `reject`
  - full portable-core verification

---

## Phase EVG-2 — Stable Agent-Behavior Evaluation

### EVG-2.1: Build `playbook_agent_behavior_v1`

Owner: codex
Type: harness evaluation
Status: planned
Depends-On: EVG-1.3
Risk-Level: high
Public-Tests-Required: required
Critic-Required: required
Holdout-Required: required
Mutation-Required: conditional
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Create one reusable empirical suite for Playbook changes that alter coding
  agent behavior, rather than creating a new suite for every prompt edit.

Acceptance-Criteria:
  - The suite contains pinned, isolated repository fixtures for at least eight
    task shapes:
    1. small root-cause bugfix;
    2. new CLI argument;
    3. validator extension;
    4. backward-compatible schema change;
    5. security-sensitive path handling;
    6. consolidation of duplicate test fixtures;
    7. removal/gating of an inactive optional capability;
    8. documentation-only change where overbuilding should be near zero.
  - Each task has an executable success oracle and at least one hidden or
    adversarial case where relevant.
  - Tasks do not reveal holdout details to the implementer condition.
  - Fixture state, task text, verification, timeout, permissions, and scorer
    versions are pinned.
  - The suite distinguishes mechanism demonstration from empirical runs.
  - Raw runtime output stays outside Git unless it supports a durable decision;
    compact manifests and accepted comparisons may be committed.

Target-Metrics:
  - production LOC;
  - test LOC;
  - files created and touched;
  - schemas and dependencies added;
  - loaded instruction/context size.

Guardrail-Metrics:
  - task success;
  - hidden-edge-case success;
  - false completion;
  - policy/scope violations;
  - required verification success;
  - security/trust-boundary success.

Cost-Metrics:
  - input/output tokens;
  - tool calls;
  - wall-clock time;
  - model cost when available;
  - human interventions.

Verification:
  - suite schema validation
  - deterministic scorer self-tests
  - one scripted mechanism run marked non-empirical
  - contamination test: baseline cannot load candidate instructions
  - holdout-leak test
  - full portable-core verification

### EVG-2.2: Harden Empirical Isolation And Comparison Semantics

Owner: codex
Type: harness integrity
Status: planned
Depends-On: EVG-2.1
Risk-Level: critical
Public-Tests-Required: required
Critic-Required: required
Holdout-Required: required
Mutation-Required: conditional
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Ensure observed differences come from the intended Playbook change rather
  than global plugins, reused threads, mismatched environments, or scorer drift.

Acceptance-Criteria:
  - Every trial uses a fresh worktree/copy and fresh agent context.
  - Baseline and candidate record exact repository ref, model/provider, CLI,
    reasoning profile, permissions, delivery profile, tool registry, timeout,
    retry policy, prompt/context hashes, plugin/hook sources, and environment
    digest.
  - Global agent plugins/instructions are excluded or explicitly identical in
    both arms.
  - Scripted adapters are rejected for empirical claims.
  - Minimum trials are enforced per task, not only in aggregate.
  - Target, guardrail, and cost metrics remain separate; no single weighted
    quality score decides acceptance.
  - Guardrails use non-inferiority or strict zero-regression thresholds declared
    before the run.
  - Invalid, timed-out, or infrastructure-failed trials are preserved and
    classified rather than silently discarded.

Verification:
  - deliberate plugin contamination is detected
  - prompt/context hash mismatch blocks comparison
  - scorer/version mismatch blocks comparison
  - missing task pair blocks comparison
  - zero/insufficient trials block empirical decision
  - invalid runs are visible in the report and cannot improve the candidate
  - full portable-core verification

### EVG-2.3: Run The Minimal-Implementation Policy A/B Pilot

Owner: human + codex
Type: empirical evaluation
Status: planned
Depends-On: EVG-2.2
Risk-Level: high
Public-Tests-Required: required
Critic-Required: required
Holdout-Required: required
Mutation-Required: not_required
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Measure whether the Minimal Implementation Policy reduces code and artifact
  growth without reducing correctness, robustness, safety, or evidence quality.

Conditions:
  - Baseline ref: `965612aa463fca1a35a55104633d0e09da33d615`.
  - Candidate ref: `2474ac816a15491bd260b2f80ad89a9e642d8228`.
  - Suite: `playbook_agent_behavior_v1`.
  - Minimum: 3 valid trials per task per arm.
  - Expected total: 8 tasks × 2 arms × 3 trials = 48 valid runs.

Acceptance-Criteria:
  - The only intended behavioral difference between arms is the minimal
    implementation instruction set.
  - All HarnessEvalUnit compatibility checks pass.
  - Candidate target metrics are reported per task and in aggregate.
  - Task success, hidden-edge-case success, false completion, policy violations,
    security cases, and required verification do not regress beyond declared
    margins.
  - Any candidate-only failure becomes a retained eval/regression case before a
    second run.
  - A current change-evaluation decision is recorded as `promote`,
    `accept_without_claim`, `inconclusive`, or `reject`.
  - No headline efficiency claim is made from invalid or insufficient trials.

Decision-Policy:
  - `promote`: meaningful reduction in code/artifacts with green guardrails.
  - `accept_without_claim`: policy is useful as a preference but benefit is not
    established.
  - `inconclusive`: run more or narrow the policy.
  - `reject`: remove or weaken the default policy when guardrails regress.

Verification:
  - validate every EvidenceBundle
  - `harness-lab compare --require-empirical`
  - change-evaluation resolver against exact candidate ref
  - human decision receipt

---

## Phase EVG-3 — Evaluation-Gated Minimality Cleanup

### EVG-3.1: Reduce Active Task And Prompt Context (`MIN-S2` + `MIN-S3`)

Owner: codex
Type: context and prompt cleanup
Status: planned
Depends-On: EVG-2.3
Risk-Level: high
Public-Tests-Required: required
Critic-Required: required
Holdout-Required: required
Mutation-Required: not_required
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Move completed task history out of the active task graph and reduce the
  default `CODEX_PROMPT` without losing task discovery, continuity, or completion
  discipline.

Evaluation-Intent:
  - requirement: empirical;
  - target: loaded context tokens, active task file size, prompt size;
  - guardrails: correct next-task selection, instruction adherence, false
    completion, required verification, continuity after a fresh session.

Acceptance-Criteria:
  - `docs/tasks.md` contains active/near-term work; completed history moves to one
    indexed archive with stable IDs and evidence refs.
  - Capability-specific state blocks are generated/loaded only when active.
  - One authoritative protocol exists per concept; summaries link rather than
    restate it.
  - Candidate output is net-negative in default loaded context.
  - Empirical comparison shows no guardrail regression before the reduced prompt
    becomes the default template.

Verification:
  - task/archive reference validation
  - context packet/token measurement
  - fresh-session task-selection trials
  - baseline/candidate comparison and decision artifact
  - full portable-core verification

### EVG-3.2: Simplify Initializer And Gate Optional Packs (`MIN-S4` + `MIN-S5`)

Owner: codex
Type: bootstrap refactor
Status: planned
Depends-On: EVG-2.3
Risk-Level: high
Public-Tests-Required: required
Critic-Required: required
Holdout-Required: not_required
Mutation-Required: conditional
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Replace repeated initializer copy lists with one declarative inventory, move
  the generated verifier out of an inline string, and keep inactive experimental
  packs out of default projects.

Evaluation-Intent:
  - requirement: deterministic;
  - target: initializer LOC, duplicate declarations, default generated files;
  - guardrails: generated-project matrix, backward compatibility, verifier
    truthfulness, exact mode/capability contents.

Acceptance-Criteria:
  - One versioned file inventory selects artifacts by mode and capability.
  - Generated verifier lives in one testable runtime template.
  - Lean-Core/default output excludes inactive audited/RAG/experimental packs.
  - Explicit capability flags produce complete valid packs.
  - Upgrade/hash behavior remains compatible or has a documented migration.
  - The refactor is net-negative in repeated code and does not introduce a
    generic plugin framework.

Verification:
  - Lean-Core/Standard/Strict generated-project matrix
  - each optional capability on/off matrix
  - failing downstream project still fails generated verification
  - no inactive pack leakage
  - initializer dry-run and overwrite-preservation tests
  - full portable-core verification

### EVG-3.3: Consolidate Tests By Unique Invariant (`MIN-S6`)

Owner: codex
Type: test architecture cleanup
Status: planned
Depends-On: EVG-3.2
Risk-Level: critical
Public-Tests-Required: required
Critic-Required: required
Holdout-Required: required
Mutation-Required: required
Property-Required: conditional
Visual-Contract: not_applicable

Objective: |
  Reduce test and fixture volume while preserving or improving the ability to
  catch every known false-success, safety, and evidence-tampering path.

Evaluation-Intent:
  - requirement: mechanism plus deterministic failure injection;
  - target: test LOC, fixture LOC, duplicated setup, suite runtime;
  - guardrails: unique invariant inventory and injected-failure catch rate.

Acceptance-Criteria:
  - A machine- or human-readable invariant map links each protected invariant to
    at least one executable negative case.
  - Repeated state/path/alias variants are parameterized where this improves
    clarity.
  - Thin-wrapper, constant, stdlib, and duplicate schema tests are removed only
    when they protect no unique failure mode.
  - Known bypasses remain protected: false completion, required-check failure,
    path/symlink escape, stale/tampered evidence, self-approval, review bypass,
    high-risk acceptance, exact-HEAD release, and dirty-tree blocking.
  - Selected mutation/failure-injection cases demonstrate that the consolidated
    suite still fails when core guards are weakened.
  - No raw coverage percentage is used as the acceptance oracle.
  - The slice is net-negative in tests/fixtures or runtime.

Verification:
  - invariant map completeness review
  - focused mutation/failure-injection run
  - full portable-core suite
  - before/after test runtime and LOC report
  - no protected invariant loses its negative case

### EVG-3.4: Consolidate Documentation And Evidence Retention (`MIN-S7` + `MIN-S8`)

Owner: codex
Type: docs and evidence cleanup
Status: planned
Depends-On: EVG-3.3
Risk-Level: medium
Public-Tests-Required: conditional
Critic-Required: required
Holdout-Required: not_required
Mutation-Required: not_required
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Establish one authority per protocol and remove/archive committed evidence that
  no longer supports a live task, ADR, release, regression, or empirical claim.

Evaluation-Intent:
  - requirement: deterministic, with a targeted context-navigation smoke test;
  - target: duplicated protocol prose, committed historical noise, default
    navigation/context size;
  - guardrails: no live claim loses provenance; no active task/reference breaks.

Acceptance-Criteria:
  - An authority map names the canonical document for each major concept.
  - README, PLAYBOOK, usage, tool docs, and reports use short summaries and links
    rather than competing full protocols.
  - Reports are classified as current, historical, or removable.
  - Ordinary runtime output remains under ignored `.playbook-artifacts/`.
  - Every deleted report has no live inbound task/ADR/release/claim reference.
  - Link/reference validation and a fresh-agent navigation smoke test pass.
  - The cleanup is net-negative in committed files, prose, or default context.

Verification:
  - internal link/reference scan
  - evidence-index consistency check
  - fresh-agent navigation smoke task
  - full portable-core verification

---

## Phase EVG-4 — Default Change Control And V1 Acceptance

### EVG-4.1: Make Evaluation Requirement The Default For Future Playbook Work

Owner: codex
Type: workflow integration
Status: planned
Depends-On: EVG-3.4
Risk-Level: high
Public-Tests-Required: required
Critic-Required: required
Holdout-Required: required
Mutation-Required: conditional
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Make evidence-level selection and decision freshness part of normal Playbook
  completion without turning every commit into an expensive empirical run.

Acceptance-Criteria:
  - New task templates require an explicit evaluation requirement.
  - Deterministic and mechanism tasks remain cheap and local.
  - Agent-behavior changes require empirical evidence before becoming default.
  - CI validates decision/evidence freshness but does not launch paid model runs.
  - Baselines are pinned and cannot be silently moved after a failed candidate.
  - `accept_without_claim` is visibly distinct from `promote` in docs/reports.
  - Missing/stale required evidence blocks completion/release claims.
  - Low-risk docs-only work remains proportional.

Verification:
  - task creation/template tests
  - deterministic task completes without empirical bundles
  - prompt change cannot promote without empirical decision
  - CI offline evidence validation
  - stale candidate/baseline negative tests
  - full portable-core verification

### EVG-4.2: Dogfood The Full Loop And Produce The Internal V1 Decision

Owner: human + codex
Type: release readiness evaluation
Status: planned
Depends-On: EVG-4.1
Risk-Level: critical
Public-Tests-Required: required
Critic-Required: required
Holdout-Required: required
Mutation-Required: conditional
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Prove the completed Playbook can govern its own deterministic, mechanism, and
  empirical changes end to end before declaring the internal tool finished.

Acceptance-Criteria:
  - At least one deterministic change, one mechanism change, and one empirical
    agent-behavior change pass the full requirement → evidence → decision flow.
  - One cleanup change is accepted only after its declared metrics and guardrails
    are checked.
  - One intentionally bad candidate is rejected by a hard gate.
  - One `accept_without_claim` or `inconclusive` scenario is preserved to prove
    the system does not force every valid change into a success narrative.
  - Exact-HEAD portable verification is green.
  - No known false-success path remains open in current audits.
  - Generated Lean-Core/Standard/Strict projects pass their expected smoke
    matrix.
  - One real existing repository completes a retrofit → task → verification →
    decision flow using the current Playbook.
  - A commit-scoped report states tested mechanisms, empirical results,
    limitations, and deferred work without stale test counts.

Internal-V1 Exit Criteria:
  - simple new-project and retrofit flows are executable from documented entry
    points;
  - required checks and evidence are truthful;
  - behavior-changing defaults have a current evaluation decision;
  - optional experimental packs remain optional;
  - default context and generated artifacts are materially smaller than the
    pre-cleanup baseline;
  - future corrections can be promoted into permanent eval/regression assets.

Verification:
  - exact commands and EvidenceBundles recorded
  - current change-evaluation decisions validate
  - full portable-core verification
  - generated-project smoke matrix
  - retrofit case-study report
  - human internal-v1 acceptance receipt

---

## Workstream Completion Rule

This workstream is complete only when Playbook changes can be classified and
accepted through the smallest sufficient evidence path:

```text
docs-only change
→ no unnecessary empirical run

validator/security change
→ deterministic negative evidence

new lifecycle mechanism
→ mechanism demonstration and tamper tests

agent-behavior/default change
→ isolated baseline/candidate empirical evidence
```

The result must be a smaller and more trustworthy Playbook, not a second
evaluation framework layered on top of Harness Lab.
