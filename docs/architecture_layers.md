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

## 3. Optional Execution Patterns

These patterns help execution but are not the center of the system:

- parallel subagents
- fanout / merge review
- isolated worktrees
- runtime tier selection

Useful, but secondary.

## 4. Harness / Packaging

This makes the playbook reusable:

- hooks
- Claude Code settings
- bootstrap flow
- templates
- usage guides

Packaging should improve adoption without being confused for architecture.

## Boundary Rule

If a change makes the repository look more like a scheduler than a governance system, it likely belongs in optional execution or outside the playbook core.
