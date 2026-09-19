# Playbook Native — preview.3

One entry: describe a task in ordinary language, beginning with “Playbook”.
The agent infers new/existing project, create/fix/check intent and
automatic/plan-first/extended control. Explicit choices win. Quick work retains
verification while reducing ceremony. Beginner instructions explain what to open,
what works and what remains, without requiring framework or workflow expertise.

This is a **private evaluation candidate**, not a public or newcomer-validated
release. See [Legal Status](../../docs/LEGAL_STATUS.md); no new reuse rights are granted.

| Component | Responsibility |
|---|---|
| `playbook` | Single entry and control boundaries; connection reference only when needed |
| `playbook-frontend` | Implement UI, exercise it, inspect appearance and fix observed defects |
| Project block | Small always-loaded expectations in the effective AGENTS file |

Six skill payload files including UI metadata; one 22-line project block, plus
brief verified project facts when useful. No installed runtime, hooks, MCP servers,
model settings, external accounts or auto-update. Skills guide decisions; they
do not enforce permissions or guarantee outcomes.

## Try it

The [Russian quick start](../../docs/native/QUICKSTART_RU.md) starts with a small
[offline kit](../../distribution/native/README.md): extract, open `START.html`,
open the included `Мой проект` folder in Codex, describe a task. That folder
already contains exact repo-local copies of these skills. No terminal or hidden
file copying is needed for the first try. The kit does not bundle Codex itself.

For ongoing work in existing projects, the same source is a native plugin using
`.codex-plugin/plugin.json`. The start page contains the installation request.
Installed plugin skills were discovered as `playbook-native:playbook` and
`playbook-native:playbook-frontend`; repo-local skill names are unprefixed. Use
ordinary language or the host's actual skill picker instead of assuming a
universal `$playbook` alias. Never install both delivery sources in one project.

The page has no connection to an agent, project filesystem access or telemetry.
It composes a request; mode changes also work directly in conversation.

## Evidence and limits

[Onboarding trials](../../reports/native/2026-09-19-onboarding/REPORT_RU.md) record:

- Native CLI install/reinstall/update/remove and fresh-session discovery in clean,
  disposable Linux containers; host configuration and projects preserved.
- Agent connection/reconnection/update in a scratch project; a removal defect
  found and fixed by preserving a whole customized skill outside discovery.
- A fresh agent built a demo, used Chromium and screenshot inspection, fixed
  problems and explained double-click opening; a subsequent plan-only request
  left all files unchanged.
- Reproducible archive, file hashes and browser-tested start page.

Desktop installation dialogs, Windows/macOS extraction, real newcomer usability
and cross-host reliability remain unverified. A separate clean-container model
trial announced Playbook selection but could not read it because of tool failure;
that is not a successful skill execution. The earlier
[12 CLI trials](../../reports/native/2026-09-19/REPORT_RU.md) retain their failures.
No speed/quality advantage over ordinary Codex is claimed.

This branch does not globally install the plugin for the user, publish a catalog
or change a downstream project. See the [release plan](../../docs/research/CODEX_FRONTEND_IMPLEMENTATION_PLAN_RU.md).
