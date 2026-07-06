# Architecture Layers

AI Workflow Playbook is easiest to maintain if you separate four concerns.

## 1. Policy / Governance

This is the core:

- phases
- task contracts
- immutable rules
- review policy
- stop conditions
- document authority

If a feature strengthens this layer, it usually belongs in the core playbook.

## 2. Proof / Evidence

This layer answers: what proves that the work is actually done?

Examples:

- evaluation artifacts
- explicit evidence collection
- selective proof-first handling for risky tasks
- fresh verification for non-trivial changes

This layer should grow selectively, not by making every task heavy.

## 2b. Cognition / Operational Memory

This layer answers: what context must survive across sessions, agents, projects, reviews, and eval regressions?

Examples:

- repo-local cognition manifests
- ADR lineage and decision indexes
- eval history linked to tasks and evidence
- postmortems and persistent findings
- deterministic retrieval manifests
- role-scoped context packets
- optional Obsidian graph notes that cite canonical repo files

This layer is not a generic memory product. It remains markdown-native, Git-compatible, and repo-authoritative.

## 3. Optional Execution Patterns

These patterns help execution but are not the center of the system:

- parallel subagents
- fanout / merge review
- isolated worktrees
- runtime tier selection

**T3 runtime references.** When Phase 1 selects `Higher-autonomy agent` + `T3`, external runtimes such as Hermes Agent may be useful candidates. Treat them as optional solution references, not base-path dependencies. Before selecting Hermes or rebuilding a Hermes-shaped runtime subsystem, run the reuse gate in `docs/hermes_agent_reference_policy.md` and record the decision. See `reference/solution_references.md` and `docs/dynamic_workflow_reference_policy.md`.

Useful, but secondary.

## 4. Harness Design / Packaging

Harness design makes agentic systems auditable:

- model + prompt boundary
- tool registry and permission classes
- memory/state, retries, recovery, and termination
- trace schema and runtime evidence
- human handoff contract
- harness eval and benchmark cards

This is an architecture contract, not a runtime framework.

Packaging makes the playbook reusable:

- hooks
- Claude Code settings
- bootstrap flow
- templates
- usage guides

Packaging should improve adoption without being confused for architecture.

## Boundary Rule

If a change makes the repository look more like a scheduler than a governance system, it likely belongs in optional execution or outside the playbook core.
