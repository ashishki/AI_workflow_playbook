# Handoff: Playbook Native preview.5

Updated 2026-09-19. Branch `docs/codex-frontend-skills-mcp-20260919`.
This increment starts at `eedeaf3`; original proposal base `d070f4e`.
Master remains `d570163`; no downstream changes, public release, licensing change,
host configuration change or subscriber contact.

## Current result

A [small offline kit](../../distribution/native/README.md) provides a prepared
project with two skills and a short block. Users work in **Codex**. START.html
explains the first run and optionally builds a prompt; it does not run an agent.
The same source package supports native plugin installation for existing projects.

The dimensions stay independent: new/existing; create/fix/check;
automatic/plan-first/extended. Quick reduces ceremony and retains verification.
Namespaced plugin skills and repo-local skills have different technical names;
the plain-language user entry remains “Playbook, помоги с задачей”.

The root README is short and in Russian. The long Governed reference moved to
[docs/governed](../governed/README.md); its mechanisms and frozen pilots are retained.
Forty-five historical Native artifacts were removed from the current tree after
byte verification against `b80eb56`; [pinned archive links](../../reports/native/README.md)
preserve access. No Git history was rewritten. Old preview.3 downloads are intact.

The user chose **automatic Role Runner** and **Windows, macOS and Linux**.
The existing engine has a portable Native profile: compact request, no governed
renderer/registries, no Git prerequisite. Canonical code stays in `tools/`; package
copies must match. One focused review follows code changes, including quick mode;
plan-only writes nothing. Python 3.10+ and authenticated Codex CLI are required.
Missing/denied review is disclosed, never upgraded to PASS or retried by weakening access.

## Current development route

Use [the short author protocol](../native/DEVELOPMENT_RU.md): observed problem,
small change, explicit acceptance, evidence, decision. **Existing Harness Lab**
owns new comparisons. Ground Truth Lab is deferred by the user.

[Native suite](../../evals/native/harness/README.md) connects backend, plan, review
and frontend through Lab's command adapter. It supports plain Codex or a previous
Native package as baseline. Added telemetry sums primary and captured reviewer
tokens, retains unknown counters and avoids double-counting latency. Original
`evals/native/run.py` remains diagnostic/reproduction tooling. New-project and
lifecycle probes remain separate. No second lab is created.

Real model trials run from an external terminal/worker under the Lab's documented
execution boundary. Explicit user authorization permits a maintainer to launch
the worker on copied fixtures. Task agents must not launch experiments recursively.
This increment includes actual model diagnostics; see the
[autoreview report](../../reports/native/2026-09-19-autoreview/REPORT_RU.md).
They do not establish an effectiveness or token-saving percentage for Native.

## Verification

- Native tests: 13 PASS (8 Lab integration tests + 5 existing runner tests).
- Package tests: 11 PASS, including 6 tests of the actual bundled Role Runner with fake CLI.
- Extracted START: 48 combinations, cards/help, clipboard API stub and real
  selection fallback, 390/1280 px; screenshots viewed, no page errors or requests.
- Plugin and both skills validate. Remote Native CI passed on all three OSes;
  the second run also produced byte-identical ZIPs after fixing Windows metadata/line endings.
- Full repository result and remaining historical failures are recorded in the
  [current report](../../reports/native/2026-09-19-autoreview/REPORT_RU.md).
- Integrity check passes with the two pre-existing generated-cognition warnings.
  Full pytest: 226 passed, 12 skipped, the same 2 frozen-pilot failures. A subsequently
  added scorer-classification test passed separately. The broader validator also
  reports 6 pre-existing missing historical task references; do not claim all-green.

ZIP: `Playbook-0.1.0-preview.5.zip`, 64,264 bytes, 26 files.
SHA256: `052609d7c6f5f7fa6756f8f6669d7776bbf56c89f818192147fe9491e2cde24e`.
Local build: `.playbook-artifacts/native-autoreview-v2/kit/`.
No logs, tests, reports or lab tools enter the subscriber archive.

## Remaining work

1. Complete the actual desktop newcomer first run and real OS clipboard check on all three OSes.
   Prior CLI discovery/lifecycle and agent/browser examples are not substitutes.
2. Decide reuse/distribution rights, then conduct the [small pilot](../native/PILOT_RU.md).
3. Complete the automatic implementation/review/fix loop in a host that legitimately
   supports the reviewer process. Standalone real review found the fixture defect;
   nested CLI is blocked by read-only service-state access in this eval host.
   Aggregate false-success metrics do not grade Native natural-language claims.
4. Address the known frozen-pilot/toolchain mismatches separately; do not rewrite
   old evidence to make the current checkout green.

Prior [onboarding results](../../reports/native/2026-09-19-onboarding/REPORT_RU.md)
include successful clean-container lifecycle/discovery, a full agent/browser
example, and failed model skill-reading attempts. Preserve those distinctions.
