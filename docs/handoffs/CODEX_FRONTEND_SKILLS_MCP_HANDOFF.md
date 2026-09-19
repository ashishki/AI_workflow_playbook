# Handoff: Playbook Native preview.4

Updated 2026-09-19. Branch `docs/codex-frontend-skills-mcp-20260919`.
This increment starts at `b80eb56`; original proposal base `d070f4e`.
Master remains `d570163`; no downstream changes, public release, licensing change,
host configuration change or subscriber contact.

## Current result

A [small offline kit](../../distribution/native/README.md) provides a prepared
project with two skills and a 22-line block. Users work in **Codex**. START.html
explains the first run and optionally builds a prompt; it does not run an agent.
The same source package supports native plugin installation for existing projects.

The dimensions stay independent: new/existing; create/fix/check;
automatic/plan-first/extended. Quick reduces ceremony and retains verification.
Namespaced plugin skills and repo-local skills have different technical names;
the plain-language user entry remains “Playbook, помоги с задачей”.

The root README is now 78 lines in Russian. The long Governed reference moved to
[docs/governed](../governed/README.md); its mechanisms and frozen pilots are retained.
Forty-five historical Native artifacts were removed from the current tree after
byte verification against `b80eb56`; [pinned archive links](../../reports/native/README.md)
preserve access. No Git history was rewritten. Old preview.3 downloads are intact.

## Current development route

Use [the short author protocol](../native/DEVELOPMENT_RU.md): observed problem,
small change, explicit acceptance, evidence, decision. **Existing Harness Lab**
owns new comparisons. Ground Truth Lab is deferred by the user.

[Native suite](../../evals/native/harness/README.md) connects backend repair and
plan-only through Lab's command adapter. It supports plain Codex or a previous
Native package as baseline. Native only supplies skill delivery and external
acceptance; no new runtime, scoring registry or evidence format. Original
`evals/native/run.py` remains diagnostic/reproduction tooling. Browser, review,
new-project and lifecycle cases are not yet part of this Lab suite.

Real model trials run from an external terminal/worker under the Lab's documented
execution boundary. This increment tests the integration with explicitly fake
Codex; it contains **no new inference trials or effectiveness claims**. CLI
execution and user-facing skill usefulness require different evidence.

## Verification

- Native tests: 11 PASS (6 new Lab integration tests + 5 existing runner tests).
- Package tests: 5 PASS; actual ZIP extracted and its manifest verified.
- Extracted START: 48 combinations, cards/help, clipboard API stub and real
  selection fallback, 390/1280 px; screenshots viewed, no page errors or requests.
- Plugin and both skills validate. Python/JS syntax, Native CI YAML and pinned
  read-only actions checked. Remote CI was not run in this increment.
- Full repository result and remaining historical failures are recorded in the
  [maintenance report](../../reports/native/2026-09-19-maintenance/REPORT_RU.md).
- Integrity check passes with the two pre-existing generated-cognition warnings.
  The larger 26-check verifier was not rerun; prior 24/26 is historical evidence.

ZIP: `Playbook-0.1.0-preview.4.zip`, 34,624 bytes, 19 files.
SHA256: `58bde061d9d90f312ccc992b63eae68816d23a1da31c49ee44055d34bcf723b9`.
Local build: `.playbook-artifacts/native-maintenance/preview4/`.
No logs, tests, reports or lab tools enter the subscriber archive.

## Remaining work

1. Complete the actual desktop newcomer first run and real OS clipboard check.
   Prior CLI discovery/lifecycle and agent/browser examples are not substitutes.
2. Decide reuse/distribution rights, then conduct the [small pilot](../native/PILOT_RU.md).
3. Execute matched real trials through the new Lab integration externally; read
   per-task failures and final claims. Aggregate false-success metrics do not
   grade Native natural-language claims. Then add targeted frontend/review cases.
4. Address the known frozen-pilot/toolchain mismatches separately; do not rewrite
   old evidence to make the current checkout green.

Prior [onboarding results](../../reports/native/2026-09-19-onboarding/REPORT_RU.md)
include successful clean-container lifecycle/discovery, a full agent/browser
example, and failed model skill-reading attempts. Preserve those distinctions.
