# Lean Review Checklist

Use this for Lean-mode tasks and deterministic review of low-risk changes.

## Inputs

- Task:
- Changed files:
- Verification command:
- Verification result:

## Checks

- [ ] Changed files match the task scope.
- [ ] The implementation satisfies every acceptance criterion.
- [ ] Each `test:` or `verify:` command was run, or a concrete reason is recorded.
- [ ] No tests, checks, or acceptance criteria were weakened.
- [ ] No secrets, credentials, tokens, or `.env` files were added.
- [ ] No auth, billing, data deletion, external side effect, runtime, network, or
      privilege boundary changed without escalation.
- [ ] Cost/model usage stayed within the declared task budget or was explicitly
      approved.
- [ ] Completion claims are supported by repository state.

## Verdict

LEAN_REVIEW_RESULT: PASS | ISSUES_FOUND | ESCALATE

Escalate when the change affects security, runtime, external side effects,
autonomy, compliance evidence, or cannot be verified by this checklist.
