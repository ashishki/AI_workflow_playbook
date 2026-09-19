---
name: playbook
description: Start or steer Playbook work when the user invokes Playbook, asks to connect it, or asks it to choose a workflow. Infer project context, create/fix/check intent and automatic/plan-first/extended control. Do not activate for every unrelated code edit.
---

Provide one entry to the project. Accept the user's ordinary task description;
make the working approach understandable without requiring a process form.
Preserve existing authorization, project instructions and the user's changes.

## Choose a useful approach

Read enough of the current directory, instructions and project to resolve three
independent dimensions. The user's explicit choices override your suggestions.

| Dimension | Choices | Default inference |
|---|---|---|
| Project | New / existing | Inspect files and the task; a new feature in an existing repo is still an existing project |
| Action | Create / fix / check | Infer the requested outcome, not just a keyword |
| Control | Automatic / plan first / extended | Automatic for clear local work; recommend extended for material auth/data/payment/migration risk |

Briefly state the proposed approach and why, for example:
"Existing project · fix · automatic. I'll reproduce the mobile issue, make the
change and check the form in the browser." Continue when intent is clear.
Do not turn this announcement into an extra approval gate. The user can change
any dimension in ordinary language, including while work is in progress.

If no task was supplied, ask one short question about the desired outcome.
Offer optional examples: create a new project, fix an existing bug, check a
result. Do not require the user to select all three dimensions. If a supposed
new project targets an occupied folder, preserve its contents and resolve the
actual destination before scaffolding. Do not invent business requirements.

## Honor the selected control

- **Automatic:** choose a proportional plan, implement, verify the real outcome,
  fix observed problems and present the result. "Quick" means this mode with
  less ceremony; it does not remove verification, project policy or permissions.
- **Plan first:** inspect and clarify the task, then present the proposed changes,
  acceptance checks and material choices. Stop before implementation. Do not
  write project files, install/connect the package, or persist a plan unless
  separately requested. Continue implementation only when the user requests it.
- **Extended:** make acceptance criteria and material risks explicit, add relevant
  negative/regression checks and a focused fresh review when available and
  authorized. State what extra checks are justified. If independent review is
  unavailable, disclose that limitation. Do not invent a reviewer or import a
  full governance framework. Existing policy determines consequential approvals;
  the mode itself does not demand approval for every local step.
  Keep criteria and findings in the conversation unless a report file was
  requested. Prioritize defects affecting the task; do not expand into an
  unrelated audit just because extended control was selected.

Control applies independently of action. **Check** inspects and tests, and reports
findings; it does not fix source code unless the user asks. Temporary evidence
is allowed when consistent with the user's scope. "Plan first + check" means
propose the review plan and stop before executing it. An explicit request to
only inspect must never turn into automatic installation or implementation.

## Connect only when needed

For a connect/update/remove request, read [connection instructions](references/connect.md).
For a first implementation task through Playbook in an unconnected repository,
use those instructions to establish the small project block and available skills,
then continue. Skip reconnection in an already connected project. If another
mandatory workflow conflicts, resolve that conflict without silently weakening it.

Plan-only and check-only requests do not authorize setup writes. The installed
plugin can guide those tasks without a repository block. If invoked from a source
checkout, the reference explains how to copy only the two skill folders.

## Deliver and verify

For rendered UI implementation, use `playbook-frontend` when available. For a
check-only UI task, read [browser checks](../playbook-frontend/references/browser-check.md), preserving the no-fix
boundary. For other work, use relevant project checks; do not launch a browser
for backend-only or prose changes. Reuse existing skills/tools instead of
installing a catalogue. Missing capabilities are named gaps, not a pass.

Present the result appropriate to the chosen action: implemented outcome, plan,
or findings. Include actual verification, remaining limitations, and a useful
next step only when work remains. Keep process metadata out of the final answer
unless it helps the user understand a real decision.
