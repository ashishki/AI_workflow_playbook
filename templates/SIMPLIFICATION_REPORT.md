# SIMPLIFICATION_REPORT — {{PROJECT_NAME}} (Template)

_Copy to `docs/audit/SIMPLIFICATION_REPORT.md` in your project. Overwrite per
pass — only the most recent pass lives here. The skill is opt-in and
experimental; see `reference/optional_skills.md` and
`templates/skills/simplification_skill.md`._

---

## Header

- Pass: SIMP-{N}
- Date: YYYY-MM-DD
- Project: {{PROJECT_NAME}}
- Reviewer: simplification reviewer agent (`prompts/audit/PROMPT_SIMPLIFY.md`)

## Baseline

- Tests passing before pass: N
- Complexity baseline: {tool name + summary numbers}
- Scope (user-stated or fallback): {file/dir list}

## Approved Findings

### SIMP-{N}-{NN} — Title

- File: path:line-line
- Current shape: short description
- Proposed simplification: short description
- Behavior delta: **none** (required)
- Complexity delta: estimated improvement
- Test guard:
  - existing test `tests/...::test_...` pins behavior, OR
  - new pinning test required: `tests/...::test_...` (must be added by the
    implementing task)
- Risk: low | medium

(repeat per finding)

## Rejected Findings

### SIMP-{N}-{NN}-rej — Title

- File: path:line-line
- Reason: behavior change | weakens contract | masks open finding | removes
  required instrumentation | other (specify)

(repeat per rejection)

## Notes

Optional — what the human should know before approving.

## Approval

- Approved by: {human reviewer name or handle}
- Approved on: YYYY-MM-DD
- Tasks created in `docs/tasks.md`: {T-NN, T-NN, ...}
