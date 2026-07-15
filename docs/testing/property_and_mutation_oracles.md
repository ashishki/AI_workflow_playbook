# Property And Mutation Oracle Guidance

## Purpose And Boundary

Property-based and mutation checks are task-routed supplements for high-value
deterministic logic. They are not mandatory Playbook dependencies, do not
replace public executable specs, and do not turn line coverage into proof of
fault detection.

Use project-native tools when they exist and the evidence value justifies their
runtime/cost. The examples below are illustrative, not install requirements.

## Decision Tree

1. Validate the task and resolve `Public-Tests-Required`, `Property-Required`,
   and `Mutation-Required` through
   `docs/testing/test_first_protocol.md §Deterministic Risk Routing`.
2. If no executable semantics change, use the declared concrete verifier.
   Property and mutation checks are not applicable unless an explicit route
   names a deterministic artifact/algorithm they must audit.
3. For executable semantics, keep the routed public example/contract test as the
   RED/GREEN inner-loop oracle. Stronger checks run in addition to it.
4. Evaluate the property predicate independently: is there a stable invariant
   over a broad input/state space with a reproducible generator and runner? If
   yes, require it when the field/risk floor says required; otherwise record why
   `conditional` resolved to not required.
5. Evaluate the mutation predicate independently: can a stable supported tool
   introduce controlled faults in the named critical logic, and can the suite
   detect them within a bounded budget? If yes, require it when routed; otherwise
   record the bounded rationale.
6. If both predicates apply, run both. Do not choose mutation merely because a
   property runner is unavailable, or vice versa; name the alternative evidence.
7. If a resolved-required gate is unavailable, flaky, or unaffordable within the
   declared budget, stop for a human-approved exception with compensating
   evidence. Do not downgrade after seeing a failure.
8. Run the exact predeclared commands and pass rules. Required property failure
   or an unaccepted actionable surviving mutant is stop-ship until fixed or
   handled by the governing policy.

## Applicability

Consider stronger oracles only where faults have material consequences or public
examples leave a real oracle gap:

| Target | Property candidates | Mutation candidates |
|--------|---------------------|---------------------|
| Critical algorithms/calculations | bounds, monotonicity, conservation, round-trip, equivalence | operators/branches that change formula, comparison, boundary, or rounding |
| State transitions | only allowed transitions, idempotence, terminal-state invariants | removed guards, inverted transitions, changed retry/timeout limits |
| Security/compliance/authorization | deny-by-default, non-leakage, tenant isolation, classification invariants | removed filters/checks, inverted predicates, weakened thresholds |
| Model routing/retrieval semantics | allowed-route, fallback, ACL, freshness, no-answer, source-mapping invariants | route/filter/threshold/fallback/evaluator logic |
| Agent retry/termination | finite bound, terminal outcome, no side effect after denial | changed caps, exit predicates, recovery branches, approval checks |
| Parsers/schemas/data contracts | valid/invalid partition, normalization, round-trip, schema preservation | validation branches, field requirements, comparison/dispatch logic |

Routine adapters, presentation-only changes, generated glue, or code already
covered by a complete deterministic contract usually do not justify both gates.
Explicit task metadata may still strengthen the route.

Do not property-test stochastic answer quality as if it were deterministic.
Properties may cover deterministic wrappers, schemas, citations, budgets,
permissions, routing, and failure behavior; capability quality remains in the
applicable eval artifact.

## Property Checks

A useful property names:

- the invariant and why it follows from the contract
- the generator/input domain and excluded invalid domain
- boundary, negative, and state-transition cases
- deterministic seed/replay and case/shrink budget
- exact runner/config and pass/failure rule

On failure, retain the seed and smallest shrunk counterexample when the tool
provides them. Add a public regression example when disclosure is safe, fix the
root behavior, and rerun the property. A non-reproducible or environment-caused
run is invalid evidence, not a product pass or failure.

## Mutation Checks

Scope mutation to named files/symbols and relevant operator classes. Exclude
generated/vendor code and deliberate equivalents before the run where possible.
Set timeout, concurrency, and runtime budget up front so the agent cannot expand
the task indefinitely.

Classify survivors:

| Class | Treatment |
|-------|-----------|
| `actionable` | The mutant changes required behavior and existing oracles miss it; add/fix the smallest appropriate oracle |
| `equivalent` | No observable contract behavior differs; retain adjudication evidence rather than forcing a test |
| `invalid` | Tool/build/instrumentation failure; repair the run and do not count it as a survivor/pass |
| `out_of_scope` | Mutation is outside the declared target; justify the exclusion and correct future config |

Do not prescribe a universal mutation score across stacks or tasks. Declare a
task-specific pass rule before the run: for example, no actionable survivors in
named authorization predicates, or a project-owned threshold backed by prior
baseline and exclusions. Do not lower it after seeing results. Killed-mutant
counts and line coverage are diagnostic context, not independent completion
authority.

## Minimum Evidence Contract

Record one row/artifact per gate:

| Evidence | Required content |
|----------|------------------|
| Routing | Declared -> resolved field, risk, predicate, and applicability rationale |
| Scope | Exact files/symbols/invariant or mutation targets, operator classes, and exclusions |
| Command/config | Exact command, config path/version, tool version, seed/case budget or mutation operators/timeouts |
| Pass rule | Pre-run threshold or explicit rationale such as zero actionable survivors in named critical logic |
| Result | Exit/status; property cases, seed/shrink/failure; mutation killed/survived/timeout/no-coverage/error and adjudication |
| Durable evidence | Receipt and report/artifact path tied to exact diff/commit and environment |
| Exception | For skipped resolved-required work: owner, reason, scope/blast radius, compensating evidence, expiry/follow-up, human approval |

Receipts report what ran. They do not certify oracle adequacy, merge readiness,
or empirical workflow improvement.

## Stack-Neutral Examples

| Stack/purpose | Example project-owned command shape | Notes |
|---------------|-------------------------------------|-------|
| Python property checks | `python -m pytest path/to/property_tests.py -q` using Hypothesis or equivalent | Record seed/profile/case budget in project config |
| Python mutation checks | `mutmut run` scoped by project config | Record target paths, operators/exclusions, timeout, and survivor adjudication |
| JS/TS mutation checks | `npx stryker run path/to/config` | Pin/configure in the project; do not add it to Playbook core |
| Data contract property | `jq -e -f path/to/invariant.jq artifact.json` | Useful for deterministic JSON invariants and receipt validation |
| JSON schema contract | project-native JSON Schema validator command | Record schema version and negative fixtures |

## Failure, Repair, And Authority

- Required property or mutation failure follows `docs/merge_authority.md`.
- Tool crashes, timeouts, invalid instrumentation, or unreproducible generation
  do not satisfy a required gate; the evidence owner repairs the runner.
- The implementer may add public tests for an actionable oracle gap but cannot
  self-approve an equivalent-mutant classification or accepted risk.
- An optional result is advisory and cannot silently become stop-ship.
- Bound correction turns and escalate recurring survivors/flakes rather than
  weakening assertions, generators, operators, thresholds, or scope.

## Claims Boundary

This guidance defines mechanisms and evidence fields. It does not prove higher
defect detection, better code quality, or faster delivery. Those claims require
recorded project-specific calibration and paired pilot evidence.

## Related Protocols

- `docs/testing/test_first_protocol.md`
- `docs/testing/holdout_acceptance.md`
- `docs/merge_authority.md`
- `docs/evaluation/CI_EVAL_GATE.md`
