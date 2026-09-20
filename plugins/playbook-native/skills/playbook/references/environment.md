# Establish capabilities without changing the user's machine

First use the tools that this actual session exposes. A desktop login is not
proof that a child CLI is authenticated; a skill is not a browser. Do not ask
an owner to debug tool names. Explain the consequence and a specific next step.

If Python is available, the bundled read-only inventory can help:

```text
python /path/to/playbook/scripts/playbook_environment.py --root /project --audience product --json
python /path/to/playbook/scripts/playbook_environment.py --root /project --need review --need browser --json
```

Resolve the helper from this skill's installed location. It only checks named
paths and module/executable presence: no network, subprocess, credentials read,
installation or project write. Exit 0 means an inventory, not ready-to-use.
Exit 1 means requested prerequisites are missing or live checks remain pending;
this is expected for requested browser/review until separate execution evidence
exists. Exit 2 is an invalid input/environment inspection error.

Do not repeatedly invoke it hoping that authentication or a browser will become
verified. To close those gaps use the actual authorized Role Runner and browser
workflow. Never turn a denial into full-access, reuse somebody else's profile,
copy credentials, create a public tunnel, or install all possible alternatives.

For each blocker say what is affected, what remains possible and the smallest
specific setup decision. Offer one supported route. Project dependencies may
be installed only within the task's permissions, not as a hidden setup side
operation. Preserve existing local changes and managed/global environments.
If execution is unavailable, discovery or planning may continue honestly; do
not claim the code or UI was checked. Package tests do not establish user setup.
