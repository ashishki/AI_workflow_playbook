# AI Workflow Playbook

A distilled AI-assisted development workflow extracted from the [gdev-agent](https://github.com/ashishki/gdev-agent) project. This playbook provides the structure, prompts, and templates needed to replicate that workflow on any new project.

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
  Each Codex agent: captures baseline → implements → tests → commits
        |
        v
  [Review cycle] (after each phase)
  META review   → process compliance
  ARCH review   → architectural compliance
  CODE review   → detailed code findings (P1/P2/P3)
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
│   └── ORCHESTRATOR.md         — system prompt for the development orchestrator session
├── templates/
│   ├── ARCHITECTURE.md         — template for system architecture document
│   ├── CODEX_PROMPT.md         — template for session handoff document
│   └── IMPLEMENTATION_CONTRACT.md — template for immutable rules document
├── ci/
│   └── ci.yml                  — GitHub Actions CI template
└── reference/
    └── GDEV_AGENT.md           — how to use gdev-agent as implementation reference
```

### What each file is for

**PLAYBOOK.md** is the master document. Read it before anything else. It defines the philosophy, phase structure, task execution protocol, review cycle structure, and all universal rules.

**prompts/STRATEGIST.md** is the system prompt you give to a Claude session when starting a new project. The agent reads your project description and produces all the starter documents.

**prompts/ORCHESTRATOR.md** is the system prompt for the Claude Code session that runs the development loop — spawning Codex agents, running reviews, and enforcing phase gates.

**templates/** contains starting-point documents with `{{PLACEHOLDER}}` markers. The Strategist agent fills these in for your specific project.

**ci/ci.yml** is a GitHub Actions template that mirrors the pattern proven in gdev-agent.

**reference/GDEV_AGENT.md** explains which parts of gdev-agent to study when you need a concrete implementation example.

---

## How to Start a New Project

1. Open a Claude session (Claude.ai or Claude Code).
2. Attach or paste:
   - The contents of `PLAYBOOK.md`
   - The contents of `prompts/STRATEGIST.md` as the system prompt
3. Describe your project: domain, stack preferences, expected scale, team size, key constraints.
4. The Strategist agent will produce all starter documents. Save them into your new repo.
5. Open a Claude Code session in your new repo with `prompts/ORCHESTRATOR.md` as the system prompt.
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
