# CODEX_PROMPT.md

Version: 1.0
Date: {{DATE}}
Phase: 1

<!--
This file is the single source of truth for session state.
Every Codex agent reads this file before starting work.
Every Codex agent updates this file before committing at a phase boundary.
The orchestrator reads this file at the start of every session.

Never delete history from this file. Append; do not replace.
-->

---

## Current State

- **Phase:** 1
- **Baseline:** 0 passing tests (pre-implementation)
- **Ruff:** not yet configured
- **Last CI run:** not yet configured
- **Last updated:** {{DATE}}

---

## Next Task

**T01: Project Skeleton**

Read T01 in `docs/tasks.md` for the full specification, acceptance criteria, and file list.

---

## Fix Queue

empty

<!--
The Fix Queue contains items that must be addressed before the next phase gate,
but that were deferred from the current task. Format:

- FQ-01: [T-NN] Description of what must be fixed. Added: YYYY-MM-DD.
- FQ-02: [T-NN] Description. Added: YYYY-MM-DD.
-->

---

## Open Findings

none

<!--
Open findings from review cycles. Format:

### P1 Findings (block next phase gate)
- P1-01: [CYCLE-N] Finding description. File: path/to/file.py, line N. Must be resolved before Phase {N+1}.

### P2 Findings (must resolve within 3 cycles)
- P2-01: [CYCLE-N] Finding description. File: path/to/file.py. Opened: YYYY-MM-DD. Age: 0 cycles.

### P3 Findings (optional)
- P3-01: [CYCLE-N] Finding description.

P2 Age Cap: any P2 open for more than 3 review cycles must be resolved, escalated to P1,
or formally deferred to v2 (with ADR) before the next phase gate.
-->

---

## Completed Tasks

none

<!--
Append completed tasks here. Format:

- T01: Project Skeleton — completed YYYY-MM-DD. Baseline after: N tests.
- T02: CI Setup — completed YYYY-MM-DD. Baseline after: N tests.
-->

---

## Phase History

<!--
Append phase summaries here at each phase gate. Format:

### Phase 1 — {Phase Name}
Closed: YYYY-MM-DD
Baseline at gate: N passing tests
Tasks: T01, T02, T03
Review cycle: CYCLE-1 (see docs/audit/CYCLE1_REVIEW.md)
P1s resolved: N
P2s open: N
Gate approved by: {human name or "auto"}
-->

---

## Instructions for Codex

Read these instructions every time you pick up a task. Do not skip steps.

### Pre-Task Protocol (mandatory — do not skip)

1. **Read `docs/IMPLEMENTATION_CONTRACT.md`** — before anything else. Know the rules before touching code.
2. **Read the full task in `docs/tasks.md`** — including all acceptance criteria, file lists, and notes.
3. **Read all Depends-On tasks** — understand the interface contracts your task must satisfy.
4. **Run `pytest -q`** — capture the current baseline. Record: `N passing, M failed`. If M > 0, stop and report: you cannot add failures to an already-failing baseline.
5. **Run `ruff check`** — must exit 0. If not, fix ruff issues first. Commit the ruff fix separately with message `chore(lint): resolve ruff issues`. Then re-run the pre-task protocol.
6. **Write tests before or alongside implementation.** Every acceptance criterion has exactly one corresponding test (or more, never zero).

### During Implementation

- Work on one task at a time.
- Read only the files you need. Use `grep` to find relevant sections first.
- Do not modify files outside the task's scope without documenting why.
- If you discover an interface mismatch or missing dependency, stop and report it. Do not silently patch adjacent tasks.

### Post-Task Protocol

1. Run `pytest -q` — baseline must be ≥ pre-task baseline. If lower, something broke; fix it before committing.
2. Run `ruff check app/ tests/` — must exit 0.
3. Run `ruff format --check app/ tests/` — must exit 0.
4. Update this file (`docs/CODEX_PROMPT.md`):
   - New baseline (number of passing tests)
   - Move this task to "Completed Tasks"
   - Set "Next Task" to the next task
   - Add any new open findings discovered during this task
5. Commit with format: `type(scope): description` — one logical change per commit.
6. If the task produced multiple logical changes (migration + service + tests), use multiple commits.

### Return Format

When done, return exactly:

```
IMPLEMENTATION_RESULT: DONE
New baseline: {N} passing tests
Commits: {list of commit hashes and messages}
Notes: {anything the orchestrator should know — surprises, deviations, decisions made}
```

When blocked, return exactly:

```
IMPLEMENTATION_RESULT: BLOCKED
Blocker: {exact description of what is blocking progress}
Type: dependency | interface_mismatch | environment | ambiguity
Recommended action: {what the orchestrator or human should do}
Progress made: {what was completed before hitting the blocker}
```

### Commit Message Format

```
type(scope): short description (imperative mood, ≤72 chars)

Optional body: explain why, not what. The diff shows the what.
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `security`

Do not include:
- `Co-Authored-By` lines
- Credentials or secrets
- TODO comments without a task reference (`# TODO: see T{NN}`)
- Commented-out code
- `print()` debugging statements
