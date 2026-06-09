# Dynamic Workflow Reference Policy

## Purpose

Dynamic workflows and external agent runtimes are optional reference material.
They are useful when the playbook needs executable orchestration patterns, not
when a project only needs instructions for an LLM.

The base playbook must not depend on Claude dynamic workflows, Hermes, Mythos,
Entropy Core, Gensyn, Cybos, or any other external runtime. These references are
a catalog of solution patterns.

## Skill vs Workflow

| Surface | Best For | Limitation |
|---------|----------|------------|
| Skill / prompt | Teaching a model local conventions, review lenses, or tool usage | The model still has to remember and enforce the process |
| Dynamic workflow | Encoding phases, loops, schemas, fan-out, review, retries, and stop conditions | Higher token/tool cost and higher execution risk |
| Deterministic script | Link checks, schema checks, hashes, tests, formatting, CI gates | Cannot make judgment calls without explicit rules |

Prefer deterministic scripts for checks that can be formalized. Use dynamic
workflows for large tasks that need bounded parallel agents and structured
feedback.

## Use Dynamic Workflow References When

- the task can be decomposed into independent lanes
- the workflow needs bounded loops such as `MAX_ROUNDS` or `MAX_IN_FLIGHT`
- each agent can return a structured schema
- runtime evidence exists: test logs, CI logs, diffs, diagnostics, commit SHAs
- independent verification can drop, downgrade, or confirm findings
- the job is too large for one context window or one agent pass

## Do Not Use Them When

- a checklist, script, CI job, or normal review is enough
- the workflow would run unreviewed shell, GitHub, Slack, cloud, or database
  commands
- the source workflow is copied from a public repo without security review
- the project cannot afford high token/tool usage
- the workflow assumes another company's infrastructure
- the task is low-risk and short-lived

## Adoption Gate

Before adapting an external workflow, create a short reference record:

```yaml
source:
  name:
  url:
  authority: official | source-code | maintainer-docs | community | blog
  last_verified:
problem_it_solves:
patterns_to_adapt:
patterns_rejected:
required_tools:
routing_and_model_budget:
  max_model_calls:
  max_parallel_agents:
  max_tool_calls:
  max_retries:
  max_cost_usd:
  approval_before_overrun:
risk_level: lean | standard | strict-only
review_required:
verification_command:
fallback_if_workflow_fails:
```

An adapted workflow must have:

- explicit phase list
- bounded fan-out and bounded loops
- declared cost budget: max model calls, tool calls, retries, parallel agents,
  and cost per run
- structured output schemas for agent results
- idempotent side-effect steps
- stop conditions
- evidence inputs
- human approval for destructive, privileged, or external side effects

## Reference Patterns To Preserve

- structured output schemas instead of free-form completion claims
- bounded parallelism such as `MAX_FIX`, `MAX_ROUNDS`, `MAX_IN_FLIGHT`
- one expensive build/test per round when per-agent rebuilds are wasteful
- evidence-first repair from diagnostics, logs, diffs, and commit SHAs
- adversarial verification before fixing reviewer findings
- idempotent external updates for PRs, work items, tickets, and comments
- deterministic gates before LLM selection or prioritization

## Known Reference Sources

| Source | Useful Pattern | Role In Playbook |
|--------|----------------|------------------|
| Claude dynamic workflows announcement | parallel subagents, verification, long-running orchestration, token-cost warning | official product reference |
| Cybos workflow explorer | searchable public workflow patterns and categories | discovery surface only |
| Bun Zig-to-Rust workflow | one-build-per-round, test survey, bounded fix swarm, two-vote review | migration/swarm pattern reference |
| Salesforce `auto-build-wi` workflow | work-item loop, PR/CI monitor, idempotent updates, verified findings | enterprise workflow pattern reference |
| Hermes Guide wiki | operator field notes for runtime, memory, profiles, messaging, coding workflows | community reference only |
| Mythos Router | filesystem write discipline, receipts, snapshot/hash verification | verification pattern reference |
| Entropy Core | proof/evidence vocabulary | optional proof-layer reference |
| Gensyn / CodeZero | diverse solver/evaluator/referee inspiration | review diversity reference, not runtime dependency |

## Evidence URLs

- https://claude.com/blog/introducing-dynamic-workflows-in-claude-code
- https://www.cybos.ai/workflows
- https://github.com/Microck/bun-rust-port-claude-artifacts/blob/main/.claude/workflows/phase-g-mega-swarm.workflow.js
- https://github.com/forcedotcom/salesforcedx-vscode/blob/develop/.claude/workflows/auto-build-wi.js
- https://hermesguide.xyz/wiki/
- https://github.com/thewaltero/mythos-router
- https://docs.gensyn.ai/testnet/rl-swarm/how-it-works/codezero

## Boundary

External references may justify a task, ADR, or optional workflow experiment.
They do not override project contracts, CI, human approval rules, or repository
state.
