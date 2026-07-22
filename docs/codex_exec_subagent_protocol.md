# Codex Exec Subagent Protocol

Status: formalized operating profile
Maturity: prompt renderer tested; end-to-end autonomous task loop not claimed

## Purpose

This protocol defines how a main Playbook agent can use isolated `codex exec`
subagents for implementation review, Test Critic, privacy/security review,
fixes, and documentation sync while preserving role separation.

It is not the default bootstrap path. The default bootstrap path remains Codex
Direct: one active Codex session initializes the project, runs validators, and
does not spawn nested Codex processes. This protocol is an optional task-loop
profile selected after bootstrap when the project wants the main agent to
orchestrate specialized child agents.

## Roles

| Role | Writes files | Purpose | Completion authority |
|------|--------------|---------|----------------------|
| main_agent | yes | Select next task, dispatch subagents, run final gates, commit and push after approval | no |
| implementer | yes | Implement one scoped task, tests, and implementation evidence | no |
| meta_review | no | Run existing `PROMPT_0_META.md` scope and state snapshot | no |
| arch_review | no | Run existing `PROMPT_1_ARCH.md` architecture drift review | no |
| code_review | no | Run existing `PROMPT_2_CODE.md` code/security review | no |
| test_critic | no | Audit whether tests and evidence prove acceptance criteria | no |
| privacy_review | no | Audit privacy, raw-content, PII, logs, storage, and fail-closed behavior | no |
| fix_from_review | yes | Apply scoped fixes for frozen review findings | no |
| doc_sync | yes | Update task state, evidence index, journal, decision log, and session state after green gates | no |
| human | n/a | Accept task completion when policy requires it | yes |

Review agents are read-only. Fix agents do not review. Documentation sync does
not approve completion. Commit and push happen only after required gates are
green and required human approval is recorded.

## Task Loop

1. Main agent chooses the first ready task whose dependencies are satisfied.
2. Implementer handles code, tests, and implementation evidence for exactly one
   task.
3. Main agent runs deterministic gates:
   - `python3 tools/playbook_validate.py --root . --check tasks --check placeholders --check readiness --check delivery --check references`
   - `python3 tools/verify_project.py --root .`
   - `git diff --check`
4. Main agent resolves required review roles from `docs/REVIEW_POLICY.md`,
   `.playbook/delivery_execution_model.json`, and task fields such as
   `Risk-Level`, `Critic-Required`, `Visual-Contract`, and `Type`.
5. Main agent launches isolated read-only review subagents with `codex exec`.
6. If any required review returns `STOP_SHIP`, `BLOCKER`, or an actionable
   finding selected by policy, main agent launches `fix_from_review`.
7. Main agent reruns deterministic gates and required reviews after fixes.
8. When all required reviews are green, main agent launches `doc_sync`.
9. Main agent reruns deterministic gates.
10. If the task requires human completion authority, main agent stops until the
    human records approval.
11. Main agent commits and pushes.
12. Main agent moves to the next ready task.

## Standard Commands

Generate prompts with `tools/render_codex_exec_prompt.py` and pass the rendered
prompt into `codex exec`.

Deep review uses the existing audit chain from `docs/audit/`, not a separate
new prompt. Run the relevant steps as isolated read-only child agents:

```bash
codex exec \
  --cd "$PROJECT_ROOT" \
  --sandbox read-only \
  --output-last-message "docs/audit/META_ANALYSIS.md" \
  "$(python3 tools/render_codex_exec_prompt.py --root . --task T03 --role meta_review --output-path docs/audit/META_ANALYSIS.md)"

codex exec \
  --cd "$PROJECT_ROOT" \
  --sandbox read-only \
  --output-last-message "docs/audit/ARCH_REPORT.md" \
  "$(python3 tools/render_codex_exec_prompt.py --root . --task T03 --role arch_review --output-path docs/audit/ARCH_REPORT.md)"

codex exec \
  --cd "$PROJECT_ROOT" \
  --sandbox read-only \
  --output-last-message "docs/audit/CODE_REVIEW.md" \
  "$(python3 tools/render_codex_exec_prompt.py --root . --task T03 --role code_review --output-path docs/audit/CODE_REVIEW.md)"

codex exec \
  --cd "$PROJECT_ROOT" \
  --sandbox read-only \
  --output-last-message "docs/audit/REVIEW_REPORT.md" \
  "$(python3 tools/render_codex_exec_prompt.py --root . --task T03 --role consolidated_review --review docs/audit/CODE_REVIEW.md --review docs/verification/T03_test_critic.md --review docs/verification/T03_privacy_review.md --output-path docs/audit/REVIEW_REPORT.md)"
```

Test Critic:

```bash
codex exec \
  --cd "$PROJECT_ROOT" \
  --sandbox read-only \
  --output-last-message "docs/verification/T03_test_critic.md" \
  "$(python3 tools/render_codex_exec_prompt.py --root . --task T03 --role test_critic --output-path docs/verification/T03_test_critic.md)"
```

Privacy review:

```bash
codex exec \
  --cd "$PROJECT_ROOT" \
  --sandbox read-only \
  --output-last-message "docs/verification/T03_privacy_review.md" \
  "$(python3 tools/render_codex_exec_prompt.py --root . --task T03 --role privacy_review --output-path docs/verification/T03_privacy_review.md)"
```

Fix from review findings:

```bash
codex exec \
  --cd "$PROJECT_ROOT" \
  --sandbox workspace-write \
  --output-last-message "docs/verification/T03_fix_result.md" \
  "$(python3 tools/render_codex_exec_prompt.py --root . --task T03 --role fix_from_review --review docs/verification/T03_test_critic.md --review docs/verification/T03_privacy_review.md --output-path docs/verification/T03_fix_result.md)"
```

Documentation sync after green reviews:

```bash
codex exec \
  --cd "$PROJECT_ROOT" \
  --sandbox workspace-write \
  --output-last-message "docs/verification/T03_doc_sync_result.md" \
  "$(python3 tools/render_codex_exec_prompt.py --root . --task T03 --role doc_sync --review docs/audit/REVIEW_REPORT.md --review docs/verification/T03_test_critic.md --review docs/verification/T03_privacy_review.md --human-approval-ref docs/verification/T03_human_approval.md --output-path docs/verification/T03_doc_sync_result.md)"
```

## Required Result Markers

The existing deep-review audit chain keeps its current template-specific output
contracts:

- `META_ANALYSIS.md written. Run PROMPT_1_ARCH.md.`
- `ARCH_REPORT.md written. Run PROMPT_2_CODE.md.`
- `CODE review done. P0: X, P1: Y, P2: Z. Run PROMPT_3_CONSOLIDATED.md.`
- `Cycle N complete.`

Additional task-loop reports must start with one of these markers:

- `TEST_CRITIC_RESULT: NO_FINDING | ADVISORY | STOP_SHIP`
- `PRIVACY_REVIEW_RESULT: PASS | ADVISORY | STOP_SHIP`

Fix and doc sync reports must start with:

- `FIX_RESULT: APPLIED | BLOCKED`
- `DOC_SYNC_RESULT: UPDATED | BLOCKED`

The main agent treats `STOP_SHIP`, `BLOCKER`, `BLOCKED`, missing required
reports, or missing result markers as not complete.

## Authority Boundaries

- A review subagent must run read-only and must not write files.
- A fix subagent may write only within the task scope and docs required to
  explain the fix.
- A doc-sync subagent may update task/evidence/session docs only after green
  verification and required review artifacts exist.
- No subagent commits or pushes.
- No subagent grants human approval.
- If policy requires human completion authority, the loop stops until a human
  approval artifact is recorded.
