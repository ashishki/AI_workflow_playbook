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

## Human Approval Boundaries

Human approval is required for:

- auth, secrets, billing, data deletion, or external side effects
- model escalation that increases cost materially
- new autonomous loops, scheduled agents, or persistent workers
- dependency or infrastructure changes with operational risk

## Cost Boundary

- Default model class:
- Stronger model allowed when:
- Per-task budget:
- Escalation threshold:

If budget is exceeded or projected to exceed the threshold, stop and ask for
approval before continuing.

## Review

Use `templates/LEAN_REVIEW_CHECKLIST.md` for low-risk work. Escalate to Standard
review when the checklist cannot verify the change.
