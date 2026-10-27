# Skill Interface — Design LLM Privacy

Status: EXPERIMENTAL
Maintainer: Playbook maintainers

## Source and Trust

Original repository-authored instructions based on
[AGIMA's article](https://habr.com/ru/companies/agima/articles/1081356/), with
primary references and additional engineering recommendations identified in the
[design checks](../../engineering/skills/design-llm-privacy/references/design-checks.md).
No third-party executable or article body is vendored. The portable bundle is
[engineering/skills/design-llm-privacy](../../engineering/skills/design-llm-privacy/SKILL.md).

The [trust record](../../docs/security/skills/design-llm-privacy/TRUST_RECORD.md)
declares scoped capabilities, integrity, performed checks, and remaining limits.
Source publication does not install the skill or approve downstream activation.
Apply the existing external-skill gate when adopting it into another project.

## Purpose

Design or review an LLM/RAG privacy boundary that suppresses sensitive values
while preserving authorized entity-based retrieval. Supply the concrete identity,
policy, release, and evaluation decisions missing from a generic security review.
Produce an implementable handoff, not a runtime DLP service or legal assurance.

## Trigger

Invoke explicitly for a privacy architecture/review request or by naming the
skill. Announce the scope. Do not trigger for unrelated security work or merely
because a project uses an LLM. Codex metadata disables implicit invocation;
Claude's manual-only setting is documented in the Engineering usage guide.

## Allowed Role

| Role | Allowed |
|---|---|
| Strategist | yes |
| Orchestrator | no |
| Reviewer (light or deep) | yes, within the authorized review scope |
| Human | yes |
| Codex (implementation agent) | never; implement approved tasks through the existing project route |

Codex **the host application** may run an authorized design/review session,
just as Claude Code may. This does not change the Playbook implementation role
or make the skill a second task controller.

## Forbidden Actions

- Does not write application code or tests in `app/`, `src/`, `lib/`, or `tests/`.
- Does not directly modify `docs/IMPLEMENTATION_CONTRACT.md`,
  `docs/ARCHITECTURE.md`, `docs/spec.md`, `docs/tasks.md`, or `docs/CODEX_PROMPT.md`.
- Does not skip Phase 1 validation, bypass the task graph, or substitute for
  RAG, Tool-Use, Agentic, Planning, or Compliance profile gates.
- Does not read credentials, production personal data, or private dumps;
  upload data; invoke external models/tools; or run live evaluations.
- Does not install dependencies, alter permissions/settings, deploy a gateway,
  schedule monitoring, or certify anonymity or legal compliance.

## Input Artifacts

- User's named privacy question, target components, and allowed design/review scope.
- Applicable `AGENTS.md` and existing project contract/architecture decisions.
- Relevant provider clients, retrieval filters, authorization rules, output/tool
  serializers, logging configuration, and synthetic tests, found by targeted search.
- Existing evaluation requirements and safe synthetic fixtures; missing policies
  remain explicit open decisions rather than inferred disclosure permission.

## Output Artifacts

Chat by default. If a saved deliverable is requested, write the agreed scoped
note, for example `docs/design/LLM_PRIVACY_BOUNDARY.md` or
`docs/audit/LLM_PRIVACY_REVIEW.md`. Include proposed tasks with acceptance criteria
and test references in that note. These are retrieval/findings surfaces, not
authority over canonical project files.

## Evaluation Criteria

Use the bundle's [evaluation guide](../../engineering/skills/design-llm-privacy/references/evaluation.md).
For skill exercises require zero unauthorized actions, zero fabricated results,
and explicit treatment of every applicable trust boundary in the supplied case.
Native-host loading/behavior and downstream product benefit remain unverified
until separately exercised and recorded.

Evaluate skill behavior with fresh design, flawed-architecture review, and
out-of-scope live-data requests. Give the assistant only the skill and task-local
facts; keep expected findings, scoring rubric, and previous outputs outside its
context. The bundled application scenario matrix is guidance, not a blind skill
benchmark. Record actual exercise outputs and limits separately.

For the proposed application require zero unauthorized disclosures/actions in
the selected synthetic cases, with denominator and coverage. Separately measure
detection precision/recall, false entity merges, policy errors, retrieval quality,
and added p95 latency. Set utility and latency thresholds before candidate runs;
do not report these planned criteria as application results.

## Conflict Rules

Follow the target project's established precedence. For Governed projects:

1. `docs/IMPLEMENTATION_CONTRACT.md`
2. `docs/adr/`
3. `docs/ARCHITECTURE.md`
4. `docs/spec.md`
5. `docs/tasks.md`
6. Skill output, lowest priority

Report conflicts and proposed changes; do not rewrite the governing documents
or import new phase gates into a project that does not use them.

## Review Path

Route proposed implementation through the project's existing tasks, acceptance
criteria, tests, and code review. Use an ADR where architecture/contract impact
requires one. Design advice and a passing fixture do not close a runtime finding
without evidence from the affected implementation. Registration itself is a
documentation change and does not require an ADR.
