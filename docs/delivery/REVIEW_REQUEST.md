# Independent delivery review request template

The implementer fills this with actual facts in a new ignored artifact. This
file is not an executed review or an approval. Do not load unrelated history.

## Actual scope

- Repository and root:
- Baseline: 0c4027f8ecfc0b086c39613bb8c83a91b962d139 (refresh if scope changed).
- Reviewed commit and source tree; working-tree delta, if any:
- Current D-step and acceptance criteria from docs/delivery/PLAN_RU.md:
- Changed paths and affected consumers:
- Observed commands/results and evidence paths; not-run checks:
- Permissions, supported environment and declared threat boundary:
- Known baseline defects and prior findings:

## Review responsibilities

Read actual code and relevant project rules. Check requirement coverage, real
Engineering/Product/Shared consumers, data/permission boundaries, compatibility,
negative cases and whether tests could miss the defect. A report's existence
is not its truth; a CLI found in PATH is not usable authentication/execution.

Reviewers are read-only. Do not fix, commit, push, install tools, modify global
configuration, spawn another reviewer, contact users, or grant release/approval.
Findings must cite affected code and a reproducible condition or explicit unmet
requirement. Distinguish confirmed blockers, advisory gaps, accepted owner risks
and untested claims. Avoid expanding a local helper into an unrequested platform.

Return findings with severity and evidence, false-positive dispositions, scope
limits and required rechecks. The native runner adds the selected role's output
contract. Do not claim provider identity or tests that are not observable.
