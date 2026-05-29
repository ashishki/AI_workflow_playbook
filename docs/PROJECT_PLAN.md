# AI Workflow Playbook - Project Plan

Status: active core framework
Role: operating system for AI-assisted engineering
Priority: P0

## Strategic Role

AI Workflow Playbook remains the canonical governance layer for the portfolio. It
defines how projects are planned, implemented, reviewed, verified, documented,
and resumed across agents and machines.

The playbook is not a product UI and should not become a mandatory runtime. Its
value is protocol discipline: contracts, evidence, review, phase gates, runtime
verification, and cognition integrity.

## Near-Term Roadmap

### P0 - Consolidate Zero-Trust Execution

- Integrate Runtime Verification Protocol into default task templates.
- Add examples of `runtime_verification`, `decision_receipt`, and
  `risk_acceptance_record`.
- Add CI example for `tools/integrity_check.py`.
- Add reviewer checklist rows for stale cognition packets and broken
  Context-Refs.

### P1 - Add Entropy-Inspired Evidence Layer

- Define playbook-native receipt schemas:
  - `agent_action_receipt`
  - `decision_receipt`
  - `referee_review_record`
  - `risk_acceptance_record`
- Keep receipts as artifacts, not infrastructure dependencies.
- Use `docs/entropy_core_and_gensyn_reference_policy.md` to keep Entropy Core
  references optional and Gensyn-inspired patterns bounded.
- Add examples for implementation, review, provider fallback, and eval
  regression.

### P1 - Add Diverse Review Principle

- Document that role/model diversity is useful for high-risk work because
  different reviewers find different failure niches.
- Do not add swarm behavior.
- Keep consolidation human-readable and evidence-backed.

### P2 - Portfolio Integration

- Add a portfolio operating guide showing how Playbook, Entropy Core, Workflow
  Studio, Training OS, Radar, and Telegram Intelligence fit together.
- Add migration notes for projects that only need a lightweight version.

## AI-Development Tasks

- Use Codex for doc/protocol edits only after task scope is explicit.
- Require runtime verification for risky prompt/template changes.
- Use reviewer agents for architecture-impacting changes.
- Do not use autonomous self-repair beyond bounded correction rules.

## Stop Conditions

- If a proposed feature requires a server, database, or UI, it likely belongs in
  another project.
- If a protocol cannot be explained as an artifact/check/workflow, do not add it.
