# Playbook Native — preview

Two skills and a small project instruction block: connect a repo, ask for a
change, let the agent implement it and check the real result.

This is a source package for evaluation, **not a published or user-validated
release**. The repository has no project-level reuse license; see
[Legal Status](../../docs/LEGAL_STATUS.md). No new permission is granted here.

| Component | Responsibility |
|---|---|
| `playbook-setup` | Connect/update/remove the repository instructions and discover existing commands |
| `playbook-frontend` | Implement UI, exercise it in a browser, inspect appearance, fix observed defects |
| Project block | Small always-loaded expectations in the effective `AGENTS.md` or override |

The package has no executable scripts, hooks, MCP servers, model settings,
external account dependencies, or auto-update behavior. It does not copy the
governed Playbook into a user's project. Skills guide the agent; they do not
enforce permissions or guarantee good results.

## Try the source package

In an authorized scratch repository, ask the agent to read
`plugins/playbook-native/skills/playbook-setup/SKILL.md` from this checkout and
connect the current repository. Use an absolute source path. The setup skill
copies the two skill folders only when an installed plugin does not already
supply them, and preserves existing project instructions.

Then start a new session if needed and ask for a real change, for example:

```text
Исправь форму подписки: на узком экране кнопка выходит за границы.
Проверь отправку, ошибку валидации и внешний вид в работающем приложении.
```

See the [Russian quick start](../../docs/native/QUICKSTART_RU.md) for capability
checks, troubleshooting, and removal. Installation in downstream projects is
not part of authoring this package.

## Distribution boundary

The manifest uses the supported `.codex-plugin/plugin.json` compatibility
layout. It can be packaged through native plugin distribution after release
checks and a licensing decision. No marketplace entry, global configuration,
or plugin installation is created by this repository change. A directory
containing a manifest is not an installed plugin.

Repository-local `.agents/skills` is the fallback using the same source files,
not a separately maintained implementation. Do not install both routes.
Desktop browser availability, CLI browser setup, and plugin installation need
separate host-level smoke tests; static validation is not proof of discovery.

[Product decision](../../docs/research/CODEX_FRONTEND_SKILLS_MCP_ADOPTION_RU.md)
and [delivery plan](../../docs/research/CODEX_FRONTEND_IMPLEMENTATION_PLAN_RU.md)
define the release boundary and tests still needed.
