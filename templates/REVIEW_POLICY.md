# Project Review Policy

This policy wires the existing Playbook review mechanisms into this project.
The selected roles, delivery profile, task-loop status and optional model /
reasoning bindings live in `.playbook/delivery_execution_model.json`.
Read that contract before dispatching work. A model binding is a requested
setting, not evidence that the host changed model or that a reviewer ran.
Unset model IDs remain environment-owned. Unset reviewer reasoning follows the
chosen runner's default (Governed Role Runner: `medium`), not necessarily the
parent's effort. Record the actual invocation; select explicit settings as needed.

## Roles and authority

- `solo_verified`: human orchestrates; the active session implements and fixes;
  independent review is selected by risk. The task-loop subagent profile is off.
- `independent_review`: the active session selects work, writes code, applies
  fixes and collects evidence. Separate read-only agents review; they may use
  the same model but must have independent context. The existing task-loop
  subagent profile is selected for work after bootstrap.
- Bootstrap itself stays Codex Direct. Initializing does not launch models,
  authorize new spend, modify host settings, or prove a successful agent loop.
- Reviewers do not fix code, commit, approve their own work or spawn reviewers.
  The main session applies implementer-owned fixes; it never authors missing
  independent review, human approval or restricted-holdout evidence.
- Completion authority remains the human named by the delivery contract.
  Phase/merge and high/critical approvals follow `docs/merge_authority.md`.
  Selecting an orchestrator does not delegate completion or risk acceptance.

## Review routing and stopping

Use the existing routing and correction rules in
`docs/prompts/ORCHESTRATOR.md`; its external orchestration launch examples are
not instructions to run nested implementers from an active Codex session.
Resolve review depth before implementation from the task risk, change type,
active profile and explicit required gates. Record the route with task evidence.

- Deterministic review: qualifying low-risk navigation/documentation changes
  with no semantic or authority change; run the declared project checks.
- Light: routine scoped changes and contract/documentation changes where the
  existing route does not require Deep; independent reviewer, focused findings.
- Deep: architecture/security/authority boundaries, high/critical risk and
  profile-specific triggers. Use the existing audit chain:
  META -> ARCH -> CODE -> Test Critic when required -> CONSOLIDATED.
  Significant boundaries trigger it; a small follow-up does not restart the
  entire chain unless it creates a new applicable trigger.
- Fix only findings with a valid blocking basis. Optional minor/style ideas
  go to the backlog; they are not a new gate. Required evidence cannot be waived
  by assigning a finding a lower severity.
- Light: one targeted correction/recheck; repeated issues stop the task.
  Deep: at most two correction attempts, rerunning affected gates and required
  review stages on the changed scope. Remaining blockers stop and escalate.
  Missing approval is routed to the approver, not another code-fix attempt.

## Context and evidence

Use `docs/codex_exec_subagent_protocol.md` and the existing prompt renderer.
For the four supported review roles, use `tools/run_codex_role.py`; a failed
runner is invalid evidence, not permission to bypass it with unmanaged exec.

Pass a bounded task digest: task/acceptance criteria, exact scope and base/diff,
applicable contract rules, dependency facts, verification commands, required
evidence, role and output path. A fresh exec process does not inherit the parent
conversation. Return findings with file/evidence references, severity and
blocking basis; the parent reconciles reports against current repository state.
Dependent audit stages consume preceding reports; only independent work may
run concurrently. No full transcript or full Playbook by default.

Keep `docs/CODEX_PROMPT.md` to current state, next action and evidence pointers.
Put history in `docs/IMPLEMENTATION_JOURNAL.md`, decisions in
`docs/DECISION_LOG.md` and results in `docs/EVIDENCE_INDEX.md` plus task reports.
Model choice, independence, actual checks and remaining gaps must be reported
truthfully; a generated policy is not a passing product review.
