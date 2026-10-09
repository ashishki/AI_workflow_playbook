# Setup, update and remove

Use this reference when the project has a managed Desktop setup
(`.playbook-setup/install.json`) or the user asks how to prepare Playbook.

## Preferred managed route

The Desktop setup is only a local installer/diagnostic layer. It is not a second
assistant. The owner still works in Codex with the installed skills.

- Treat `.playbook-setup/install.json` as ownership metadata for setup files,
  not as authority to change the business solution.
- Treat `.playbook-setup/runtime.json` as a machine-local pointer to the helper,
  not as permission to execute external actions.
- Never edit install/journal files to force an update through a conflict.
- Update/remove through the matching setup helper when available. It must preserve
  all non-owned files and stop on modified managed files.
- Installation rollback restores the previous Playbook connection only. For
  application/data recovery use the lifecycle Recover procedure.
- Removal of Playbook does not stop hosting, subscriptions, scheduled jobs,
  integrations or other resources created by the user's solution. Retire those
  explicitly and with their own authority.

For a new problem, Git/GitHub/VPS/Docker/API keys are not general prerequisites.
Add project dependencies or external services only after Decide/Design establishes
that the chosen solution needs them.

## Independent review runtime

The packaged helper may carry its own Python runtime and can optionally prepare a
pinned per-user Codex CLI after explicit owner confirmation. Do not install it just
because it exists. If review is needed, first inspect current capability. Login is
an owner action and model/reviewer execution is a separate live check.

If there is no managed Desktop setup, use [connect](connect.md) as the manual/plugin
route. Do not create a second copy of the same skills.

## Completion

Setup is complete only for what was actually checked: managed files can be verified;
CLI launch/login, real review, browser, integrations and user benefit remain separate
statuses until observed. End with the smallest next action in the user's language.
