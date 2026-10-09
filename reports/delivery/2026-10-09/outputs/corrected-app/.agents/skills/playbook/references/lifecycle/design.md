# Design

Design the change, not an impressive technical object. Preserve existing constraints
and conventions. Define the main user action, rules, exceptions, data locations,
access, inputs/outputs and what must survive the next change. Include safe fallback,
diagnosis, restore and eventual exit early. Explain consequential decisions in
ordinary language: who sees data, what costs money, what can be undone.

For UI use the existing frontend skill, real content and a visual direction. Plan
loading/empty/error/success states and mobile/keyboard behavior. A design skill is
not a browser; beauty and functional correctness require different checks. Do not
change frameworks or install extra skills for decoration.

For a small change a short agreed approach is enough. For a complex project use
its existing Feature Workflow/required reviews and exact approvals; do not import
that machinery into every template task or waive an existing contract. Write
executable acceptance scenarios where feasible, including a failure/recovery case.

Deliver the behavior to build and how to judge it, with unresolved owner decisions.
Plan-only stops before file writes. Design scope is not deployment or data permission.
