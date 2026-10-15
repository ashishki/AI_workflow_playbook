# Change

Reopen the real project, resolve current version, state, business rules and open
findings before changing it. Respect a new session's actual permissions; remembered
consent is not authority. Reuse existing notes, not a second independent task ledger.
Ask only about the changed rule and material ambiguities, not the whole history.

Before correcting a mismatch, distinguish an implementation defect, a confirmed
requirement change and unresolved business meaning. For a defect, keep the valid
requirement, fix the code/configuration and add or strengthen a regression check;
do not rewrite requirements or weaken tests to justify broken behavior. For an
owner-confirmed rule change, update the existing agreement, implementation and
checks together. For ambiguity, ask only for the missing owner decision rather
than inventing a rule. If the cause is not established, investigate or report the
blocker instead of changing the agreement to fit the current result.

Trace affected screens, stored data, integrations and users. Define old behavior
that must survive and a concrete new scenario. Plan data compatibility and rollback
before edits; test on safe copies. Update implementation/configuration, run relevant
regressions and the existing independent review for code. Explain and check the
result with the owner; update the same state only with observed facts.

For significant scope/rights/cost shifts return to Decide/Design. A new requirement
invalidates affected evidence; do not reuse old PASS as proof of the changed version.
Use [state helper](../state.md) when an existing JSON record benefits from mechanical
validation/snapshots; it is optional, not a mandatory new state system.

Evidence: new scenario plus preserved old cases/data, current version and open gaps.
A fresh assistant should be able to continue from these, not private conversation history.
