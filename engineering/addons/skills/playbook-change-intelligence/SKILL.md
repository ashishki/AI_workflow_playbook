---
name: playbook-change-intelligence
description: Explain the behavioral and architectural consequences of a selected PR or revision range. Use explicitly for owner catch-up or pre-merge understanding, not as an automatic code-writing or publishing workflow.
---

# Understand the change

Read the project's existing instructions. Resolve repository, base, target and
local modifications; distinguish merged source from a deployed service. Ask only
for a scope decision that cannot be established from available facts.

Start with the diff and existing state. Trace affected callers, data, permissions,
error paths and tests only as needed to answer the owner's question. Investigate
more deeply when evidence reveals a material uncertainty, not because a report
has many headings. One primary agent is the default; no mandatory delegation.

Explain before/after behavior, why it matters, what could break, and the next
owner decision. Separate documented rationale, your inference, confirmed defects,
potential risks and unknowns. Attach exact paths/revisions or other evidence to
important claims. Tests read are not tests run. Agreement between agents is not proof.

Use the existing state/decision record. Propose an update unless writing it is
within the assignment; never create a competing knowledge system or advance a
checkpoint beyond examined changes. A checkpoint must include repo and revision.
Changed branch/history or dirty files require rechecking it, not blind continuation.

Finish with a short owner summary and only the code locations worth attention.
Do not expose private data, secrets or raw internal chats. Missing evidence remains
visible. This explanation is not independent review or merge authorization.
Do not edit code, create issues, commit, push, merge or deploy under this skill alone.
