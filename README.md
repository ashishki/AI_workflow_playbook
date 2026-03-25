# AI Workflow Playbook

A distilled AI-assisted development workflow extracted from the [gdev-agent](https://github.com/ashishki/gdev-agent) project. This playbook provides the structure, prompts, and templates needed to replicate that workflow on any new project.

---

## Why This Playbook Is Different

Most "AI coding" workflows are a single prompt → single agent → hope for the best. This one is an engineering system with hard guarantees:

**Strict layer separation.** Seven layers, each with defined inputs, outputs, and hard boundaries. The Orchestrator never writes application code. The implementation agent never reviews its own output. Review agents never write code. These are not conventions — they are enforced rules with explicit rationale.

**Stateless orchestration.** `docs/CODEX_PROMPT.md` is the single source of truth for all session state. Any agent, any session, any machine can resume exactly where the last one stopped by reading that file. Nothing is held in conversational memory. Sessions are fully resumable after interruption.

**Immutable contract.** `IMPLEMENTATION_CONTRACT.md` is the unchanging floor of the project. Architectural decisions may evolve; the contract does not — without an explicit ADR. This prevents incremental erosion of quality standards across phases.

**Two-tier review, not one pass.** Every task gets a lightweight 6-check security/contract review immediately after implementation. Every phase gets a deep four-agent review cycle: META (process compliance) → ARCH (architecture compliance) → CODE (P0–P3 findings) → CONSOLIDATED (merged report). The two tiers serve different functions and neither replaces the other.

**Baseline tracking with enforcement.** After Phase 1, the passing test count is recorded. Every subsequent session must not decrease it. A session that breaks tests must not commit — this is a hard rule, not a guideline.

**Finding lifecycle enforcement (P2 Age Cap).** P2 findings that survive three review cycles without resolution are escalated, closed with justification, or deferred to v2. Findings cannot accumulate indefinitely. The audit trail is append-only.

**CI in Phase 1, not Phase 3.** CI is mandatory in Phase 1. There is never a moment in this workflow when "tests pass locally but CI is unknown."

**Capability Profiles with enforced evaluation.** Optional architectural modes that extend the base workflow with profile-specific artifacts, review checks, state tracking, and evaluation criteria. Four profiles are supported: **RAG** (document retrieval), **Tool-Use** (LLM-directed tool calls), **Agentic** (multi-step decision loops), **Planning** (structured plan output). RAG is the reference implementation with the most detailed worked example. Each active profile adds its own architecture section, contract rules, review checks, and an evaluation artifact (`retrieval_eval.md`, `tool_eval.md`, etc.). Evaluation is not optional — the Orchestrator enforces it as Step 3.5: whenever a task carries a capability tag (`rag:query`, `tool:schema`, `agent:loop`, etc.), the task is not complete until the evaluation artifact is updated and compared against its baseline. A regression blocks task completion and becomes a P1 finding. For the RAG profile specifically, evaluation covers two independent dimensions: retrieval quality (hit@k, MRR, citation precision) and answer quality (faithfulness, completeness, relevance via LLM judge). Each profile now has a full set of deep-review checks: **RET-N** (7 checks) for RAG, **TOOL-N** (5 checks) for Tool-Use, **AGENT-N** (5 checks) for Agentic, **PLAN-N** (4 checks) for Planning. These run at every phase-boundary deep review alongside the baseline SEC+QUAL+CF checks.

**Capability auto-detection and semantic validation.** Two mechanisms that catch tagging errors before and after implementation. Pre-implementation (Step 0-E): the Orchestrator matches the task's file scope against a table of capability signal patterns (e.g. `retrieval/`, `embedding` → RAG; `tools/`, `@tool` → Tool-Use). A HIGH-confidence match with no corresponding `Type:` tag stops the session with a `TAG_WARNING` before any code is written. Post-implementation (Step 3): if Codex's actual modified files match a different profile than the task tag, a `SEMANTIC_MISMATCH` is surfaced to the light reviewer (non-blocking). Profile-conditional light review checks fire automatically based on the task tag — `RAG-L1/L2` for retrieval tasks, `TOOL-L1` for unsafe tools, `AGENT-L1` for loops, `PLAN-L1` for planning tasks — expanding the standard 6-check SEC+CF checklist without requiring a full deep review. Four worked scenarios in `PLAYBOOK.md §Capability Check Scenarios` define exact expected outputs including a negative control (no overfiring on unrelated files) and a mixed-profile case (semantic ownership + additive checks).

**Operational reference for the implementation agent.** `reference/CODEX_CLI.md` documents real-world Codex CLI behavior: known sandbox limitations (async DB hangs, heavy ML deps), prompt engineering patterns, and a pre-run checklist. This knowledge was learned through failures; it is not theoretical.

**Proven on a real project.** Every rule was validated through 12 phases of building gdev-agent — a production multi-tenant AI triage service. The reference implementation exists and is public.

---

## What This Playbook Is

This playbook captures the exact development process used to build gdev-agent — a multi-tenant AI triage service built over 12 phases using Claude as both the implementation agent and the reviewer. The workflow is general enough to apply to any backend service; the templates and prompts are project-agnostic starting points.

The playbook is not theoretical. Every rule, every template, and every prompt was validated through real phases on a real project. The reference implementation at https://github.com/ashishki/gdev-agent is the living proof of concept.

---

## The Loop

```
PLAYBOOK.md + project description
        |
        v
  [Strategist agent]
  Reads PLAYBOOK.md and STRATEGIST.md prompt
  Produces: ARCHITECTURE.md, spec.md, tasks.md,
            CODEX_PROMPT.md, IMPLEMENTATION_CONTRACT.md, ci.yml
        |
        v
  [Orchestrator session]
  Reads CODEX_PROMPT.md before every task
  Spawns Codex subagents for implementation
  Each Codex agent: captures baseline → implements → tests → evaluates (if capability tag) → commits
        |
        v
  [Capability tag check — Step 0-E / Step 3]
  Pre-impl:  file scope vs. signal patterns → TAG_WARNING + STOP if mismatch (HIGH confidence)
  Post-impl: modified files vs. tag → SEMANTIC_MISMATCH surfaced to reviewer (non-blocking)
        |
        v
  [Evaluation gate — Step 3.5] (if task has capability tag)
  Orchestrator verifies Codex updated the evaluation artifact
  Regression detected → P1 finding, task not complete
  Missing evaluation → focused remediation prompt back to Codex (not a new agent)
        |
        v
  [Review cycle] (after each phase)
  META review   → process compliance
  ARCH review   → architectural compliance
  CODE review   → detailed code findings (P0/P1/P2/P3)
  CONSOLIDATED  → merged report saved to docs/audit/
        |
        v
  Phase gate: all P1s resolved, ruff clean, tests pass
        |
        v
  Next phase — repeat
```

The human sits at every phase gate. Agents implement and review; the human approves before the next phase begins.

---

## Repo Structure

```
AI_workflow_playbook/
├── README.md                   — this file
├── PLAYBOOK.md                 — master workflow document (read this first)
├── prompts/
│   ├── STRATEGIST.md           — system prompt for the architecture-generation agent
│   ├── ORCHESTRATOR.md         — system prompt for the development orchestrator session
│   ├── PHASE1_VALIDATOR.md     — Phase 1 completeness validator prompt
│   ├── PROMPT_S_STRATEGY.md    — phase-boundary strategy reviewer prompt (template)
│   └── audit/
│       ├── PROMPT_0_META.md    — review pipeline: meta-analysis (template)
│       ├── PROMPT_1_ARCH.md    — review pipeline: architecture drift (template)
│       ├── PROMPT_2_CODE.md    — review pipeline: code & security (template)
│       ├── PROMPT_3_CONSOLIDATED.md — review pipeline: consolidated report (template)
│       └── AUDIT_INDEX.md      — audit index template
├── templates/
│   ├── ARCHITECTURE.md         — template for system architecture document
│   ├── CODEX_PROMPT.md         — template for session handoff document
│   ├── IMPLEMENTATION_CONTRACT.md — template for immutable rules document
│   └── RETRIEVAL_EVAL.md       — RAG evaluation artifact template (copy to docs/ when RAG=ON)
├── ci/
│   └── ci.yml                  — GitHub Actions CI template
└── reference/
    ├── GDEV_AGENT.md           — how to use gdev-agent as implementation reference
    └── CODEX_CLI.md            — Codex CLI invocation patterns, sandbox limitations, prompt engineering
```

### What each file is for

**PLAYBOOK.md** is the master document. Read it before anything else. It defines the philosophy, phase structure, task execution protocol, review cycle structure, and all universal rules.

**prompts/STRATEGIST.md** is the system prompt you give to a Claude session when starting a new project. The agent reads your project description and produces all the starter documents.

**prompts/ORCHESTRATOR.md** is the system prompt for the Claude Code session that runs the development loop — spawning Codex agents, running reviews, and enforcing phase gates.

**prompts/PROMPT_S_STRATEGY.md** is the phase-boundary strategy reviewer prompt. At every phase gate, the Orchestrator spawns a Strategy Reviewer agent with this prompt. It reads ARCHITECTURE.md, open findings, ADRs, and the upcoming phase tasks, then issues a Proceed or Pause recommendation before implementation begins.

**prompts/audit/** contains the four deep-review prompt templates (META → ARCH → CODE → CONSOLIDATED) and the AUDIT_INDEX template. The Strategist copies these into your project's `docs/audit/` at project creation, filling in the project name. The Orchestrator's review agents read them from there at runtime.

**templates/** contains starting-point documents with `{{PLACEHOLDER}}` markers. The Strategist agent fills these in for your specific project. `RETRIEVAL_EVAL.md` is copied to `docs/retrieval_eval.md` when the RAG profile is activated; it tracks retrieval metrics, answer quality metrics, query type coverage, corpus versioning, and evaluation history.

**ci/ci.yml** is a GitHub Actions template that mirrors the pattern proven in gdev-agent.

**reference/GDEV_AGENT.md** explains which parts of gdev-agent to study when you need a concrete implementation example.

**reference/CODEX_CLI.md** documents hard-won operational knowledge about running Codex as the implementation agent: the file-based prompt invocation pattern, known sandbox limitations (async DB hangs, heavy ML deps), prompt engineering guidelines, and a pre-run checklist. Read this before starting a project that uses the Codex CLI.

**Capability Profiles** (`PLAYBOOK.md §2c`) — optional architectural modes activated in Phase 1. When a profile is ON, it extends the workflow with profile-specific artifacts, review checks (RET-N / TOOL-N / AGENT-N / PLAN-N), state tracking, and an evaluation artifact. Each profile must satisfy the 9-property invariant defined in §2c before activation. The section also contains the Capability Signal Patterns table (file path → profile inference), the Semantic Ownership Rule (RAG beats Tool-Use for retrieval tasks), the Additive Checks Rule (Agentic + Tool-Use checks are cumulative), and four worked Capability Check Scenarios with a shared workflow effect vocabulary (BLOCK / TASK_NOT_COMPLETE / LIGHT_REVIEW_EXPANDED / DEEP_REVIEW_EXPANDED).

---

## How to Start a New Project

1. Open a Claude session (Claude.ai or Claude Code).
2. Attach or paste:
   - The contents of `PLAYBOOK.md`
   - The contents of `prompts/STRATEGIST.md` as the system prompt
3. Describe your project: domain, stack preferences, expected scale, team size, key constraints.
4. The Strategist produces **13 files** — save them all into your new repo:
   - `docs/ARCHITECTURE.md`, `docs/spec.md`, `docs/tasks.md`
   - `docs/CODEX_PROMPT.md`, `docs/IMPLEMENTATION_CONTRACT.md`
   - `.github/workflows/ci.yml`
   - `docs/prompts/ORCHESTRATOR.md` (stub — copy full `prompts/ORCHESTRATOR.md` from this playbook and fill `{{PROJECT_ROOT}}` and `{{CODEX_COMMAND}}`)
   - `docs/prompts/PROMPT_S_STRATEGY.md`
   - `docs/audit/PROMPT_0_META.md` through `PROMPT_3_CONSOLIDATED.md`
   - `docs/audit/AUDIT_INDEX.md`
5. Open a Claude Code session in your new repo with `docs/prompts/ORCHESTRATOR.md` as the system prompt.
6. Say: "Start Phase 1." The orchestrator reads `docs/CODEX_PROMPT.md` and begins.

That's the entire startup sequence. From there, the loop runs itself with you approving phase gates.

---

## Reference Implementation

**https://github.com/ashishki/gdev-agent**

gdev-agent is a FastAPI / PostgreSQL (pgvector) / Redis / Claude API service built using this exact playbook over 12 phases. When a prompt says "see the reference implementation," it means this repo.

Key things to study in gdev-agent:
- `docs/CODEX_PROMPT.md` — see what a real session handoff looks like at mid-project
- `docs/audit/` — see what actual review cycle reports look like
- `app/services/` — the service layer pattern
- `app/tracing.py` — the shared tracing module pattern
- `tests/conftest.py` — fixture structure

See `reference/GDEV_AGENT.md` for a detailed guide to which files to read and why.
