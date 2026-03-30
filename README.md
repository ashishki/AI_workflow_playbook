# AI Workflow Playbook

A structured AI-assisted development workflow with hard quality guarantees. It provides prompts, templates, and enforcement mechanisms for building AI systems with explicit artifacts, review loops, and fit-for-purpose governance.

---

## Why This Playbook Is Different

Most "AI coding" workflows are a single prompt → single agent → hope for the best. This one is an engineering system with hard guarantees:

**Strict role separation.** The Orchestrator never writes code. The implementation agent never reviews its own output. Review agents never write code. These are not conventions — they are enforced rules with explicit rationale.

**Resumable state.** `docs/CODEX_PROMPT.md` is the single source of truth for all session state. Any agent, any session, any machine can resume exactly where the last one stopped. Nothing is held in conversational memory.

**Immutable contract.** `IMPLEMENTATION_CONTRACT.md` is the unchanging floor of the project. It does not evolve without an explicit ADR. This prevents incremental erosion of quality standards across phases.

**Structured task format.** Every task in `docs/tasks.md` follows a YAML-compatible block schema: `Owner`, `Phase`, `Type`, `Depends-On`, `Objective`, `Acceptance-Criteria` (each entry has `id`, `description`, and a `test:` field pointing to a specific test function), `Files`, `Notes`. The Orchestrator reads task fields directly without LLM parsing. A criterion without a test reference is a PHASE1_VALIDATOR blocker.

**Two-tier review.** Every task gets a lightweight 6-check security/contract review immediately after implementation. Every phase gets a deep four-agent review cycle: META → ARCH → CODE → CONSOLIDATED. The two tiers serve different purposes and neither replaces the other.

**Baseline tracking with enforcement.** After Phase 1, the passing test count is recorded as the baseline. Every subsequent session must not decrease it. A session that breaks tests must not commit — this is a hard rule.

**Finding lifecycle enforcement.** P2 findings that survive three review cycles without resolution are escalated, closed with justification, or deferred to v2. Findings cannot accumulate indefinitely.

**CI in Phase 1.** CI is mandatory in Phase 1. There is never a moment in this workflow when "tests pass locally but CI is unknown."

**Five capability profiles.** Optional architectural modes, each with algorithmic decision criteria, mandatory artifacts, profile-specific contract rules, deep-review checks, and an evaluation artifact:

| Profile | Governs | Review checks | Evaluation artifact |
|---------|---------|---------------|---------------------|
| **RAG** | Document retrieval: ingestion pipeline, query-time retrieval, `insufficient_evidence` path | RET-1..7 | `retrieval_eval.md` |
| **Tool-Use** | LLM-directed tool calls: schemas, side effects, unsafe-action gates, idempotency | TOOL-1..5 | `tool_eval.md` |
| **Agentic** | Multi-step decision loops: roles, authority boundaries, loop termination contract | AGENT-1..5 | `agent_eval.md` |
| **Planning** | Structured plan output as primary deliverable: schema, validation gate, plan-to-execution contract | PLAN-1..4 | `plan_eval.md` |
| **Compliance** | Regulated industries (HIPAA, SOC 2, PCI-DSS, GDPR): PHI enforcement, audit log, retention policy, evidence collection | COMP-1..5 | `compliance_eval.md` |

Profiles are activated in Phase 1 and treated as architectural constraints. Evaluation is enforced at Step 3.5: any task with a capability tag is not complete until the evaluation artifact is updated and compared against its baseline. A regression is a P1 finding.

**Capability auto-detection.** Pre-implementation: the Orchestrator matches the task's file scope against capability signal patterns — `retrieval/`, `embedding` → RAG; `tools/`, `@tool` → Tool-Use; `compliance/`, `audit/`, `hipaa/` → Compliance. A HIGH-confidence match with no matching `Type:` tag stops the session with a `TAG_WARNING` before any code is written. Post-implementation: file-vs-tag mismatches surface a `SEMANTIC_MISMATCH` to the reviewer.

**Domain skeletons.** Pre-built task sets for specific regulated domains that drop into `docs/tasks.md` directly. The HIPAA skeleton (`templates/domains/healthcare.md`) provides four tasks — PHI field enforcement, audit log infrastructure, retention policy enforcement, compliance evidence collection — each with complete acceptance criteria, test function references, and a starter `compliance_eval.md`. The Strategist includes it automatically when Compliance=ON and HIPAA is the active framework.

**Three-layer observability.** (1) Process level: Claude Code hooks block writes to immutable files, log every Bash command, write a session checkpoint on stop. (2) Production level: OBS-1..3 rules in `IMPLEMENTATION_CONTRACT.md` (spans, metrics, health endpoint) enforced by CODE review checks. (3) AI quality level: capability evaluation artifacts, Step 3.5 regression detection (>5% → P1, >15% → P0 Stop-Ship), optional CI eval gates. See `PLAYBOOK.md §12`.

---

## What This Playbook Is

A workflow for building AI-assisted software without assuming one default architecture. The Orchestrator runs the loop; Codex implements tasks in isolation; review agents check output at two tiers; the human approves phase gates. State lives in files, so sessions are resumable.

This playbook is intentionally not "agent-everywhere" and not "VM-by-default". It is designed to help teams choose the minimum sufficient solution shape, runtime substrate, and governance level for the actual risk and autonomy of the system.

---

## Freedom Ladder

The playbook treats AI system shape as a spectrum:

| Shape | Use when | Avoid when |
|------|----------|------------|
| **Deterministic subsystem** | Rules, routing, validation, permissions, calculations, thresholds, formatting, retries, audit triggers are already formalizable | You are adding an LLM only because it feels flexible |
| **Workflow orchestration** | The steps are known, ordered, and reviewable; tools and humans can be composed without open-ended planning | You need adaptive multi-step reasoning beyond a fixed flow |
| **Bounded ReAct / tool-using agent** | The system must choose among tools or iterate briefly under explicit limits | A workflow or deterministic router already solves it |
| **Higher-autonomy agent** | The task genuinely requires longer-horizon planning, delegation, or mutable execution under stronger controls | The same job can be decomposed into bounded workflow + deterministic guards |
| **Hybrid** | Different subsystems need different levels of freedom | You are using one architecture everywhere for convenience |

Then choose governance proportionally:

| Level | Typical fit | Expected control intensity |
|------|-------------|----------------------------|
| **Lean** | Internal assistant, prototype, low-blast-radius workflow | Core artifacts, task discipline, light controls, human approval at meaningful boundaries |
| **Standard** | Measurable internal operational system, customer-facing but recoverable service | Full phase gates, evaluation artifacts where applicable, stronger review and audit traceability |
| **Strict** | Business-critical, compliance-heavy, or high-blast-radius system | Tight change control, stronger approval boundaries, explicit evidence, stronger runtime and recovery controls |

Runtime is separate from agent shape. An agent is not a VM. VM or microVM isolation is optional and justified only when autonomy, mutability, privilege, or blast radius require it.

| Tier | Meaning | Typical use |
|------|---------|-------------|
| **T0** | Deterministic or managed execution with no special isolated mutable runtime | API logic, validators, fixed workflows, managed integrations |
| **T1** | Container / devcontainer / bounded worker runtime | Normal app services, bounded tool execution, standard CI and workers |
| **T2** | Ephemeral microVM-class or similarly isolated mutable runtime | Risky autonomous tasks that may modify workspace, shell state, or toolchain and need strong rollback |
| **T3** | Persistent VM-class or privileged long-lived isolated worker | Long-running autonomous workers with persistence, higher privilege surface, or stronger recovery needs |

Use this playbook by asking, in order:

1. Start with the minimum sufficient architecture, not the most impressive one.
2. Ask "why not deterministic?" before enabling LLM logic.
3. Ask "why not workflow?" before enabling bounded or open-ended agency.
4. Turn capability profiles ON only when they govern real behavior, not speculative future scope.
5. Keep runtime at T0/T1 unless there is a concrete isolation or mutability reason to escalate.
6. Increase governance only when error cost, auditability, or blast radius justify it.

Every rule and template addresses a concrete failure mode: silent quality erosion across phases, evaluation that never runs, review that misses profile-specific risks, compliance requirements that fall through to free-form LLM reasoning.

---

## The Loop

```
Project description
        |
        v
  [Strategist agent]
  Produces: ARCHITECTURE.md, spec.md, tasks.md (structured format),
            CODEX_PROMPT.md, IMPLEMENTATION_CONTRACT.md, ci.yml,
            + profile-specific artifacts (compliance_eval.md, nfr.md, etc.)
        |
        v
  [Phase 1 Validator]
  Structural and consistency checks across the Phase 1 artifact set before implementation begins
  PHASE1_AUDIT: PASS | FAIL
        |
        v
  [Orchestrator session]
  Reads CODEX_PROMPT.md before every task
  Step 0-E: capability signal detection → TAG_WARNING + STOP if mismatch
  Spawns Codex for implementation
  Step 3: semantic mismatch check (non-blocking)
  Step 3.5: evaluation gate (if capability tag) — regression → P1
        |
        v
  [Review cycle] (after each phase)
  META → ARCH → CODE → CONSOLIDATED
  CODE fires profile-specific checks: RET-N / TOOL-N / AGENT-N / PLAN-N / COMP-N
        |
        v
  Phase gate: all P1s resolved, ruff clean, tests pass, human approves
        |
        v
  Next phase — repeat
```

---

## Repo Structure

```
AI_workflow_playbook/
├── README.md
├── PLAYBOOK.md                      — master workflow document (read this first)
├── prompts/
│   ├── STRATEGIST.md                — architecture-generation agent prompt
│   ├── ORCHESTRATOR.md              — development orchestrator prompt
│   ├── PHASE1_VALIDATOR.md          — pre-implementation artifact validator
│   ├── PROMPT_S_STRATEGY.md         — phase-boundary strategy reviewer prompt
│   └── audit/
│       ├── PROMPT_0_META.md         — review: meta-analysis
│       ├── PROMPT_1_ARCH.md         — review: architecture drift
│       ├── PROMPT_2_CODE.md         — review: code & security (SEC + profile checks)
│       ├── PROMPT_3_CONSOLIDATED.md — review: consolidated report
│       └── AUDIT_INDEX.md           — audit index template
├── hooks/
│   ├── guard_files.sh               — PreToolUse: blocks writes to immutable files
│   ├── log_bash.sh                  — PostToolUse: audit log for Bash + Codex results
│   └── save_checkpoint.sh           — Stop: writes Orchestrator state snapshot
├── templates/
│   ├── ARCHITECTURE.md              — system architecture document template
│   ├── CODEX_PROMPT.md              — session handoff template (all 5 profile state blocks)
│   ├── IMPLEMENTATION_CONTRACT.md   — immutable rules template (universal + profile rules)
│   ├── PROJECT_BRIEF.md             — input template for the Strategist
│   ├── RETRIEVAL_EVAL.md            — RAG evaluation artifact template
│   ├── NFR.md                       — non-functional requirements template (SLA table + history)
│   ├── tasks_schema.md              — YAML-compatible task block schema, tag namespace, AC rules
│   ├── domains/
│   │   └── healthcare.md            — HIPAA skeleton: T-HC-01..04 with full AC + test refs
│   └── .claude/
│       └── settings.json            — Claude Code hook configuration
├── ci/
│   └── ci.yml                       — GitHub Actions template (lint, tests, all 5 eval steps, NFR load test)
└── reference/
    └── CODEX_CLI.md                 — Codex CLI patterns, sandbox limitations, pre-run checklist
```

### What each file is for

**PLAYBOOK.md** is the master document. Read it before anything else. It defines the phase structure, right-sizing logic, runtime selection, capability profiles, task execution protocol, review cycle, and universal rules.

**prompts/STRATEGIST.md** is the system prompt for the architecture-generation session. It reads your project description and produces the complete starter package. It forces explicit decisions about solution shape, rejected simpler alternatives, runtime tier, deterministic decomposition, human approval boundaries, and capability profiles.

**prompts/ORCHESTRATOR.md** runs the development loop — capability signal detection (Step 0-E), complexity/runtime drift checks, Codex dispatch, evaluation gate (Step 3.5), and phase gate enforcement.

**prompts/PHASE1_VALIDATOR.md** runs once, after the Strategist produces deliverables and before T01 begins. It checks structural completeness and cross-document consistency across the Phase 1 artifact set. Any blocker stops implementation.

**prompts/audit/PROMPT_2_CODE.md** is the code review prompt. It fires SEC-N (universal), profile-conditional RET-N / TOOL-N / AGENT-N / PLAN-N / COMP-N checks, and OBS-N (observability) on every deep review cycle.

**templates/tasks_schema.md** defines the task block format. Every task in `docs/tasks.md` must use this schema — `Type:` tag, structured `Acceptance-Criteria` entries each with a `test:` pointer, explicit `Depends-On`. The Orchestrator reads these fields directly; a missing `test:` field is a PHASE1_VALIDATOR blocker.

**templates/ARCHITECTURE.md** now requires solution shape, governance level, runtime tier, deterministic-vs-LLM ownership, human approval boundaries, and anti-overengineering non-goals.

**templates/PROJECT_BRIEF.md** is the recommended input template before running the Strategist. It helps you describe goals, workflows, risks, AI scope, deterministic candidates, human approval boundaries, constraints, and success metrics without pre-deciding the architecture.

**templates/domains/healthcare.md** is the HIPAA domain skeleton. It provides four production-ready tasks with complete acceptance criteria (including specific test function references), a starter `docs/compliance_eval.md` table with HIPAA control rows, and ARCHITECTURE.md snippets. The Strategist includes it verbatim when Compliance=ON and HIPAA is the active framework.

**templates/NFR.md** tracks non-functional SLAs: target, measurement method, CI gate threshold, and a phase-by-phase baseline history. Included when the project has explicit latency, throughput, or error rate requirements.

**ci/ci.yml** has five commented capability eval steps (RAG, Agentic, Tool-Use, Planning, Compliance) and a commented NFR load test step (locust). Uncomment the steps for your active profiles.

**reference/CODEX_CLI.md** documents real operational knowledge: file-based prompt invocation, known sandbox limitations (async DB hangs, heavy ML deps), prompt engineering patterns.

---

## How to Start a New Project

1. Open a Claude session (Claude.ai or Claude Code).
2. Set `prompts/STRATEGIST.md` as the system prompt.
3. Fill `templates/PROJECT_BRIEF.md` or describe the same fields in chat: domain, workflows, AI scope, deterministic candidates, expected scale, constraints, risk boundaries, and compliance requirements.
4. The Strategist asks clarifying questions, then produces the starter package:
   - `docs/ARCHITECTURE.md`, `docs/spec.md`, `docs/tasks.md`
   - `docs/CODEX_PROMPT.md`, `docs/IMPLEMENTATION_CONTRACT.md`
   - `.github/workflows/ci.yml`
   - Review prompts: `docs/audit/PROMPT_0_META.md` through `PROMPT_3_CONSOLIDATED.md`, `docs/audit/AUDIT_INDEX.md`
   - If Compliance=ON: `docs/compliance_eval.md` (with framework-specific control rows)
   - If NFR constraints stated: `docs/nfr.md` (with SLA table)
5. Copy `prompts/ORCHESTRATOR.md` to `your-project/docs/prompts/ORCHESTRATOR.md`, fill `{{PROJECT_ROOT}}` and `{{CODEX_COMMAND}}`.
6. Copy hooks and settings:
   ```bash
   cp -r hooks/ your-project/hooks/
   mkdir -p your-project/.claude/
   cp templates/.claude/settings.json your-project/.claude/settings.json
   chmod +x your-project/hooks/*.sh
   ```
7. Run the Phase 1 Validator before starting implementation:
   - Open a Claude session with `prompts/PHASE1_VALIDATOR.md` as the prompt
   - Point it at your 6 starter artifacts
   - It produces `docs/audit/PHASE1_AUDIT.md` (74 checks across 6 artifacts) — resolve all BLOCKERs before proceeding
8. Open a Claude Code session with `docs/prompts/ORCHESTRATOR.md` as the system prompt.
9. Say: "Start Phase 1." The Orchestrator reads `docs/CODEX_PROMPT.md` and begins.

The human sits at every phase gate. From there, the loop runs itself.
