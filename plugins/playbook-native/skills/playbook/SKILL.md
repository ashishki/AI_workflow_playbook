---
name: playbook
description: Start or steer Playbook work when the user invokes Playbook, asks to connect it, or asks it to choose a workflow. Infer project context, create/fix/check intent and automatic/plan-first/extended control. Do not activate for every unrelated code edit.
---

Work in the user's coding agent and project. Accept an ordinary task description;
no launcher, generated prompt, role selection or process form is required.
Use the project's conventions and available tools. Ask only when missing intent
changes the result; keep existing authorization and user changes intact.

## Scope and control

Infer new/existing project, create/fix/check, and automatic/plan-first/extended
control from the task and files. A new feature can belong to an existing project.
Explain your approach briefly in the user's language, then continue. The user
can change any choice in chat; do not ask for approval of routine local work.

- Automatic is the default for clear work. Quick reduces ceremony and retains checks.
- Plan-first presents the proposal and stops before implementation or file writes.
- Check-only reports findings without fixing source or installing the package.
  Temporary evidence must fit the user's scope. Plan-first + check proposes the
  review and stops before carrying it out.
- Extended adds checks justified by the task's risks; it does not add approval gates.

For connection/update/removal, read [connect](references/connect.md). Use it for
an unconnected project's first implementation task, then continue that task.
Do not reconnect an already connected project or weaken its required workflow.

## Deliver a usable result

Check the user's actual outcome, not only a component's passing test. Follow the
changed flow to its observable result using the available tools. Distinguish a
local example, saved data, a working external integration and a published service.
An unavailable part remains an explicit limitation. Do not invent business rules.

For UI implementation use `playbook-frontend`; for a check-only UI task read its
[browser checks](../playbook-frontend/references/browser-check.md) without fixing code.
Use relevant project checks for other tasks. Reproduce observed defects, fix them,
and check the final state. Avoid new process files unless needed to continue work.

After code changes use the included [Role Runner](references/review.md) for one
focused independent review, also in quick mode. Address confirmed findings and
recheck. Plan-only writes nothing; reviewers never start other reviewers. If the
host lacks or denies review, disclose it and preserve its evidence. Tests and
checking the running result remain the main agent's responsibility.

End with the result, a useful way to open or use it, actual checks, and unresolved
limitations. Explain these in ordinary language; the user need not read logs or
know the tools' names. Continue later in the same project, using its saved state.
