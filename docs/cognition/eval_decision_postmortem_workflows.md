# Eval, Decision, Finding, and Postmortem Memory

Version: 1.0
Last updated: 2026-05-25

---

## ADR Lineage

Use ADRs for decisions that change architecture, runtime tier, capability profile behavior, data boundaries, eval policy, or governance rules.

ADR lifecycle:

1. Write ADR with status `Proposed`.
2. Link supporting research, eval, or finding evidence.
3. Mark `Accepted` only after human approval.
4. Add or update `docs/DECISION_LOG.md`.
5. Add task `Context-Refs` to the ADR when implementation depends on it.
6. Supersede with a new ADR instead of editing history.

Decision lineage fields:

- `Decision ID`
- `ADR`
- `Status`
- `Supersedes`
- `Superseded by`
- `Evidence`
- `Affected evals`
- `Affected tasks`

---

## Eval-Linked Memory

Every active capability profile needs an eval artifact when behavior changes:

- RAG: `docs/retrieval_eval.md`
- Tool-use: `docs/tool_eval.md`
- Agentic: `docs/agent_eval.md`
- Planning: `docs/plan_eval.md`
- Compliance: `docs/compliance_eval.md`

Eval memory must record:

- exact eval source
- date
- corpus or fixture version when relevant
- baseline
- current result
- delta
- regression decision
- linked task or ADR

An eval row without `Eval Source` or date is invalid.

---

## Finding Persistence

Findings are not just review comments. They are operational memory until closed.

Finding lifecycle:

1. Review opens finding with severity.
2. `docs/CODEX_PROMPT.md` open findings section is updated.
3. `docs/EVIDENCE_INDEX.md` links the finding to proof or missing proof when the finding is recurring or high-risk.
4. Fix task references the finding in `Context-Refs`.
5. Reviewer closes the finding with evidence path.
6. Closure is archived in the relevant review report or audit index.

Never close a P1/P2 finding only in a vault note.

---

## Postmortems

Use postmortems for:

- eval regressions that reached a phase boundary
- production incidents
- escaped defects that should have been caught by the playbook
- repeated P2 findings that indicate system drift
- retrieval or agent behavior that failed despite tests passing

Recommended path:

```text
docs/postmortems/YYYY-MM-DD-short-slug.md
```

Required sections:

- `Impact`
- `Detection`
- `Timeline`
- `Root Cause`
- `Why Existing Controls Missed It`
- `Corrective Actions`
- `Evidence`
- `Decision or Contract Changes`
- `Regression Tests or Eval Updates`

Postmortems should update the evidence index and, when architecture changes, create or supersede an ADR.

---

## Hypothesis Tracking

Hypotheses are operational when they guide build or evaluation decisions.

Store product and architecture hypotheses in one of:

- `docs/hypotheses/*.md` for standalone records
- `docs/*_eval.md` experiment sections
- product strategy docs when already canonical

Minimum fields:

- hypothesis statement
- decision it informs
- evidence needed
- current state: `untested`, `testing`, `supported`, `weakened`, `rejected`
- next review date or task

Do not track vague preferences, daily thoughts, or personal notes.

