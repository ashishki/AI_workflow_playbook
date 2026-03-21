# AI Workflow Playbook

Version: 1.0
Last updated: 2026-03-21
Reference implementation: https://github.com/ashishki/gdev-agent

---

## 1. Philosophy

### AI-Assisted Development

The developer is the architect and reviewer. AI agents (Codex) write code. Review agents validate it. The human approves phase gates. Nothing progresses without human sign-off.

This is not "AI writes everything." This is "AI does the mechanical work under a structure you control." The value of this workflow is the structure — the prompts, the contracts, the review cycle — not the raw capability of any individual agent call.

### The Three-Layer Loop

```
Strategist (architecture)
    → Orchestrator (phase execution)
        → Codex agents (implementation, one task at a time)
            → Review cycle (META → ARCH → CODE → CONSOLIDATED)
                → Human approval
                    → next phase
```

Every layer has a defined input, a defined output, and a defined boundary with the next layer. No layer crosses into another layer's responsibility.

### Why This Works

- **Phase gates** prevent drift. A flaw caught at the end of Phase 2 is infinitely cheaper than one discovered in Phase 8.
- **Subagents** prevent context collapse. Each task and each review runs in its own context window with exactly the files it needs.
- **CODEX_PROMPT.md** is the single source of truth for session state. Any agent can resume a session by reading it. Nothing is held in conversational memory.
- **IMPLEMENTATION_CONTRACT.md** is the unchanging floor. Architectural decisions may evolve; the contract does not, without an explicit ADR.

---

## 2. Project Initialization (Phase 1)

Phase 1 is not optional and is not abbreviated. Every project — regardless of size, scope, or timeline — begins here.

### Required Deliverables at End of Phase 1

1. `docs/ARCHITECTURE.md` — system design document
2. `docs/spec.md` — feature specification with acceptance criteria
3. `docs/tasks.md` — complete task graph
4. `docs/CODEX_PROMPT.md` — session handoff document, initialized
5. `docs/IMPLEMENTATION_CONTRACT.md` — immutable rules, tailored to the project
6. Project skeleton (directories, `__init__.py`, entry points)
7. First tests (at minimum: smoke tests proving the skeleton works)
8. CI setup (`.github/workflows/ci.yml`) — passing on first commit

### Why CI Is Set Up in Phase 1

CI is not a Phase 3 polish task. Setting it up in Phase 1 means:
- Every subsequent commit is automatically verified
- Baseline drift is caught immediately, not accumulated
- Review cycles can reference CI status as ground truth
- There is never a moment when "tests pass locally but CI is unknown"

Deferring CI past Phase 1 is a forbidden action. See Section 9.

### Establishing the Baseline

After the first passing tests, record the baseline in `docs/CODEX_PROMPT.md`:

```
Current Baseline: N passing tests
Last CI run: green
```

Every subsequent session starts by running `pytest` and comparing against this baseline. A session that produces fewer passing tests than the baseline has broken something and must not commit.

---

## 3. Phase Structure

### What a Phase Is

A phase is a coherent unit of work that takes the project from one stable state to the next. A phase contains one or more tasks from `tasks.md`. Tasks within a phase may run sequentially or — if independent — in parallel via parallel subagents.

Phases are sequential. Phase N is never started until the Phase N-1 gate is passed.

### Phase Gate Criteria

All of the following must be true before a phase is closed:

- [ ] All tests pass (`pytest` exits 0)
- [ ] Ruff is clean (`ruff check` exits 0, `ruff format --check` exits 0)
- [ ] All P1 findings from the review cycle are resolved
- [ ] `docs/CODEX_PROMPT.md` is updated with new baseline, next task, and open findings
- [ ] Review cycle report saved to `docs/audit/CYCLE{N}_REVIEW.md`
- [ ] Human has reviewed and approved

### CODEX_PROMPT.md at Phase Boundaries

`CODEX_PROMPT.md` must be updated before the commit that closes a phase. It must contain:
- Current baseline (number of passing tests)
- Next task (the first task of the next phase, or "COMPLETE" if done)
- Open findings from the review cycle (P2s that survived, P3s of note)
- Fix Queue (any items deferred to next phase)

---

## 4. Task Execution — Codex Agent Protocol

Each task is executed by a Codex subagent. The orchestrator spawns the subagent with a precise prompt. The subagent operates in its own context window.

### Pre-Task Protocol (skip nothing)

The following steps are mandatory before writing any implementation code:

1. **Read the full task** in `tasks.md` — including all acceptance criteria and the Depends-On list.
2. **Read all Depends-On tasks** to understand the interface contracts you must satisfy.
3. **Run `pytest`** to capture the pre-task baseline. Record the number: `N passing, M failed`.
4. **Run `ruff check`** — must exit 0. Do not begin if ruff is not clean. Fix ruff issues first, commit them separately.
5. **Write tests before or alongside implementation.** No task is complete until every acceptance criterion has a passing test.

### During Implementation

- Work on one task at a time. Do not begin the next task until the current one is committed.
- Read only the files you need. Use `grep` to find relevant lines; read only those sections.
- Do not modify files outside the task's stated scope without explicit justification.
- If you discover a dependency or interface mismatch, stop and report it. Do not silently patch adjacent tasks.

### Post-Task Protocol

1. Run the full pre-commit check suite:
   - `ruff check app/ tests/`
   - `ruff format --check app/ tests/`
   - `pytest` — verify baseline increased or held (never decreased)
2. Update `docs/CODEX_PROMPT.md`:
   - New baseline
   - Next task
   - Any open findings discovered during this task
3. Commit with a granular commit message. One logical change per commit.
4. If the task produced multiple logical changes (e.g., a migration + a service + tests), use multiple commits.

### Codex Prompt Structure (from Orchestrator)

When the orchestrator spawns a Codex subagent, the prompt must specify:

```
Task: T{NN} — {task name}
Files to read: [exact list]
Files to modify: [exact list]
Files to create: [exact list]
Expected output: [what you return when done]
Acceptance criteria: [copied from tasks.md]
Pre-task baseline: {N} passing tests
```

Vague Codex prompts produce vague results. Precise prompts produce verifiable results.

---

## 5. Review Cycle Structure

The review cycle runs after each phase. It consists of four sequential review agents. Each is a subagent with its own context window.

### PROMPT_1: META Review

**Question answered:** Did the implementation follow the process?

Checks:
- Were all acceptance criteria from `tasks.md` implemented?
- Is each acceptance criterion covered by a test?
- Was the pre-task baseline captured and recorded?
- Was `docs/CODEX_PROMPT.md` updated at the phase boundary?
- Were any forbidden actions taken (see Section 9)?
- Was CI passing at the time of the phase gate commit?

Output: list of META findings (compliance gaps), each tagged P1/P2/P3.

### PROMPT_2: ARCH Review

**Question answered:** Does the implementation match the architecture?

Checks:
- Do new components appear in `docs/ARCHITECTURE.md`? If not, is an ADR warranted?
- Are new route handlers thin (delegate to services)?
- Are services testable without HTTP (accept primitives and sessions)?
- Is all SQL parameterized with named params?
- Is `SET LOCAL` used instead of session-level `SET` (for multi-tenant systems)?
- No PII in log messages, span attributes, or metrics?
- Shared tracing module used — no inline noop spans?
- Authorization enforced on every new route?

Output: list of ARCH findings, each tagged P1/P2/P3.

### PROMPT_3: CODE Review

**Question answered:** Does the code meet quality standards?

This review reads actual code. It:
- Verifies every finding from PROMPT_1 and PROMPT_2 against the actual source files
- Identifies additional code-level issues (error handling gaps, type errors, missing edge cases, security issues)
- Reviews test quality (are tests actually asserting behavior, or just running?)
- Checks for common anti-patterns

Severity tags:
- **P1** — must be fixed before the next phase gate. Blocks the phase.
- **P2** — must be fixed within 3 review cycles (see P2 Age Cap rule below). Does not block the current phase gate.
- **P3** — optional improvement. Log it, address it if convenient.

Output: consolidated findings with severity tags, file references, and specific line numbers where applicable.

### PROMPT_4: CONSOLIDATED Review

**Question answered:** What is the official state of this phase?

This agent:
- Merges findings from PROMPT_1, PROMPT_2, and PROMPT_3
- Deduplicates overlapping findings
- Produces the cycle report: `docs/audit/CYCLE{N}_REVIEW.md`
- Determines which P1s must be resolved before the gate passes
- Updates `docs/CODEX_PROMPT.md` with open findings

The cycle report is append-only. Do not edit previous cycle reports.

### P2 Age Cap Rule

Any P2 finding that remains open for more than 3 consecutive review cycles MUST be:
- Closed (resolved), OR
- Escalated to P1 (and resolved before the next phase gate), OR
- Formally deferred to v2 (documented in an ADR, removed from open findings)

A P2 finding cannot age indefinitely. The Age Cap rule prevents the finding backlog from becoming a graveyard.

### Running Reviews Concurrently

PROMPT_1 (META) and PROMPT_2 (ARCH) can run concurrently — they read different things. PROMPT_3 depends on their outputs. PROMPT_4 depends on PROMPT_3. So the sequence is:

```
[PROMPT_1 || PROMPT_2] → PROMPT_3 → PROMPT_4
```

---

## 6. Immutable Implementation Rules

These rules apply to every project that uses this playbook. They must appear verbatim in `docs/IMPLEMENTATION_CONTRACT.md`. They are never changed without an explicit Architectural Decision Record (ADR) filed in `docs/adr/`.

### Universal Rules

**SQL safety**
- All SQL is parameterized. Use `text()` with named params: `text("SELECT ... WHERE id = :id")`.
- Never interpolate variables into SQL strings.
- Never use string concatenation to build queries.

**Multi-tenant systems**
- Every database call is preceded by the appropriate tenant context (`SET LOCAL app.tenant_id = :tid` or equivalent RLS setup).
- No query executes without a tenant context in multi-tenant code paths.

**Async Redis**
- Redis is accessed only in `async def` functions using `redis.asyncio`.
- Never import or call the synchronous redis client in async code paths.

**Authorization**
- Every new route handler enforces authorization (role check, JWT validation, or equivalent).
- Authorization is never deferred to "we'll add it later."

**PII policy**
- No PII in log messages, span attributes, or metrics.
- Where identifiers must be logged, use hashes (SHA-256 or equivalent).
- This applies to all observability — logs, traces, and metrics.

**Credentials**
- No credentials, API keys, or secrets in source code.
- Use environment variables. Document required env vars in `docs/ARCHITECTURE.md` under Runtime Contract.

**Tracing**
- Shared tracing module: one `get_tracer()` function, imported everywhere.
- No inline noop span implementations scattered across files.
- All spans use the shared module.

**CI**
- CI must pass before any PR is merged.
- No exceptions. No "merge now, fix CI later."

---

## 7. Commit Discipline

### One Logical Change Per Commit

If a task involves a database migration, a service implementation, and tests, that is three commits — not one. Split at the boundary of logical changes, not at the boundary of files.

### Commit Message Format

```
type(scope): short description

Optional body: explain the why, not the what. The diff shows the what.
```

Types:
- `feat` — new feature
- `fix` — bug fix
- `refactor` — restructuring without behavior change
- `test` — adding or fixing tests
- `docs` — documentation only
- `chore` — maintenance (deps, config, CI)
- `perf` — performance improvement
- `security` — security fix

### What Not to Include in Commits

- No `Co-Authored-By` lines from AI agents
- No secrets or credentials
- No TODO comments without a task reference (`# TODO: see T{NN}`)
- No commented-out code
- No `print()` debugging statements left in production code

---

## 8. Token Efficiency Strategy

Token efficiency is not about being cheap with the API. It is about keeping agent context windows clean so that agents produce accurate outputs.

### Primary Strategies

**Subagents for heavy tasks**
Any task that requires reading more than 5 files, or produces more than approximately 2,000 lines of output, should run in a subagent. Subagents have fresh context windows — they do not carry the accumulated context of the orchestrator session.

**CODEX_PROMPT.md as session state**
`CODEX_PROMPT.md` is the zero-overhead session resumption mechanism. Any new session starts by reading this file. There is no need to re-read the entire codebase to know where you are.

**Selective reads**
Always: `grep` first to find the relevant lines, then read only those lines. Do not `cat` entire files to find one function.

**Compact before large tasks**
Run `/compact` before starting a deep review cycle or a large refactor. This condenses accumulated context without losing the active state.

**Parallel agents for independent work**
META and ARCH reviews can run as parallel subagents. Independent tasks within a phase can run as parallel subagents if there are no data dependencies between them.

**Precise Codex prompts**
The orchestrator prompt to a Codex agent must list exact files to read, exact files to modify, and the expected return format. Vague prompts cause agents to explore broadly, consuming tokens on files that are not relevant.

---

## 9. Forbidden Actions

The following actions are never permitted without explicit documented exception:

| Action | Why Forbidden |
|--------|---------------|
| String interpolation in SQL | SQL injection risk; parameterized queries are non-negotiable |
| Session-level `SET` in multi-tenant systems | Leaks tenant context across requests; use `SET LOCAL` |
| Skipping pre-task baseline capture | Cannot verify that implementation did not break existing tests |
| Self-closing review findings without code verification | Findings are closed by reading the code, not by asserting the code was fixed |
| Modifying `IMPLEMENTATION_CONTRACT.md` without an ADR | The contract is immutable; changes require architectural review |
| Deferring CI setup past Phase 1 | Every commit after Phase 1 must be CI-verified |
| Running tests without capturing the pre-change baseline | Baseline comparison is the primary correctness signal |
| Merging a PR with failing CI | The CI gate exists for this reason |
| Committing credentials or secrets | Irreversible exposure risk |

If any of these occur, they must be surfaced as P1 findings in the next review cycle. They are not waived retroactively.

---

## 10. Documentation Set

Every project using this playbook maintains the following documents. They are not optional.

| Document | Path | Role | Mutability |
|----------|------|------|------------|
| Architecture | `docs/ARCHITECTURE.md` | System design, component table, data flows, runtime contract | Updated when architecture changes; changes need ADR if significant |
| Specification | `docs/spec.md` | Feature specification and acceptance criteria | Updated when scope changes; changes need human approval |
| Task graph | `docs/tasks.md` | Authoritative task contracts — the ground truth for what agents implement | Append-only for completed tasks; active tasks updated as needed |
| Session handoff | `docs/CODEX_PROMPT.md` | Current baseline, Fix Queue, open findings, next task | Updated at every phase boundary and before every Codex spawn |
| Implementation contract | `docs/IMPLEMENTATION_CONTRACT.md` | Immutable rules — requires ADR to change | Immutable (with ADR exception) |
| Review cycle reports | `docs/audit/CYCLE{N}_REVIEW.md` | Phase-by-phase review findings | Append-only; never edited after creation |
| ADRs | `docs/adr/ADR{NNN}.md` | Architectural Decision Records | Append-only |
| Dev standards | `docs/dev-standards.md` | Code style, test strategy, observability conventions | Updated as team conventions evolve |

### CODEX_PROMPT.md — Required Fields

Every version of `CODEX_PROMPT.md` must contain:

```markdown
## Current State
- Phase: {N}
- Baseline: {N} passing tests
- Ruff: clean | N issues
- Last CI: green | red

## Next Task
{T-NN: task name}

## Fix Queue
{list of deferred items, or "empty"}

## Open Findings
{list of P1/P2 findings from last review cycle, or "none"}

## Completed Tasks
{sequential list}
```

### tasks.md — Task Contract Format

Each task in `tasks.md` must specify:

```markdown
## T{NN}: {Task Name}

Owner: codex
Phase: {N}
Depends-On: T{XX}, T{YY}

### Objective
{One-paragraph description of what this task accomplishes}

### Acceptance Criteria
- [ ] {Specific, testable criterion}
- [ ] {Specific, testable criterion}

### Files
- Create: {list}
- Modify: {list}

### Notes
{Implementation hints, interface contracts, edge cases to handle}
```

Vague acceptance criteria produce vague implementations. "The endpoint works" is not an acceptance criterion. "GET /items returns 200 with `{"items": [...]}` when the tenant has items, 200 with `{"items": []}` when empty, and 404 when the tenant does not exist" is an acceptance criterion.
