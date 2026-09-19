# Observation record: connection agent

This is the evaluating agent's factual account, collected after execution;
not a machine-exported event trace. Paths were synthetic scratch workspaces.

Initial independent task connected an existing Python project with root
AGENTS.md, effective AGENTS.override.md and an uncommitted slugs.py change.
Only the override was extended (one block and a project test note), plus six
skill files: playbook/{SKILL.md, agents/openai.yaml, assets/project-block.md,
references/connect.md} and playbook-frontend/{SKILL.md, references/browser-check.md}.
Installed bytes matched source. The pre-existing instruction text and other
user files were preserved. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v`
passed one test; `git diff --check` passed.

Reconnect was the next invocation in the same session: no bytes, modification
times or file modes outside .git changed. A client restart was not tested here.

Update was another continuation. The fixture author had added a user line:
`User customization: use the existing project color palette.` The source had a
compatible update: `Source update probe: keep layout examples local.` Only the
installed frontend SKILL.md changed; both lines and prior content remained.
Other five payload files and the block matched source. Other project files
were unchanged; diff check passed. Application tests were not rerun.

The original remove deleted the block, four entry-skill files and the frontend
browser reference. The customized frontend SKILL.md was left active. The agent
reported incomplete removal and a missing reference. This was a product failure;
the preserved file was still discoverable in .agents/skills.

The parent revised the canonical removal reference. The same agent then tested
a new fixture containing the current skills and customized frontend instructions.
This was a follow-up regression, not a fresh independent evaluator. The complete
frontend folder (SKILL.md and reference) was saved to
`.playbook-saved/skills/playbook-frontend/`. Bytes and permissions were compared
before removing the active copy. Four unchanged entry-skill files and only the
marked block were removed; the useful project note remained. No active Playbook
SKILL remained in the inspected project discovery roots. Other user files,
permissions and the uncommitted change were preserved. Diff check passed.

The parent separately compared before/after hashes and the complete backup.
These agent passes do not prove fresh client discovery after removal, plugin
installation or browser capability. Those have separate evidence in the report.
No downstream, global configuration, source package, external account or model
was changed by this evaluating agent. No additional dependencies or commits.
