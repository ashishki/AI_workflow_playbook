# Audited Execution Protocol

Status: experimental mechanism. Not a Playbook Mode. Not empirical evidence.

## Execution Profiles

`direct_codex` is the default profile for short and medium tasks. The normal
Feature Workflow still applies: approved design, one slice, deterministic
verification, independent review, and human/policy acceptance.

`audited_rounds` is optional for a long, high-risk slice where state drift is a
material risk. It wraps execution of one accepted slice contract in bounded
rounds:

`accepted slice contract -> manager proposal -> fresh executor -> read-only auditor -> deterministic apply-audit -> audited state`

Feature Workflow remains the authority for what to build, boundaries, human
authority, slice acceptance, and release readiness.

## Trust Model

- Agent claims are not evidence.
- Executor reports always have `trust_status=unverified`.
- Auditor is read-only and does not update persistent state.
- Only deterministic `apply-audit` can update `audited_state.json`.
- `done` is blocked until all requirements in audited state are verified.
- Fresh executor prompts include the original goal ref, current audited state,
  current round contract, allowed files, verification, permissions, and budget.
  They exclude raw old Executor history.

## Artifacts

Audited runs live under:

`.playbook-artifacts/audited-runs/<run-id>/`

Required run files:

- `manifest.json`
- `audited_state.json`
- `result.json`
- `rounds/0001/manager_proposal.json`
- `rounds/0001/round_contract.json`
- `rounds/0001/executor_prompt.md`
- `rounds/0001/executor_report.json`
- `rounds/0001/audit_prompt.md`
- `rounds/0001/audit_report.json`
- `rounds/0001/receipts/...`

Audited state stores verified requirements, verified facts, blockers,
verified artifact refs, open requirements, audit refs, round counters, and
budgets. It does not store hidden chain of thought or unverified Executor prose
as operational truth.

## Feature Workflow Integration

Start a slice normally:

```bash
python3 tools/feature_workflow.py --root . start \
  --task T14 \
  --feature-id F01 \
  --slice-id F01-S1 \
  --execution-profile direct_codex
```

Start an audited slice:

```bash
python3 tools/feature_workflow.py --root . start \
  --task T14 \
  --feature-id F01 \
  --slice-id F01-S1 \
  --execution-profile audited_rounds
```

For `audited_rounds`, the generated slice context becomes the run's original
goal ref. `feature_workflow check` requires a complete audited run result
before it runs the normal slice verification/review/acceptance gates.

For high-risk slices the sequence is:

`start -> implementation -> check/review -> local commit -> accept-slice -> next`

`accept-slice` requires a clean working tree, current HEAD different from the
slice base commit, a matching candidate diff hash, current post-state file
hashes, unchanged verification receipts, unchanged review records, and human
acknowledgement for advisories.

## CLI

The companion lab exposes:

```bash
harness-lab audited-run init
harness-lab audited-run next
harness-lab audited-run executor-prompt
harness-lab audited-run audit-prompt
harness-lab audited-run apply-audit
harness-lab audited-run status
harness-lab audited-run stop
```

Stop reasons include:

- `budget_exhausted`
- `repeated_failure`
- `no_progress`
- `policy_violation`
- `human_input_required`
- `all_requirements_verified`

## Harness Lab Comparison

Harness Lab may compare:

`direct_codex` vs `audited_rounds`

The comparison must keep task, model, CLI/harness version, permissions,
environment, timeout, cost ceiling, verification, and human acceptance policy
constant.

Metrics:

- task success
- verified requirements completed
- false-progress rounds
- audit rejection rate
- rework rounds
- state-loss incidents
- repeated failed actions
- scope violations
- human interventions
- wall-clock time
- tokens
- tool calls
- cost per successful task

The included audited-rounds fixture is a mechanism demonstration: round 1
claims success and audit rejects; round 2 supplies evidence and audit verifies.
It is not empirical evidence.

## LongHorizon-Harness Boundary

The official LongHorizon-Harness paper describes a Manage-Execute-Audit loop
with explicit task state, fresh-context execution, and read-only audit. The
official repository exposes an `lh-harness` CLI, `doctor`, project config, and
run directories under `.lh-harness/runs/<run-id>/`.

This Playbook implementation does not add LongHorizon-Harness as a dependency.
Until a project explicitly pilots it, the boundary is export/import:

- export the approved slice context and acceptance criteria as the task;
- run `lh-harness doctor` and record the exact installed version/commit;
- run the external harness outside Playbook CI;
- import only verified final state, receipts, and report refs;
- pass through Feature Workflow `check` and `accept-slice`.

No quality improvement is claimed without a real paired pilot.

## Non-Goals

- No generic autonomous scheduler.
- No model training, RL, distillation, teacher model calls, or model-internal
  memory.
- No ReOPD, Prime Intellect, or Molt integration.
- No cryptographic attestation.
- No replacement for human design/slice/final acceptance.
