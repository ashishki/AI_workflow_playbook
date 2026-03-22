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

## 1b. System Architecture — Layer Map

The workflow has seven layers. Each layer has a defined purpose, defined outputs, and a hard boundary with adjacent layers. Layers never cross into each other's responsibility.

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: PLANNING                                               │
│  Strategist agent reads project description → produces all       │
│  Phase 1 artifacts before any code is written.                   │
│  Outputs: ARCHITECTURE.md, spec.md, tasks.md, CODEX_PROMPT.md,  │
│           IMPLEMENTATION_CONTRACT.md, CI workflow                │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  LAYER 2: ORCHESTRATION                                          │
│  Orchestrator reads state from files → decides action →          │
│  spawns agents → updates state → loops.                          │
│  Stateless across sessions. All state lives in files.            │
│  Output: Loop control, subagent invocations, state transitions   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  LAYER 3: IMPLEMENTATION (Codex)                                 │
│  One task at a time. Reads exact file list. Writes code + tests. │
│  Never self-reviews. Never touches adjacent tasks.               │
│  Output: Code changes + tests + CODEX_PROMPT.md patch + commit   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  LAYER 4: REVIEW (Two-Tier)                                      │
│  Tier 1 — Light: 1 agent, 6 security/contract checks per task    │
│  Tier 2 — Deep:  META → ARCH → CODE → CONSOLIDATED per phase     │
│  Output: Findings (P0/P1/P2/P3), REVIEW_REPORT.md, Fix Queue    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  LAYER 5: QUALITY LOOP                                           │
│  Baseline tracking (tests must not decrease).                    │
│  P2 Age Cap (3-cycle limit → escalate, close, or defer to v2).  │
│  Append-only audit trail in docs/audit/.                         │
│  Output: Quality trend signal, finding lifecycle enforcement     │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  LAYER 6: AUDIT / TRACEABILITY                                   │
│  CODEX_PROMPT.md: immutable session state across interruptions.  │
│  IMPLEMENTATION_CONTRACT.md: immutable rules (ADR required).     │
│  ADRs: append-only architectural decisions.                      │
│  docs/audit/CYCLE{N}_REVIEW.md: append-only findings trail.     │
│  Typed commits: one logical change, one commit, traceable.       │
│  Output: Full reconstruct of any session from files alone        │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  LAYER 7: RUNTIME / CI                                           │
│  GitHub Actions CI: lint + format + tests on every commit.       │
│  Environment contract in ARCHITECTURE.md §Runtime Contract.      │
│  Services (PostgreSQL, Redis, etc.) declared in ci.yml.          │
│  Output: Green/red signal per commit, baseline verification      │
└─────────────────────────────────────────────────────────────────┘
```

### Layer Boundaries — Hard Rules

| Rule | Why |
|------|-----|
| Implementation never reviews its own output | The Codex agent that writes the code never runs the review agents |
| Review never writes code | Review agents produce findings; Codex fixes them |
| Orchestrator never writes application code | It reads, decides, and spawns — no direct file edits in app/ |
| Planning precedes implementation | Phase 1 (Layer 1) must be complete before Layer 3 begins |
| CI gate is a layer boundary | No PR crosses from Layer 3 to Layer 4 if CI is red |

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

## 2c. Capability Profiles

A Capability Profile is an optional architectural mode that can be activated during Phase 1. Each profile extends the base workflow with profile-specific artifacts, rules, review checks, state tracking, and evaluation criteria.

### The 9-Property Profile Invariant

Every Capability Profile must define all nine of the following properties. A profile that omits any property is incomplete and must not be activated.

| # | Property | What it covers |
|---|----------|----------------|
| 1 | **Decision Gate** | Explicit ON/OFF criteria in Phase 1 (Strategist decision) |
| 2 | **Architecture Sections** | Additional sections in `docs/ARCHITECTURE.md` when ON |
| 3a | **Spec Sections** | Additional sections in `docs/spec.md` when ON |
| 3b | **Task Type Namespace** | Profile-scoped task tags (e.g. `rag:ingestion`, `rag:query`) |
| 4 | **Implementation Contract Rules** | `## Profile Rules: {name}` section in `IMPLEMENTATION_CONTRACT.md` |
| 5 | **Orchestrator Behavior** | How the orchestrator detects and reacts to active profile and profile task tags |
| 6 | **Profile State Block** | `## Profile State: {name}` block in `CODEX_PROMPT.md` |
| 7 | **Audit Extensions** | Conditional check blocks in `PROMPT_1_ARCH.md` and `PROMPT_2_CODE.md` |
| 8 | **Evaluation Artifact** | A dedicated evaluation document with its own lifecycle (e.g. `docs/retrieval_eval.md`) |

Profiles are declared in the `## Capability Profiles` table in `docs/ARCHITECTURE.md`. The table is machine-readable by the orchestrator and extensible — adding a profile means adding a row, not editing a flat field.

**RAG is the reference implementation of this pattern.** The RAG-specific sections below show what each property looks like in practice.

---

### Profile: RAG

RAG (Retrieval-Augmented Generation) is **not a default requirement**. It is an optional architectural mode that the Strategist must explicitly enable or disable during Phase 1. Its evaluation artifact is `docs/retrieval_eval.md`.

#### RAG Status: ON | OFF

The Strategist declares the RAG status in the `## Capability Profiles` table in `docs/ARCHITECTURE.md`:

```
| RAG | ON  | docs/retrieval_eval.md | project uses retrieval-backed architecture |
| RAG | OFF | docs/retrieval_eval.md | project does not use retrieval; standard prompting only |
```

This decision is made once, in Phase 1, and treated as an architectural constraint for all subsequent phases. Changing it requires an ADR.

#### When to Turn RAG ON

Turn RAG Profile ON when one or more of the following is true:

| Signal | Example |
|--------|---------|
| Large document/corpus context that does not fit in a prompt | Policy manuals, legal documents, multi-volume runbooks |
| Knowledge that changes faster than the code deploy cycle | Frequently updated FAQs, live regulations, evolving product catalogs |
| Citations or evidence are required in the output | Answers must reference source documents with traceability |
| Document-heavy sources | PDFs, markdown corpora, internal wikis, technical manuals |
| Retrieval needed not just for end-user chat but also for agent or tool context | An agent that must look up current pricing or policy before acting |

When none of these signals are present, RAG Profile is OFF. Do not add retrieval infrastructure speculatively.

#### Additional Artifacts When RAG Status = ON

If the Strategist declares RAG Status ON, the following additional artifacts must be produced in Phase 1:

| Artifact | Path | Purpose |
|----------|------|---------|
| RAG Architecture section | `docs/ARCHITECTURE.md §Profile: RAG > §RAG Architecture` | Ingestion pipeline, query-time pipeline, corpus description, index strategy |
| Retrieval spec section | `docs/spec.md §Retrieval` | What sources are indexed, update frequency, expected query types, citation requirements |
| RAG tasks | `docs/tasks.md` | Separate tasks for ingestion pipeline and query-time retrieval (never merged into a single task) |
| Retrieval acceptance criteria | `docs/tasks.md` (per task) | Retrieval-specific criteria: recall targets, latency bounds, insufficient-evidence path |
| Profile contract rules | `docs/IMPLEMENTATION_CONTRACT.md §Profile Rules: RAG` | Corpus isolation, schema versioning, stale-index handling policy |
| Profile state block | `docs/CODEX_PROMPT.md §Profile State: RAG` | Retrieval baseline, open retrieval findings, index schema version, pending reindex |
| Evaluation artifact | `docs/retrieval_eval.md` | Retrieval quality metrics with own lifecycle (separate from code quality) |

#### RAG Workflow Shape

When RAG Status = ON, the retrieval system has two distinct pipelines. These are separate responsibilities and must never be merged into a single task or service.

**Ingestion pipeline** (offline, scheduled, or event-driven):
```
extract → normalize → chunk → embed → index
```

**Query-time pipeline** (online, per-request):
```
query analyze → retrieve → rerank/filter → assemble evidence → answer | insufficient_evidence
```

The `insufficient_evidence` path is not optional. If the retrieved evidence does not support an answer, the system must return `insufficient_evidence` rather than hallucinating a response. This path must have an explicit acceptance criterion and a test.

#### Retrieval Quality is Evaluated Separately from Code Quality

Retrieval correctness cannot be verified by code review alone. When RAG Status = ON, the review cycle must include retrieval-specific checks:

- **Recall audit**: Does the system retrieve the right documents for representative queries?
- **Evidence assembly**: Is the assembled context coherent and relevant to the query?
- **Insufficient-evidence path**: Is the fallback path exercised in tests with queries that should not be answerable?
- **Index staleness**: Is there a defined maximum age for indexed documents? Is it enforced?
- **Corpus isolation**: If multi-tenant, are corpus boundaries enforced at the retrieval layer?

These checks are added to `PROMPT_2_CODE.md` (code review) and `PROMPT_1_ARCH.md` (architecture review) when RAG Status = ON.

#### RAG-Specific Risks

The following risks apply only to RAG-profile projects and must be documented in `docs/ARCHITECTURE.md §Profile: RAG > §Risks` when RAG Status = ON:

| Risk | Description | Mitigation |
|------|-------------|------------|
| Hallucination on weak evidence | Model answers confidently despite low-quality retrieval | Require confidence threshold; implement `insufficient_evidence` path |
| Schema drift | Embedding model or chunk format changes invalidate the index | Version the index schema; re-index on model change; enforce via ADR |
| Stale index | Indexed documents fall out of date silently | Define max index age; add staleness check to health endpoint |
| Corpus isolation failure | Retrieval crosses tenant or classification boundaries | Enforce corpus-level ACLs at the retrieval layer, not just application layer |
| Retrieval latency regression | Adding reranking or larger corpora degrades p95 latency | Set latency acceptance criteria per retrieval task; track in baseline |

#### Orchestrator Handling of RAG Work

When RAG Status = ON, the Orchestrator applies a **stricter review path** to retrieval-related tasks:

- All tasks tagged `rag:ingestion` or `rag:query` trigger a **deep review**, not just a light review, regardless of phase boundary.
- The ARCH review must explicitly verify corpus isolation and pipeline separation.
- The CODE review must verify the `insufficient_evidence` path is tested.
- P2 findings on retrieval components escalate to P1 at the next cycle (the Age Cap is reduced from 3 cycles to 1 cycle for retrieval-critical findings).

Tag retrieval tasks in `tasks.md` with a `Type:` field:

```markdown
Type: rag:ingestion   # ingestion pipeline tasks
Type: rag:query       # query-time retrieval tasks
```

The Orchestrator reads this tag to apply the stricter review path.

---

## 2b. Session Start Ritual — The Loop Mechanism

This is the mechanism that makes the workflow run autonomously without manual step-by-step prompting.

### The Problem It Solves

Without a structured session start, the developer acts as the orchestrator — manually triggering each step (implement, review, archive, doc update, phase report). Each pause is a gap where context is lost and steps get skipped.

With the ritual, the orchestrator drives the entire cycle from a single paste. The developer's only job is approving phase gates and resolving blockers.

### How It Works

Every session begins with a single action:

```
Paste the entire contents of docs/prompts/ORCHESTRATOR.md into Claude Code.
```

The orchestrator then:
1. Reads `docs/CODEX_PROMPT.md` and `docs/tasks.md` to determine current state
2. Prints an `=== ORCHESTRATOR STATE ===` block showing what it sees
3. Drives the full loop: Fix Queue → Strategy → Implement → Light Review → (if phase boundary) Deep Review → Archive → Doc Update → Phase Report → checkpoint → next task

No manual prompting is needed between steps. The orchestrator stops only when:
- A task is blocked `[!]` and needs human input
- A P0 finding cannot be resolved after 2 attempts
- All tasks are complete
- An API rate limit is hit (sends notification with resume time)

### What ORCHESTRATOR.md Must Contain

Every project's `docs/prompts/ORCHESTRATOR.md` must have all 7 steps filled in with project-specific values:

| Placeholder | What to replace with |
|---|---|
| Project name | Used in all agent system prompts |
| Project root | Absolute path on disk |
| Implementation agent command | `codex exec` or `Agent tool (general-purpose)` — whichever is available |
| Test command | `pytest tests/ -q` or `python3 -m unittest discover tests/ -q` |
| Lint command | `ruff check` or skip if not enforced |
| Notification channel | Telegram bot, Slack, desktop notify, or remove if not needed |

The template is in `prompts/ORCHESTRATOR.md` in this playbook. Copy it, fill the placeholders, commit it as `docs/prompts/ORCHESTRATOR.md` in your project.

### Required Audit Prompt Files

The deep review pipeline (Steps 4.0–4.3) references four prompt files that must exist in `docs/audit/`:

| File | Purpose |
|---|---|
| `PROMPT_0_META.md` | Snapshot current state, define review scope |
| `PROMPT_1_ARCH.md` | Check architectural drift vs spec + contracts |
| `PROMPT_2_CODE.md` | Security and quality checklist per file |
| `PROMPT_3_CONSOLIDATED.md` | Produce REVIEW_REPORT.md + patches for tasks.md and CODEX_PROMPT.md |
| `AUDIT_INDEX.md` | Running log of all review cycles and archive entries |

Templates for all five are in the `prompts/audit/` directory of this playbook.

### Retrofit for Existing Projects

If a project already has code but lacks the workflow scaffolding:

1. Create `docs/CODEX_PROMPT.md` with current baseline and open findings
2. Create `docs/IMPLEMENTATION_CONTRACT.md` with project-specific rules
3. Add `.github/workflows/ci.yml`
4. Copy and fill `docs/prompts/ORCHESTRATOR.md`
5. Copy audit prompt templates to `docs/audit/`
6. Create `docs/audit/AUDIT_INDEX.md` (start at Cycle 1)

After retrofit, paste ORCHESTRATOR.md and the loop runs identically to a greenfield project.

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

---

## 11. Known Gaps — v2 Roadmap

This section documents what the workflow does **not yet solve**. These are real limitations, not theoretical ones. They are documented here so future contributors know what is missing and why, rather than discovering it mid-project.

Each gap includes: what is missing, what impact it has, and the minimum viable addition that would close it.

---

### GAP-1: Single-Model Dependency (Claude only)

**What is missing:** The orchestrator has no model selection logic. All agents use Claude via the Anthropic API. There is no fallback model, no cost optimization by routing tasks to cheaper models, and no way to verify results by comparing outputs from two different models.

**Impact:** Medium. Switching providers or using GPT-4 for specific tasks (e.g., cost-sensitive code generation) requires rewriting orchestrator prompts. An Anthropic outage stops all agents.

**v2 addition:**
- Model selection policy in ORCHESTRATOR.md (e.g., "use Haiku for light review, Opus for deep review")
- Fallback routing: if primary model returns error, retry with fallback
- Cost tracking per model per task (see GAP-2)

---

### GAP-2: No Token / Cost Tracking

**What is missing:** The workflow tracks test baselines and finding severity, but not token consumption per task, cost per phase, or cost trends over time. There is no budget signal.

**Impact:** Low-Medium. Without cost tracking, a project with many phases cannot detect cost drift until the invoice arrives.

**v2 addition:**
- Log `input_tokens`, `output_tokens`, `cost_usd` in CODEX_PROMPT.md per task
- Phase cost summary in CONSOLIDATED review output
- Optional budget gate in phase gate criteria (e.g., "if phase cost > $X, human reviews before proceeding")

---

### GAP-3: Security Review Not Formalized as a Separate Layer

**What is missing:** Security checks are embedded in the CODE review agent (Tier 2) and the Light review checklist (Tier 1). There is no dedicated security review agent, no formal threat model document, and no security-specific audit index.

**Impact:** High for production systems. Security findings are mixed with quality findings in REVIEW_REPORT.md. A reviewer optimizing for code quality may miss a subtle auth bypass.

**v2 addition:**
- `docs/THREAT_MODEL.md` — formal threat model (assets, threat actors, attack vectors, mitigations)
- PROMPT_SECURITY agent in the deep review pipeline: focused exclusively on auth, injection, data leakage, privilege escalation, and secrets
- Security audit index: `docs/audit/SECURITY_AUDIT.md` — one row per security finding per cycle
- Security gate in phase gate criteria: all P1 security findings resolved before gate passes

---

### GAP-4: No Performance / Load Testing Integration

**What is missing:** The workflow requires functional tests (pytest) and lint (ruff). It has no performance gate — no load test suite, no latency SLA verification, no memory/CPU regression detection.

**Impact:** Low in Phases 1–3 (correctness matters more than performance). High in Phase 6+ when the system handles real traffic.

**v2 addition:**
- Load test suite (Locust or k6) in `load_tests/`
- Baseline performance metrics stored in CODEX_PROMPT.md (e.g., `p95_latency_ms: 180`)
- Performance gate in phase gate criteria (Phase 6+): p95 latency must not regress by more than 20% vs. baseline
- Performance findings in REVIEW_REPORT.md if regression detected

---

### GAP-5: No Production Incident Integration

**What is missing:** The workflow is entirely development-focused. There is no formal path for a production incident to enter the development loop. There is no hot-fix process, no post-deployment health check, and no incident-to-task conversion.

**Impact:** High for live systems. When production breaks, the team needs a fast path that bypasses the normal phase gate process without abandoning quality controls.

**v2 addition:**
- Hot-fix task type in tasks.md: `Type: hotfix`, bypasses strategy review and deep review, triggers light review only
- Incident template: `docs/incidents/INC-{NNN}.md` — what broke, what was the impact, root cause, task created
- Post-deploy smoke test in CI: a minimal health check run after deploy, result logged to CODEX_PROMPT.md
- Incident-to-task conversion: each incident produces exactly one task entry in tasks.md

---

### GAP-6: Advanced Quality Metrics (Coverage, Complexity)

**What is missing:** The workflow tracks test count and finding severity. It does not track test coverage percentage, code complexity (cyclomatic, cognitive), or documentation coverage.

**Impact:** Low. Test count is a reasonable proxy for quality in early phases. In later phases, a project can have 200 passing tests with 40% coverage — the tests are not representative.

**v2 addition:**
- Coverage gate in CI: `pytest --cov=app --cov-fail-under=80`
- Coverage trend in CODEX_PROMPT.md: `Coverage: 73% (+2% vs. last phase)`
- Complexity budget in ARCH review: "no function with cyclomatic complexity > 15 without documented justification"

---

### Summary Table

| Gap | Severity | Effort to Close | Priority |
|-----|----------|-----------------|----------|
| GAP-1: Single-model dependency | Medium | High (orchestrator redesign) | v2 |
| GAP-2: No cost tracking | Low-Medium | Low (add fields to CODEX_PROMPT) | v2 |
| GAP-3: Security not formalized | High | Medium (new agent + threat model) | v2 priority |
| GAP-4: No performance testing | Low→High | Medium (load test suite + gate) | Phase 6+ |
| GAP-5: No production integration | High | Medium (incident template + hotfix path) | pre-launch |
| GAP-6: No coverage/complexity metrics | Low | Low (pytest-cov + CI flag) | v2 |

**v2 priority order:** GAP-3 (security formalization) → GAP-5 (production integration) → GAP-2 (cost tracking) → GAP-6 (coverage) → GAP-4 (performance testing) → GAP-1 (multi-model)

_This section is updated at each major version of the playbook. Gaps that are closed move to the changelog._
