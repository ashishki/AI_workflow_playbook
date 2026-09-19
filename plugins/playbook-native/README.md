# Playbook Native — preview.2

One entry: `$playbook` and an ordinary task. The agent infers new/existing project,
create/fix/check intent and automatic/plan-first/extended control. Explicit user
choices take precedence. Quick work keeps verification and reduces ceremony.

This is a source candidate with diagnostic runtime trials, **not a published or
newcomer-validated release**. The repository has no project-level reuse license;
see [Legal Status](../../docs/LEGAL_STATUS.md). No new permission is granted here.

| Component | Responsibility |
|---|---|
| `playbook` | Single entry, intent/control boundaries; connect/update/remove reference loaded as needed |
| `playbook-frontend` | Implement UI, exercise the running app, inspect appearance, fix observed defects |
| Project block | Small always-loaded expectations in the effective AGENTS file |

Five skill payload files; one 22-line project block, plus brief verified project
facts when useful. No executable runtime, hooks, MCP servers, model settings,
external accounts or auto-update. The evaluation tools and optional offline
[start page](../../docs/native/start.html) are outside the installed skills.
Skills guide behavior; they do not enforce permissions or guarantee results.

## Try it

Use the [Russian quick start](../../docs/native/QUICKSTART_RU.md). An installed
plugin supplies both skills. Source-checkout setup can copy the same two folders
to `.agents/skills` when the host allows it; never install duplicate copies.

Actual CLI trials loaded the repo-local skills. Agent-mediated installation into
protected `.agents` was denied: the revised setup leaves existing files intact
and does not add instructions for missing skills. Plugin install/remove has not
yet been validated; do not present the source-read path as universally working.

After connection, write `$playbook` and the task, or copy a request from the
start page. That page has no agent connection, repository access or telemetry.
The process can also be changed directly in conversation without a page.

## Distribution boundary

The manifest uses the supported `.codex-plugin/plugin.json` compatibility layout.
Native plugin distribution remains the intended release channel. This change
does not install the package globally or publish a marketplace. A synthetic
unregistered project marketplace was not auto-discovered by this CLI; this is
not a successful plugin installation test.

[Actual trials](../../reports/native/2026-09-19/REPORT_RU.md) distinguish model
runs, external browser checks and unresolved delivery limitations.
[Product decision](../../docs/research/CODEX_FRONTEND_SKILLS_MCP_ADOPTION_RU.md)
and [release plan](../../docs/research/CODEX_FRONTEND_IMPLEMENTATION_PLAN_RU.md)
explain what remains before subscriber distribution.
