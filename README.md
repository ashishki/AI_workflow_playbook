# AI Workflow Playbook

A structured AI-assisted development workflow with hard quality guarantees. It provides prompts, templates, and enforcement mechanisms for building AI systems with explicit artifacts, review loops, and fit-for-purpose governance.

The current playbook is strongest when read as a layered system:

1. Policy / Governance
2. Proof / Evidence
3. Optional Execution Patterns
4. Harness / Packaging

This repository is not trying to become a generic orchestration framework. Its center of gravity remains governance, contracts, reviews, and auditable repo artifacts.

---

## Why This Playbook Is Different

Most "AI coding" workflows are a single prompt → single agent → hope for the best. This one is an engineering system with hard guarantees:

**Strict role separation.** The Orchestrator never writes code. The implementation agent never reviews its own output. Review agents never write code. These are not conventions — they are enforced rules with explicit rationale.

**Resumable state.** `docs/CODEX_PROMPT.md` is the single source of truth for live session state. Any agent, any session, any machine can resume exactly where the last one stopped. Nothing operational is held in conversational memory.

**Scoped continuity.** Prior decisions, implementation history, and proof are retrieved from explicit repo artifacts such as `docs/DECISION_LOG.md`, `docs/IMPLEMENTATION_JOURNAL.md`, `docs/EVIDENCE_INDEX.md`, ADRs, and review archives. Retrieval is convenience, not authority.

**README-first navigation.** Repo and folder `README.md` files are lightweight knowledge indexes. Before a phase closes, changed subsystems should have their nearest README updated with links to current canonical docs, decisions, tasks, proof, evals, and known gaps. README files route readers; they do not replace authoritative artifacts.

**Immutable contract.** `IMPLEMENTATION_CONTRACT.md` is the unchanging floor of the project. It does not evolve without an explicit ADR. This prevents incremental erosion of quality standards across phases.

**Structured task format.** Every task in `docs/tasks.md` follows a YAML-compatible block schema: `Owner`, `Phase`, `Type`, `Depends-On`, `Objective`, `Acceptance-Criteria` (each entry has `id`, `description`, and a mode-appropriate `test:` or `verify:` field), `Files`, `Notes`. The Orchestrator reads task fields directly without LLM parsing. A criterion without concrete verification evidence is a PHASE1_VALIDATOR blocker.

**Two-tier review.** Every task gets a lightweight 6-check security/contract review immediately after implementation. Every phase gets a deep four-agent review cycle: META → ARCH → CODE → CONSOLIDATED. The two tiers serve different purposes and neither replaces the other.

**Baseline tracking with enforcement.** After Phase 1, the passing test count is recorded as the baseline. Every subsequent session must not decrease it. A session that breaks tests must not commit — this is a hard rule.

**Finding lifecycle enforcement.** P2 findings that survive three review cycles without resolution are escalated, closed with justification, or deferred to v2. Findings cannot accumulate indefinitely.

**CI in Phase 1.** CI is mandatory in Phase 1. There is never a moment in this workflow when "tests pass locally but CI is unknown."

**Problem-first adoption gate.** Before choosing agent shape or runtime, Phase 1 must name the concrete operational pain, current workaround, first proof metric, and claims that are out of bounds before evidence exists. This keeps the playbook attached to real workflow problems instead of demo-driven AI adoption.

**Five capability profiles.** Optional architectural modes, each with algorithmic decision criteria, mandatory artifacts, profile-specific contract rules, deep-review checks, and an evaluation artifact:

| Profile | Governs | Review checks | Evaluation artifact |
|---------|---------|---------------|---------------------|
| **RAG** | Document retrieval: ingestion pipeline, query-time retrieval, explicit embedding strategy, `insufficient_evidence` path | RET-1..9 | `retrieval_eval.md` |
| **Tool-Use** | LLM-directed tool calls: schemas, side effects, unsafe-action gates, idempotency | TOOL-1..5 | `tool_eval.md` |
| **Agentic** | Multi-step decision loops: roles, authority boundaries, loop termination contract | AGENT-1..5 | `agent_eval.md` |
| **Planning** | Structured plan output as primary deliverable: schema, validation gate, plan-to-execution contract | PLAN-1..4 | `plan_eval.md` |
| **Compliance** | Regulated industries (HIPAA, SOC 2, PCI-DSS, GDPR): PHI enforcement, audit log, retention policy, evidence collection | COMP-1..5 | `compliance_eval.md` |

Profiles are activated in Phase 1 and treated as architectural constraints. Evaluation is enforced at Step 3.5: any task with a capability tag is not complete until the evaluation artifact is updated and compared against its baseline. A regression is a P1 finding.

**Capability auto-detection.** Pre-implementation: the Orchestrator matches the task's file scope against capability signal patterns — `retrieval/`, `embedding` → RAG; `tools/`, `@tool` → Tool-Use; `compliance/`, `audit/`, `hipaa/` → Compliance. A HIGH-confidence match with no matching `Type:` tag stops the session with a `TAG_WARNING` before any code is written. Post-implementation: file-vs-tag mismatches surface a `SEMANTIC_MISMATCH` to the reviewer.

**Domain skeletons.** Pre-built task sets for specific regulated domains that drop into `docs/tasks.md` directly. The HIPAA skeleton (`templates/domains/healthcare.md`) provides four tasks — PHI field enforcement, audit log infrastructure, retention policy enforcement, compliance evidence collection — each with complete acceptance criteria, test function references, and a starter `compliance_eval.md`. The Strategist includes it automatically when Compliance=ON and HIPAA is the active framework.

**Three-layer observability.** (1) Process level: Claude Code hooks block writes to immutable files; log every Bash command with `[TASK:T##]` tagging (set `CURRENT_TASK` env var in the orchestrator's Execute block); write a session checkpoint on stop with optional push notification (set `NOTIFICATION_TOKEN` + `NOTIFICATION_TARGET`, use `SILENT=1` to suppress for automated sessions). (2) Production level: OBS-1..3 rules in `IMPLEMENTATION_CONTRACT.md` (spans, metrics, health endpoint) enforced by CODE review checks. (3) AI quality level: capability evaluation artifacts, Step 3.5 regression detection (>5% → P1, >15% → P0 Stop-Ship), optional CI eval gates. See `PLAYBOOK.md §12`.

**Cost budget guardrails.** AI/model work must declare a budget boundary before it runs. Lean projects can keep the budget inline; Standard/Strict projects use `docs/COST_BUDGET.md` for recurring AI usage, agent loops, dynamic workflows, multi-user AI features, or material inference cost. Cost architecture is separate from budget: `docs/ai_cost_architecture.md` explains workload classes, cache layout, batch lanes, routing maturity, cascades, and cost-per-successful-task. Orchestrator and reviewer prompts flag missing budgets, missing cost architecture, model escalation, fan-out/retry expansion, dynamic routing, cascades, and cost-saving changes without eval/latency evidence.

**External skill security.** Third-party or cross-project agent skills are
treated as supply-chain artifacts. Before install, enablement, update, or
global exposure, projects create a trust record with source pin/signature/hash,
declared capabilities, SkillSpector or equivalent scan evidence, finding triage,
install scope, and risk acceptance. Clean scans and signatures are evidence, not
proof of safety.

**Codex-only code writing.** Claude-side direct edits to application code can be blocked with hooks so implementation goes only through `Bash -> codex exec`, preserving the implementer/reviewer split. A separate phase-boundary hook can block `CODEX_PROMPT.md` phase advancement until the completed phase has an archived review entry.

**Default implementation command.** The default and recommended implementation path is `codex exec -s workspace-write` invoked from Bash with a prompt file. The playbook's intended operating model is: Claude orchestrates and reviews; Codex writes application code.

---

## What This Playbook Is

A workflow for building AI-assisted software without assuming one default architecture. The Orchestrator runs the loop; Codex implements tasks in isolation; review agents check output at two tiers; the human approves phase gates. State lives in files, so sessions are resumable.

This playbook does not add a generic "memory layer" above the repo. It adds disciplined retrieval surfaces for architectural recall, implementation continuity, prior findings, and durable evidence while keeping files as the source of truth.

The cognition layer extension turns those retrieval surfaces into a portable markdown operating layer for long-lived engineering context. It remains repo-authoritative, Git-compatible, Obsidian-optional, and deterministic-first. Start with:

- [docs/cognition/architecture.md](docs/cognition/architecture.md) — cognition and operational memory architecture
- [docs/cognition/vault_usage_protocol.md](docs/cognition/vault_usage_protocol.md) — when the cognition vault should and should not be used
- [docs/cognition/obsidian_vault_architecture.md](docs/cognition/obsidian_vault_architecture.md) — optional Obsidian vault structure
- [docs/cognition/retrieval_context_packets.md](docs/cognition/retrieval_context_packets.md) — deterministic retrieval and context packet model
- [docs/cognition/migration_plan.md](docs/cognition/migration_plan.md) — staged rollout across existing repositories
- [docs/cognition/anti_complexity_safeguards.md](docs/cognition/anti_complexity_safeguards.md) — explicit boundaries and complexity ceilings

The local README-first index protocol sits below the cognition vault and above
ad hoc search:

- [docs/readme_first_knowledge_index.md](docs/readme_first_knowledge_index.md) — README index rules and phase-gate check
- [templates/README_INDEX.md](templates/README_INDEX.md) — folder/repo README index template

This playbook is intentionally not "agent-everywhere" and not "VM-by-default". It is designed to help teams choose the minimum sufficient solution shape, runtime substrate, and governance level for the actual risk and autonomy of the system.

For practical setup and adoption, use:

- [docs/usage_guide.md](docs/usage_guide.md) — end-to-end usage for new and existing repositories
- [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md) — current portfolio role and roadmap
- [docs/tasks.md](docs/tasks.md) — active framework task graph
- [docs/project_fit_guide.md](docs/project_fit_guide.md) — problem-first entry points, adoption reality gate, and anti-patterns
- [docs/architecture_layers.md](docs/architecture_layers.md) — concise layer map
- [docs/heavy_task_mode.md](docs/heavy_task_mode.md) — selective proof-first mode for risky tasks
- [docs/workflow_continuity_retrofit.md](docs/workflow_continuity_retrofit.md) — MemPalace assessment and the playbook-native continuity retrofit
- [docs/coverage_experiment_report_ru.md](docs/coverage_experiment_report_ru.md) — Russian coverage experiment report: project-fit zones, heavy-task boundaries, and execution-substrate line
- [docs/cost_budget_guardrails.md](docs/cost_budget_guardrails.md) — AI/model cost attribution, budget gates, and approval rules
- [docs/ai_cost_architecture.md](docs/ai_cost_architecture.md) — workload classes, cache/batch/routing strategy, cascades, and cost-per-successful-task rules
- [docs/cache_context_layout.md](docs/cache_context_layout.md) — prompt cache stable-prefix / volatile-suffix layout rules
- [docs/cost_telemetry_protocol.md](docs/cost_telemetry_protocol.md) — provider-agnostic AI cost telemetry JSONL and rollup protocol
- [docs/external_skill_security_policy.md](docs/external_skill_security_policy.md) — external agent skill trust gate, scan/signature policy, and approval rules
- [tools/init_playbook_project.py](tools/init_playbook_project.py) — deterministic Lean / Standard / Strict project initializer
- [tools/skill_security_gate.py](tools/skill_security_gate.py) — CI-friendly external skill trust-record and SkillSpector wrapper
- [templates/cost_adapters/](templates/cost_adapters/) — provider-neutral starter adapter for writing AI cost telemetry

The zero-trust execution extension strengthens the runtime/CI side without
making any external router mandatory:

- [docs/mythos_router_assessment.md](docs/mythos_router_assessment.md) — critical Mythos Router comparison and integration roadmap
- [docs/filesystem_reality_principle.md](docs/filesystem_reality_principle.md) — repo state beats model claims
- [docs/runtime_verification_protocol.md](docs/runtime_verification_protocol.md) — before/after verification record for risky writes
- [docs/bounded_correction_turns.md](docs/bounded_correction_turns.md) — limited self-repair and escalation rules
- [docs/provider_routing_policy.md](docs/provider_routing_policy.md) — optional multi-provider fallback policy
- [docs/integrity_verification_jobs.md](docs/integrity_verification_jobs.md) — CI/runtime reference integrity checks
- [docs/cognition_layer_integrity.md](docs/cognition_layer_integrity.md) — generated memory and Obsidian integrity rules
- [docs/entropy_core_proof_layer_protocol.md](docs/entropy_core_proof_layer_protocol.md) — optional proof layer protocol for product receipts and evidence
- [docs/entropy_core_and_gensyn_reference_policy.md](docs/entropy_core_and_gensyn_reference_policy.md) — optional Entropy Core references and bounded Gensyn-inspired patterns
- [docs/hermes_agent_reference_policy.md](docs/hermes_agent_reference_policy.md) — optional Hermes Agent T3 runtime reuse gate
- [docs/dynamic_workflow_reference_policy.md](docs/dynamic_workflow_reference_policy.md) — optional dynamic workflow and external orchestration reference policy
- [reference/solution_references.md](reference/solution_references.md) — curated external solution references, not mandatory dependencies
- [reference/cost_guardrails_research.md](reference/cost_guardrails_research.md) — current external evidence for cost tracking and guardrails

## Quick Start Cheat Sheet

### 1. Choose Adoption Mode

Read `docs/project_fit_guide.md`, then select a mode from
`docs/adoption_modes.md`.

| Mode | Use when | Starter kit |
|------|----------|-------------|
| Lean | Prototype, internal helper, low-blast-radius workflow | `docs/tasks.md`, short `docs/CODEX_PROMPT.md` or `AGENTS.md`, contract-lite, CI/local verification command |
| Standard | Recoverable product or operational system | Full core docs, README indexes, CI, light/deep review at phase boundaries |
| Strict | Compliance, PII, privileged tools, persistent agent runtime, risky migration | Standard plus evidence index, cognition manifest when used, runtime verification records, stricter review gates |

### 2. New Project

1. Choose Lean, Standard, or Strict.
2. Copy only the kit required by that mode.
3. Declare AI/model budget boundaries if the project uses LLMs, agents, dynamic workflows, or recurring eval/review calls. Add cost architecture when usage is recurring/material or uses prompt caching, batch lanes, dynamic routing, or cascades.
4. If using Claude Code and Standard/Strict, copy `.claude` settings/commands and hooks.
5. Run `/bootstrap-new` or produce the mode's starter artifacts manually.
6. Run the Phase 1 validator in the selected mode.
7. Start the orchestrator or Lean task/review loop.

### 3. Existing Project

1. Choose Lean, Standard, or Strict.
2. Copy only the kit required by that mode.
3. Normalize CI or document the local verification command.
4. Declare AI/model budget boundaries for recurring or material AI usage. Add cost architecture when the existing system already has prompt caching, batch lanes, dynamic routing, cascades, or provider/model tiering.
5. Run `/bootstrap-retrofit` only if the repo needs the full bootstrap flow.
6. Run the Phase 1 validator in the selected mode.
7. Start from the first real incomplete task.

### Mental Model

- project fit = problem-first gate
- `/bootstrap-*` = bootstrap entrypoint
- validator = artifact gate
- orchestrator = ongoing control-plane

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

See `docs/adoption_modes.md` for the artifact matrix. Lean mode is a real
reduced path, not a promise to create the full Strict artifact set with less
care.

Runtime is separate from agent shape. An agent is not a VM. VM or microVM isolation is optional and justified only when autonomy, mutability, privilege, or blast radius require it.

| Tier | Meaning | Typical use |
|------|---------|-------------|
| **T0** | Deterministic or managed execution with no special isolated mutable runtime | API logic, validators, fixed workflows, managed integrations |
| **T1** | Container / devcontainer / bounded worker runtime | Normal app services, bounded tool execution, standard CI and workers |
| **T2** | Ephemeral microVM-class or similarly isolated mutable runtime | Risky autonomous tasks that may modify workspace, shell state, or toolchain and need strong rollback |
| **T3** | Persistent VM-class or privileged long-lived isolated worker | Long-running autonomous workers with persistence, higher privilege surface, or stronger recovery needs |

Use this playbook by asking, in order:

1. Start with the concrete operational pain and current workaround.
2. Define the first proof metric and the claims that are not allowed before evidence exists.
3. Start with the minimum sufficient architecture, not the most impressive one.
4. Ask "why not deterministic?" before enabling LLM logic.
5. Ask "why not workflow?" before enabling bounded or open-ended agency.
6. Turn capability profiles ON only when they govern real behavior, not speculative future scope.
7. Keep runtime at T0/T1 unless there is a concrete isolation or mutability reason to escalate.
8. Increase governance only when error cost, auditability, or blast radius justify it.
9. Treat LLM cost like latency or security: budget it before recurring use, fan-out, retry loops, or model escalation.

Every rule and template addresses a concrete failure mode: silent quality erosion across phases, evaluation that never runs, review that misses profile-specific risks, compliance requirements that fall through to free-form LLM reasoning.

---

## The Loop

```
Project description
        |
        v
  [Strategist agent]
  Produces the selected mode's starter artifacts:
            Lean / Standard / Strict artifact set
            + profile-specific artifacts only when active
            + cost budget / cost architecture when AI/model work requires it
        |
        v
  [Phase 1 Validator]
  Mode-aware structural and consistency checks before implementation begins
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
├── docs/
│   ├── project_fit_guide.md          — problem-first entry points, adoption reality gate, and anti-patterns
│   ├── adoption_modes.md             — Lean / Standard / Strict artifact matrix
│   ├── cost_budget_guardrails.md      — AI/model budget gates and cost attribution policy
│   ├── ai_cost_architecture.md        — workload class, cache, batch, routing, cascade, and cost architecture protocol
│   ├── cache_context_layout.md        — prompt cache stable-prefix and volatile-suffix layout protocol
│   ├── cost_telemetry_protocol.md     — provider-agnostic AI cost telemetry JSONL + rollup protocol
│   ├── external_skill_security_policy.md — external skill supply-chain gate and trust record policy
│   ├── usage_guide.md                — end-to-end usage for new and existing repositories
│   ├── architecture_layers.md        — concise layer map
│   └── ...                           — focused reports and operational guides
├── prompts/
│   ├── STRATEGIST.md                — architecture-generation agent prompt
│   ├── ORCHESTRATOR.md              — development orchestrator prompt
│   ├── PHASE1_VALIDATOR.md          — pre-implementation artifact validator
│   ├── PROMPT_S_STRATEGY.md         — phase-boundary strategy reviewer prompt
│   └── audit/
│       ├── PROMPT_0_META.md         — review: meta-analysis
│       ├── PROMPT_1_ARCH.md         — review: architecture drift
│       ├── PROMPT_2_CODE.md         — review: code & security (SEC + profile checks + TOOL-6 MCP integrity)
│       ├── PROMPT_3_CONSOLIDATED.md — review: consolidated report
│       ├── PROMPT_SIMPLIFY.md       — EXPERIMENTAL: opt-in Simplification Pass reviewer prompt
│       └── AUDIT_INDEX.md           — audit index template
├── hooks/
│   ├── guard_files.sh               — PreToolUse: blocks writes to immutable files
│   ├── log_bash.sh                  — PostToolUse: audit log with [TASK:T##] tagging; extracts Codex results
│   └── save_checkpoint.sh           — Stop: writes Orchestrator snapshot; optional session-end notification (SILENT=1 for automated sessions)
├── templates/
│   ├── ARCHITECTURE.md              — system architecture document template
│   ├── CODEX_PROMPT.md              — session handoff template (all 5 profile state blocks; session token tracking)
│   ├── LEAN_CODEX_PROMPT.md         — Lean mode session handoff template
│   ├── AGENTS.md                    — Lean mode repo-local agent instruction template
│   ├── DECISION_LOG.md              — architectural / product decision index (retrieval surface, not authority)
│   ├── IMPLEMENTATION_JOURNAL.md    — append-only task / session continuity log
│   ├── IMPLEMENTATION_CONTRACT.md   — immutable rules template (universal + profile rules)
│   ├── CONTRACT_LITE.md             — Lean mode implementation boundary
│   ├── COST_BUDGET.md               — AI/model cost budget template
│   ├── COST_ARCHITECTURE.md          — AI/model cost architecture template
│   ├── ROUTER_EVAL.md                — dynamic routing / cascade evaluation template
│   ├── EXTERNAL_SKILL_TRUST_RECORD.md — external agent skill trust record template
│   ├── COST_TELEMETRY_ENTRY.json    — one-line JSON telemetry entry template
│   ├── COST_TELEMETRY_ADAPTER.md    — project-owned provider boundary task template
│   ├── EVIDENCE_INDEX.md            — index of durable proof, review findings, and evaluation artifacts
│   ├── PROJECT_BRIEF.md             — input template for the Strategist
│   ├── RETRIEVAL_EVAL.md            — RAG evaluation artifact template
│   ├── NFR.md                       — non-functional requirements template (SLA table + history)
│   ├── tasks_schema.md              — YAML-compatible task block schema, tag namespace, AC rules
│   ├── domains/
│   │   └── healthcare.md            — HIPAA skeleton: T-HC-01..04 with full AC + test refs
│   ├── skills/
│   │   ├── SKILL_INTERFACE.md       — descriptor format for optional skills
│   │   ├── external_tools_skill.md  — descriptor for the External Tools / MCP skill
│   │   ├── external_skill_security_skill.md — descriptor for external skill security gate
│   │   ├── research_skill.md        — EXPERIMENTAL descriptor for the Research Companion skill
│   │   └── simplification_skill.md  — EXPERIMENTAL descriptor for the Simplification Pass skill
│   ├── research/
│   │   └── RESEARCH_NOTE.md         — template for docs/research/{slug}.md source-grounded notes
│   ├── SIMPLIFICATION_REPORT.md     — template for Simplification Pass audit output
│   ├── cognition/                   — portable cognition, ADR, finding, packet, hypothesis templates
│   └── .claude/
│       ├── settings.json            — Claude Code hook configuration
│       └── commands/
│           ├── bootstrap-new.md     — greenfield bootstrap (surfaces optional skills at end)
│           ├── bootstrap-retrofit.md — retrofit bootstrap (surfaces optional skills at end)
│           └── simplify.md          — opt-in slash command for the Simplification Pass
├── schemas/                         — JSON schemas for cognition metadata, manifests, packets, cost telemetry
├── tools/                           — deterministic cognition, context packet, integrity, and cost rollup tools
│   └── cost_rollup.py               — JSONL AI cost telemetry rollup and threshold checker
├── ci/
│   └── ci.yml                       — GitHub Actions template (lint, tests, all 5 eval steps, NFR load test)
└── reference/
    ├── CODEX_CLI.md                 — Codex CLI patterns, sandbox limitations, pre-run checklist
    ├── cost_guardrails_research.md  — external cost tracking / guardrails evidence
    ├── optional_skills.md           — index of opt-in skills with registration table and scope rules
    ├── external_tools_mcp_companion.md — Tool-Use companion: Tool Catalog schema, unsafe-action conventions, MCP secret handling
    └── research_companion.md        — EXPERIMENTAL: source-grounded research notes for non-trivial arch decisions
```

### What each file is for

**PLAYBOOK.md** is the master document. Read it before anything else. It defines the phase structure, right-sizing logic, runtime selection, capability profiles, task execution protocol, review cycle, and universal rules.

**prompts/STRATEGIST.md** is the system prompt for the architecture-generation session. It reads your project description, selects Lean / Standard / Strict, and produces only the starter artifacts required by that mode. It forces explicit decisions about solution shape, rejected simpler alternatives, runtime tier, deterministic decomposition, human approval boundaries, capability profiles, and AI/model budget boundaries.

**prompts/ORCHESTRATOR.md** runs the development loop — capability signal detection (Step 0-E), complexity/runtime drift checks, Codex dispatch, evaluation gate (Step 3.5), and phase gate enforcement.

**prompts/PHASE1_VALIDATOR.md** runs once, after the Strategist produces the selected mode's starter artifacts and before T01 begins. It checks structural completeness and cross-document consistency in Lean, Standard, or Strict mode. Any blocker for that mode stops implementation.

**prompts/audit/PROMPT_2_CODE.md** is the code review prompt. It fires SEC-N (universal), profile-conditional RET-N / TOOL-N / AGENT-N / PLAN-N / COMP-N checks, OBS-N (observability), and TOOL-6 (MCP-backed tool integrity: pinned server version, side-effect class, idempotency, distinct confirmation path for destructive tools) on every deep review cycle.

**docs/project_fit_guide.md** helps decide whether the playbook should be used at all: concrete pain, current workaround, first proof metric, good entry points, and anti-patterns.

**templates/tasks_schema.md** defines the task block format. Every task in `docs/tasks.md` must use this schema — `Type:` tag, structured `Acceptance-Criteria` entries, explicit `Depends-On`, and mode-appropriate verification pointers. Standard/Strict tasks use specific `test:` pointers where code is changed; Lean may use a documented verification command when no test function exists yet.

It also supports optional `Context-Refs` and heavy-task extension fields so risky or history-sensitive tasks can carry retrieval pointers and proof expectations without making all tasks expensive.

**templates/ARCHITECTURE.md** now requires problem fit, adoption reality boundaries, solution shape, governance level, runtime tier, deterministic-vs-LLM ownership, human approval boundaries, and anti-overengineering non-goals. Runtime references such as Hermes are optional solution references, not base-path requirements; see `reference/solution_references.md`.

**templates/DECISION_LOG.md** is a lightweight index of why important choices were made and where the canonical record lives. It is not a replacement for `ARCHITECTURE.md` or ADRs; it makes them easier to retrieve.

**templates/IMPLEMENTATION_JOURNAL.md** captures append-only task handoffs: what changed, why, what evidence was collected, and what the next agent should know. It is the playbook's reusable implementation memory surface.

**templates/EVIDENCE_INDEX.md** indexes tests, evaluation runs, review findings, and manual proof so agents can retrieve prior evidence without treating summaries as truth.

**templates/PROJECT_BRIEF.md** is the recommended input template before running the Strategist. It helps you describe concrete pain, current workaround, adoption proof, goals, workflows, risks, AI scope, deterministic candidates, human approval boundaries, constraints, and success metrics without pre-deciding the architecture.

**templates/COST_ARCHITECTURE.md** turns AI cost from a policy note into an architecture artifact: workload classes, model tiers, prompt-cache layout, batch lanes, routing maturity, cascade rules, and cost-per-successful-task. Use it for recurring/material AI usage or any dynamic routing/cascade plan.

**templates/ROUTER_EVAL.md** is required when a project wants evaluated dynamic routing or cascades. It records the traffic sample, baseline, candidate models, quality floor, cost target, cache-hit impact, escalation rate, and stale-router policy.

**templates/EXTERNAL_SKILL_TRUST_RECORD.md** records source, pin/signature/hash,
declared capabilities, scan evidence, finding triage, install scope, and
approval for a third-party or cross-project agent skill before it enters the
agent context.

**templates/domains/healthcare.md** is the HIPAA domain skeleton. It provides four production-ready tasks with complete acceptance criteria (including specific test function references), a starter `docs/compliance_eval.md` table with HIPAA control rows, and ARCHITECTURE.md snippets. The Strategist includes it verbatim when Compliance=ON and HIPAA is the active framework.

**templates/NFR.md** tracks non-functional SLAs: target, measurement method, CI gate threshold, and a phase-by-phase baseline history. Included when the project has explicit latency, throughput, or error rate requirements.

**ci/ci.yml** has five commented capability eval steps (RAG, Agentic, Tool-Use, Planning, Compliance) and a commented NFR load test step (locust). Uncomment the steps for your active profiles.

**reference/CODEX_CLI.md** documents real operational knowledge: file-based prompt invocation, known sandbox limitations (async DB hangs, heavy ML deps), prompt engineering patterns.

**reference/optional_skills.md** is the index of registered optional skills — registration table, "How to Add" steps, and an "Out of Scope" redirect table for things that belong in canonical artifacts instead.

**reference/external_tools_mcp_companion.md** is the Tool-Use profile companion guide: Tool Catalog row schema, side-effect classification table, idempotency requirements, unsafe-action confirmation code-path requirement, audit log shape, secret handling, tool-schema versioning, and two worked examples. Shape-only — does not require any specific vendor.

**reference/research_companion.md** (EXPERIMENTAL) governs when and how to produce source-grounded `docs/research/{slug}.md` notes for non-trivial architecture, library, or compliance decisions. Promotes to optional after experiment E3.

**templates/.claude/commands/** provides command-style entrypoints. `bootstrap-new` and `bootstrap-retrofit` start the bootstrap flow and, after generating the package, surface optional skills with conditional recommendations (MCP companion activates silently when Tool-Use=ON; Research Companion asks yes/no for non-trivial decisions; Simplification Pass is always human-triggered). `simplify.md` is the opt-in entrypoint for the Simplification Pass.

---

## How to Start a New Project

Fast path with Claude Code for Standard/Strict:

1. Check `docs/project_fit_guide.md`
2. Copy `templates/.claude/settings.json` to `.claude/settings.json`
3. Copy `templates/.claude/commands/bootstrap-new.md` to `.claude/commands/bootstrap-new.md`
4. Copy `hooks/*.sh` and make them executable
5. Run `/bootstrap-new`

This does not replace validation or orchestration. It gives Claude a standard bootstrap entrypoint without changing the system prompt.

Lean projects may skip this command path and create the smaller artifact set
from `docs/adoption_modes.md` directly.

1. Open a Claude session (Claude.ai or Claude Code).
2. Set `prompts/STRATEGIST.md` as the system prompt.
3. Fill `templates/PROJECT_BRIEF.md` or describe the same fields in chat: concrete pain, current workaround, adoption proof metric, domain, workflows, AI scope, deterministic candidates, expected scale, constraints, risk boundaries, AI/model budget, and compliance requirements.
4. The Strategist asks clarifying questions, then produces the starter package for the selected mode:
   - Lean: `docs/tasks.md`, short `docs/CODEX_PROMPT.md` or `AGENTS.md`, contract-lite, CI/local verification command, review checklist, inline budget/cost architecture notes, and inline external-skill trust notes or dedicated artifacts when needed
   - Standard/Strict:
     - `docs/ARCHITECTURE.md`, `docs/spec.md`, `docs/tasks.md`
     - `docs/CODEX_PROMPT.md`, `docs/IMPLEMENTATION_CONTRACT.md`
     - `docs/COST_BUDGET.md` when recurring AI usage, agent loops, dynamic workflows, multi-user AI features, or material inference cost are present
     - `docs/ai_cost_architecture.md` when AI spend is recurring/material, prompt caching or batch lanes are used, or model routing/cascades affect quality/cost
     - `docs/router_eval.md` when dynamic routing or cascades are used
     - `docs/security/skills/{skill-name}/TRUST_RECORD.md` before external skill install/update/enablement
     - `.github/workflows/ci.yml`
     - Review prompts: `docs/audit/PROMPT_0_META.md` through `PROMPT_3_CONSOLIDATED.md`, `docs/audit/AUDIT_INDEX.md`
     - If Compliance=ON: `docs/compliance_eval.md` (with framework-specific control rows)
     - If NFR constraints stated: `docs/nfr.md` (with SLA table)
5. Copy `prompts/ORCHESTRATOR.md` to `your-project/docs/prompts/ORCHESTRATOR.md`, fill `{{PROJECT_ROOT}}`, and set `{{CODEX_COMMAND}}` to `codex exec -s workspace-write` unless your environment requires a wrapper around the same command.
6. Copy hooks and settings:
   ```bash
   cp -r hooks/ your-project/hooks/
   mkdir -p your-project/.claude/
   cp templates/.claude/settings.json your-project/.claude/settings.json
   chmod +x your-project/hooks/*.sh
   ```
7. Run the Phase 1 Validator in the selected mode before starting implementation:
   - Open a Claude session with `prompts/PHASE1_VALIDATOR.md` as the prompt
   - Set `Mode: Lean`, `Mode: Standard`, or `Mode: Strict`
   - It produces `docs/audit/PHASE1_AUDIT.md` — resolve all mode-relevant BLOCKERs before proceeding
8. Open a Claude Code session with `docs/prompts/ORCHESTRATOR.md` as the system prompt.
9. Say: "Start Phase 1." The Orchestrator reads `docs/CODEX_PROMPT.md` and begins.

The human sits at every phase gate. From there, the loop runs itself.

## How to Retrofit an Existing Project

Do not pretend the repo is greenfield.

Use the playbook as a governance retrofit:

Fast path with Claude Code:

1. Copy `templates/.claude/settings.json` to `.claude/settings.json`
2. Copy `templates/.claude/commands/bootstrap-retrofit.md` to `.claude/commands/bootstrap-retrofit.md`
3. Copy `hooks/*.sh` and make them executable
4. Run `/bootstrap-retrofit`

This starts the retrofit bootstrap as a command-driven flow without replacing the system prompt.

1. Generate `docs/ARCHITECTURE.md` from current reality, not from an imagined rewrite.
2. Create `docs/CODEX_PROMPT.md` using the real current baseline and next task.
3. Create `docs/IMPLEMENTATION_CONTRACT.md` around stable rules the current repo must now obey.
4. Seed `docs/DECISION_LOG.md` and `docs/IMPLEMENTATION_JOURNAL.md` from active architecture and the next real task.
5. Build `docs/tasks.md` as a forward contract for upcoming work, remediation, and cleanup.
6. Add audit prompts, orchestrator prompt, and CI normalization where missing.
7. Mark only genuinely risky migration/remediation tasks as heavy.

See [docs/usage_guide.md](docs/usage_guide.md) for the full retrofit flow.
