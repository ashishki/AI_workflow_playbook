# Hermes Agent Reference Policy

Status: active reference policy
Last updated: 2026-05-31

## Purpose

Hermes Agent is a candidate open-source runtime for T3 higher-autonomy agent
projects. It is not required by the playbook, and it does not replace the
orchestrator, review loop, task graph, ADRs, evals, or project governance.

Use Hermes only when the project actually needs persistent agent execution,
messaging gateways, cron, subagents, tool backends, or long-lived assistant
memory that cannot be handled by a simpler T0/T1/T2 workflow.

## Official Discovery Sources

Check these sources before making a Hermes-related implementation decision:

- `https://github.com/NousResearch/hermes-agent`
- `https://hermes-agent.nousresearch.com/docs`
- `https://github.com/NousResearch/hermes-agent/releases`

As of 2026-05-31, the official repository is MIT licensed and documents a
runtime with provider routing, TUI/CLI, messaging gateway, persistent memory,
skills, cron scheduling, subagents, multiple terminal backends, MCP support,
and migration paths from OpenClaw.

This list is not a frozen dependency registry. Re-check the official repository
and docs before selecting, adapting, or rejecting Hermes for a task.

## Hermes Open-Source Reuse Gate

Do not rebuild a Hermes-shaped runtime subsystem before checking whether Hermes
already provides it.

Run this gate when a task touches:

- persistent assistant memory or cross-session recall;
- Telegram, Discord, Slack, WhatsApp, Signal, Email, or gateway delivery;
- cron/scheduled agent jobs;
- subagent delegation or parallel agent workstreams;
- terminal backends such as local, Docker, SSH, Modal, Daytona, or Singularity;
- skill creation, skill loading, or self-improving skill workflows;
- MCP integration for agent tools;
- provider/model switching for a long-lived assistant;
- OpenClaw migration paths;
- T3 higher-autonomy runtime selection.

Required decision order:

1. Search official Hermes sources for an existing implementation.
2. Classify the candidate as `direct_runtime`, `runtime_adapter`,
   `vendored_component`, `adapted_code`, `pattern_only`, or `reject`.
3. Prefer the highest-reuse option that passes fit, license, maintenance,
   security, operational complexity, and playbook-governance checks.
4. If rejecting a usable Hermes implementation, record why a local
   implementation is still better.
5. Pin any dependency or copied source to a repo URL, release or commit SHA,
   and file path.

Skipping this gate is allowed only when the task is documentation-only, the
feature is unrelated to Hermes-shaped runtime behavior, or the project already
contains a fresh ADR/reuse decision for the same component.

## Required Record

When Hermes is considered, record this in the project ADR, architecture section,
or task note:

```yaml
external_runtime_reuse:
  runtime: hermes-agent
  official_sources_checked:
    - https://github.com/NousResearch/hermes-agent
    - https://hermes-agent.nousresearch.com/docs
  checked_at: 2026-05-31
  candidates:
    - name: hermes-agent
      repo: https://github.com/NousResearch/hermes-agent
      version_or_commit: "<release-or-sha>"
      decision: direct_runtime
      reason: "Provides the required T3 gateway/cron/subagent runtime."
  rejected_alternatives: []
  governance_checks:
    license_checked: true
    security_review_required: true
    agent_eval_required: true
    human_review_gate_required: true
```

## Adoption Boundaries

Allowed:

- use Hermes as an optional T3 runtime after Phase 1 selects higher-autonomy
  agent plus T3;
- adapt its runtime shape as a reference for architecture planning;
- use an adapter around Hermes when the project needs only one bounded surface;
- reuse code only after license, pinning, attribution, and security review.

Not allowed by default:

- making Hermes mandatory for T0/T1/T2 projects;
- replacing the playbook orchestrator or review gates with Hermes;
- enabling community skills without review and pinning;
- enabling autonomous skill creation in production without `docs/agent_eval.md`;
- allowing plugins or subagents to inherit broad credentials;
- treating Hermes memory as canonical over repo docs.

## Fit Test

Hermes is a good candidate when the project needs a long-lived assistant that
talks through messaging channels, runs scheduled tasks, delegates to subagents,
or preserves operational memory across sessions.

Hermes is the wrong default when the work is a deterministic batch pipeline,
single-user local script, dashboard, report generator, or ordinary playbook
implementation loop.
