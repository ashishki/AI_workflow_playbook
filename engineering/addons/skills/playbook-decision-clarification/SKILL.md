---
name: playbook-decision-clarification
description: Resolve material ambiguity in work rules or a technical decision before implementation. Use explicitly when the next safe step depends on a missing decision; do not interrogate the owner on every small change.
---

# Clarify enough to proceed

Read the relevant code, examples and existing agreements first. Reuse the project's
terms and decisions; do not ask the owner for facts the repository can answer.
Separate confirmed rules from hypotheses. Ask the smallest question or question
batch that could change the next decision, with a recommendation and its trade-off.

Test ambiguous terms against concrete normal, boundary and failure examples.
For example, distinguish a cancelled event from one that occurred but remains
unpaid rather than silently merging these into one state. Examples are hypotheses,
not observations of this owner's work. The owner decides business meaning.

Stop when the next bounded step is clear; defer non-blocking uncertainty with a
reason. A simple task may need no questions. Do not require every future branch
of the design to be resolved before starting useful work.

Summarize: intended behavior, what must remain unchanged, and how to check it.
Persist only meaningful terms/decisions in existing notes when writes are allowed.
Discussion or plan-only is not permission to edit files; otherwise propose the text.
No mandatory glossary, ADR, task ledger or new architecture.

When the implementation violates a valid rule, correct the implementation and
strengthen its regression check; never rewrite the rule to justify a bug. When
the owner changes a rule, update the agreement, implementation and checks together.
For test planning, choose observations capable of failing on the targeted mistake,
not assertions derived by copying the implementation. For an architecture proposal,
name the concrete future change it should simplify and preserve behavior evidence.

Do not implement, install tools, publish or expand permissions merely to answer a
question. Unresolved access/cost/irreversible decisions return to the owner.
