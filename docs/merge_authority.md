# Merge And Completion Authority

## Purpose

This policy defines who may mark a task, phase, or merge ready after the
risk-routed evidence gates run. It is governance documentation, not a merge bot,
server, or runtime component.

An implementer's `DONE` is a progress report. A green command is a factual gate
result. A critic finding is review evidence. None of them alone grants completion
authority.

## Readiness States

| State | Meaning |
|-------|---------|
| `implementation_reported` | The implementer reports the scoped change and cited evidence; no readiness claim is accepted yet |
| `evidence_complete` | Repository state and every resolved required gate have been independently checked for the exact task/diff |
| `review_complete` | The required deterministic, Light, Deep, and/or Test Critic review completed with no unresolved stop-ship basis |
| `approved` | The authority required by this policy recorded a durable approval for the exact scope |
| `ready` | Evidence, review, and approval are all current; this is the only state that permits the governed task/phase/merge transition |
| `blocked` | A stop-ship condition, missing authority, or stale evidence prevents the transition |

A later code, test, policy, dependency, baseline, or target-branch change may
invalidate evidence or approval. Re-run the affected gates against the new
scope; do not carry a stale `ready` label forward.

## Role Authority

| Role | May do | May not do |
|------|--------|------------|
| Implementer | Change scoped files; report commands, results, receipts, and blockers | Self-certify evidence, close its own review findings, approve risk, phase advance, or merge |
| Deterministic test/verifier/CI | Produce reproducible pass/fail observations for its declared scope | Interpret product risk, grant an exception, or approve completion |
| Test Critic or review agent | Audit oracle/evidence gaps and cite deterministic or policy stop-ship bases | Grant accepted risk, assign merge authority, or turn an uncalibrated opinion into a block |
| Orchestrator | Validate repository state, aggregate gates, enforce stop conditions, and record delegated low/medium task state | Waive a required gate, approve high/critical work, approve a phase/merge, or rely on implementer prose |
| Consolidated reviewer | Validate findings, assign P-severity, and record an evidence/stop-ship disposition | Approve its own report as the human authority or override a failed required gate |
| Human approver | Approve the exact level and scope when all non-waived gates are satisfied; own explicit accepted risk | Convert a failed deterministic gate to pass or approve evidence it did not receive |

Role separation matters more than vendor identity. Cross-vendor review is an
optional hedge, not a default gate or evidence of better outcomes.

## Risk-Tier Authority

Risk strengthens the selected adoption mode; it does not make every task use the
Strict evidence surface.

| Risk | Minimum task evidence and review | Task readiness authority | Phase and merge authority |
|------|----------------------------------|--------------------------|---------------------------|
| `low` | Concrete task test/verifier, repository-state check, all explicitly required gates, and Deterministic/Light review selected by mode and change type | Orchestrator or maintainer may record `ready` under the selected Playbook workflow's standing delegation for routine task state; otherwise human maintainer | Human maintainer at the meaningful phase/merge boundary after current CI/verification |
| `medium` | Focused and broader declared checks, baseline comparison, all resolved required gates, receipts when triggered, and independent Light/Deep review selected by route | Orchestrator may record `ready` after the workflow-required independent review; project policy may instead reserve it for a human | Human maintainer after phase/merge evidence and review |
| `high` | Acceptance-criterion evidence map, all resolved required gates, Deep independent review and Test Critic, applicable eval/runtime evidence, and no unresolved stop-ship condition | Explicit human risk-owner approval for the exact task/diff is required | Explicit human approval is required again for the phase/merge scope |
| `critical` | High-tier evidence plus applicable negative/failure paths, pre-execution approval, critical task-local controls, and a current final evidence review | Named accountable human approves before execution and after evidence review; delegation is forbidden | Named accountable human gives explicit phase/release approval; missing evidence remains stop-ship |

Lean-Core keeps routine low-risk work cheap. A high/critical task in Lean-Core
gets the task-local risk floor and should trigger mode reconsideration; it does
not automatically change the mode of unrelated tasks.
Strict adds maintained CI/eval/review controls but does not manufacture mutation,
holdout, or visual work when the task route makes it not applicable.
The standing low/medium task delegation advances work only within the already
selected workflow. It cannot accept risk, waive a gate, or approve a phase or
merge.

## Level Gates

### Task Ready

All of the following must be true:

1. The canonical task record, risk, and resolved governance route are valid.
2. Acceptance criteria map to tests, verifiers, evals, or reviewable evidence.
3. Claimed files and results match repository state and the reviewed diff.
4. Required focused, broader, CI/eval, receipt, holdout, mutation/property,
   visual, critic, and runtime evidence is present and passing where applicable.
5. Baseline changes and pre-existing failures are attributed and reviewed.
6. Required review completed and no stop-ship basis remains.
7. The risk-tier task authority recorded approval or valid delegated policy.

### Phase Ready

Every task in scope is task-ready; phase CI/eval gates are current; P0/P1 and
required Test Critic blockers are resolved; audit/state/docs artifacts match the
repository; and a human approves the exact phase evidence set. Phase approval
cannot be inferred from the absence of findings.

### Merge Ready

The target diff/commit is unchanged since its evidence was collected; target-
branch CI and every route-required gate are green; no unreviewed change or
stop-ship condition remains; and a human maintainer/risk owner approves that
exact merge scope. A prior task or phase approval does not waive a newly failed
merge gate.

## Stop-Ship Conditions

| Code | Condition | Required disposition |
|------|-----------|----------------------|
| `REQUIRED_GATE_FAILED` | A required test, verifier, lint/type/schema/contract check, CI job, eval threshold, mutation/property check, or visual gate failed | Fix and rerun; do not approve |
| `REQUIRED_EVIDENCE_MISSING` | A route-required command result, receipt, artifact, critic report, runtime record, or approval is absent/non-reviewable | Produce the evidence or correct the route before implementation; do not infer pass |
| `HOLDOUT_GATE_FAILED` | A required restricted/holdout gate failed or its result is missing | Keep cases restricted, fix through public evidence, and rerun through the authorized harness |
| `REPOSITORY_STATE_MISMATCH` | Claimed files, diff, commit, deletion, test result, or task state does not match filesystem/git reality | Reconcile the claim and rerun affected verification |
| `UNAUDITED_BASELINE_CHANGE` | Failures, pass counts, thresholds, fixtures, snapshots, or accepted baselines changed without attribution and independent review | Restore or explicitly review the change; never normalize it silently |
| `SECURITY_COMPLIANCE_BLOCK` | An unresolved explicit security, privacy, compliance, cross-tenant, credential, destructive-action, or approval-boundary policy violation exists | Human escalation and verified remediation; no agent waiver |
| `AUTHORITY_OR_SCOPE_DRIFT` | Runtime tier, privilege, side effects, task scope, or risk was expanded without the required decision/approval | Stop, reclassify, and obtain approval before continuing |
| `HUMAN_APPROVAL_REJECTED_OR_BYPASSED` | Required approval was rejected/expired, or a transition is attempted without it | Block the transition; do not mark ready or manufacture approval |

Missing receipts are blocking only when the task/route requires a receipt.
Optional evidence cannot become stop-ship merely because a reviewer would prefer
it.

When all other evidence is complete and the named human has not decided yet,
the state is `approval_required`, not a code/evidence failure. It becomes
stop-ship only if approval is rejected, expires, or the workflow attempts to
bypass the approval boundary.

## Critic Authority

Test Critic and consolidated-review observations are advisory unless they cite:

- an observed deterministic failure
- missing resolved-required evidence
- an exact stop-ship condition in this or another governing policy
- a calibrated high-risk critic rule whose current calibration record explicitly
  permits blocking

Until the calibration protocol exists and current evidence satisfies it, critic
confidence or severity is not a blocking mechanism. A `NO_FINDING` result waives
nothing, and a `BLOCKER` without a valid cited basis is reduced to a concern for
human disposition.

## Exceptions And Accepted Risk

Resolve applicability before implementation. A human may approve a narrower
route or planned exception only when the risk floor and governing policy permit
it. Do not lower a gate after seeing its failure.

An exception record must include task and gate, owner, reason, unavailable
capability, compensating evidence, exact scope, decision date, expiry/follow-up,
and human approval. Its status is `accepted_risk`, never `passed`.

The following are not waivable through this process:

- no concrete task test or verifier
- a failing required deterministic/CI gate
- a failed required holdout gate
- repository-state mismatch or unreviewed evidence weakening
- implementer self-review or self-approval
- missing high/critical, phase, or merge human authority
- an explicit non-waivable security/compliance/safety boundary

## Approval Record

Durable approval records must name:

- level: task, phase, or merge
- task IDs and exact diff/commit/release scope
- approver identity and accountable role
- evidence/review artifacts considered
- decision: approved, rejected, or accepted risk with conditions
- timestamp, expiry or invalidation conditions, and required follow-up

Store the record in the project's review report, PR/merge record, signed change
record, ADR, or another canonical auditable surface. Ephemeral chat, an
implementer summary, or an agent-authored approval is insufficient.

## Claims Boundary

This policy defines a reviewable authority mechanism. Its existence does not
prove fewer defects, faster delivery, better critic accuracy, or improved
productivity. Such claims require the paired pilot and calibration evidence.
