# Establish capabilities without changing the user's machine

First use the capabilities exposed by the actual host session. Do not make the
owner debug tool names. Explain what is missing, what remains possible and the
smallest next step.

## Managed Desktop setup

If `.playbook-setup/runtime.json` exists, treat its command as the local helper
location only. It does not authorize network, publication or external writes.

The setup window can distinguish:
- managed Playbook files verified/modified;
- managed Codex binary launched/not launched;
- CLI login reported/not confirmed.

Those states do **not** prove a live reviewer, browser, integration or business
effect. Close those gaps with the real Role Runner/browser/integration workflow.

The helper can run the canonical inventory without requiring system Python:

    <local-helper> helper inventory --root <project> --json

If independent review is needed and no suitable CLI is available, the Desktop
setup can offer one pinned per-user Codex runtime. Download/install and login are
separate owner-confirmed actions. Never copy an existing token or disable account
restrictions.

## Manual/plugin route

When Python is available, the bundled inventory remains available:

    python /path/to/playbook/scripts/playbook_environment.py --root /project --audience product --json
    python /path/to/playbook/scripts/playbook_environment.py --root /project --need review --need browser --json
    python /path/to/playbook/scripts/playbook_environment.py --root /project --need preview --json
    python /path/to/playbook/scripts/playbook_environment.py --root /project --need claim --json

It checks named paths and executable/module presence only: no network, subprocess,
credentials read, installation or project write. Presence is not readiness.

For external preview, `--need preview` only inventories the adapter; live tunnel
execution still needs explicit permission and a real check. Claimable deployment
similarly does not accept Terms, log out an account, create resources or prove
authorization.

Never retry an access denial through another filesystem route, install every
possible tool preemptively or weaken protection to satisfy a check. Discovery and
planning may continue honestly when execution is unavailable.
