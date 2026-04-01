# Heavy-Task Mode

The default loop should stay light for ordinary work.

Heavy-task mode is a selective proof-first extension for tasks where normal tests plus ordinary review are not enough evidence.

## When To Use It

Good candidates:

- security boundary changes
- data migrations or destructive modifications
- retrieval semantics or evidence-policy changes
- unsafe tool behavior
- broad refactors with high blast radius

Bad candidate:

- ordinary CRUD or adapter work that already has clear tests and normal review coverage

## Goal

Give risky work a durable proof lifecycle without turning the whole playbook into ceremony.

## Recommended Pattern

For a heavy task, add explicit proof expectations to the task entry and keep task-local artifacts such as:

- frozen scope / acceptance criteria snapshot
- evidence notes or metric snapshot
- verifier focus points
- explicit completion verdict or verifier note

The exact filenames can be project-specific. The important property is that the evidence is durable and task-local, not just buried in chat history.

## Minimal Loop

1. Freeze what is being proved.
2. Implement the task.
3. Collect evidence.
4. Run fresh verification.
5. Record verdict.

## What This Is Not

- not a mandatory mode for all tasks
- not a second orchestration framework
- not a reason to duplicate all normal review artifacts

Use it where the cost of false confidence is high.
