# Contract Lite

Status: LEAN CONTRACT
Mode: Lean

Use this when a project needs task discipline and verification, but does not
justify the full `docs/IMPLEMENTATION_CONTRACT.md` surface yet.

## Scope

- Project:
- Current mode: Lean
- Allowed change area:
- Out-of-scope change area:

## Required Verification

Every task must name at least one concrete verification step:

```yaml
verify:
  command:
  expected:
```

If a task changes production behavior, add a real test before marking it done.

## Non-Negotiable Rules

- Do not commit secrets, credentials, tokens, or `.env` files.
- Do not self-review meaningful implementation changes.
- Do not weaken tests, acceptance criteria, or verification commands to make a
  task pass.
- Do not expand runtime, network, tool, or privilege boundaries without changing
  mode to Standard or Strict.
- Do not treat generated memory, chat summaries, or context packets as source of
  truth.
- Do not install, enable, update, or globally expose external agent skills
  without trust evidence. Instruction-only project-local skills may record
  inline evidence here; executable or external skills require a trust record.

## Human Approval Boundaries

Human approval is required for:

- auth, secrets, billing, data deletion, or external side effects
- model escalation that increases cost materially
- new autonomous loops, scheduled agents, or persistent workers
- dependency or infrastructure changes with operational risk
- global external skill install, or accepted risk for a high/critical skill
  security finding

## Cost Boundary

- Default model class:
- Stronger model allowed when:
- Per-task budget:
- Escalation threshold:
- Recurring/material AI usage: yes / no
- Cost architecture location: inline here / `docs/ai_cost_architecture.md` / not applicable
- Routing maturity: L0 / L1 / L2 / L3 / L4 / L5 / L6 / not applicable
- Prompt cache layout: stable-prefix documented / not used / not applicable
- Dynamic routing or cascades: forbidden / requires `docs/router_eval.md`

If budget is exceeded or projected to exceed the threshold, stop and ask for
approval before continuing.

If recurring/material AI usage, prompt caching, batch lanes, dynamic routing,
or cascades are introduced, record workload classes, output caps, retry/fan-out
caps, cache/batch/routing decisions, and escalation rules here or move the
project to a dedicated `docs/ai_cost_architecture.md`.

## External Skill Boundary

- External skills used: none / list
- Trust evidence location: inline here / `docs/security/skills/{skill-name}/TRUST_RECORD.md`
- Skill source/version/hash:
- Install scope: project-local / global
- Declared capabilities: shell / network / file / env / MCP-tool / dependencies / persistence / none
- Scan evidence: SkillSpector / equivalent / not applicable
- Signature/hash/pin evidence:
- Approval required before:

Executable, networked, MCP/tool-enabled, file/env-accessing, persistent, or
third-party skills require a full trust record before use.

## Review

Use `templates/LEAN_REVIEW_CHECKLIST.md` for low-risk work. Escalate to Standard
review when the checklist cannot verify the change.
