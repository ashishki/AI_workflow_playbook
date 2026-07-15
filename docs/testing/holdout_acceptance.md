# Holdout Acceptance Protocol

## Status And Boundary

This is a stack-neutral governance protocol for project-owned restricted
acceptance evidence. It adds no secret cases, credential store, CI job, runner,
server, or required dependency to the Playbook repository.

Public executable specs remain visible to the implementer and drive the
RED/GREEN inner loop. A holdout is an independent phase/merge oracle whose cases
or exact expected outputs are withheld when visibility would create material
overfitting, contamination, or metric-gaming risk.

The mechanism is documented, not empirically proven to improve project outcomes.
Any improvement claim requires the paired pilot.

## Effective Classification

Resolve the task's `Holdout-Required` field through
`docs/testing/test_first_protocol.md §Deterministic Risk Routing`, then record one
effective classification:

| Classification | Use when | Completion treatment |
|----------------|----------|----------------------|
| `required` | The task/risk floor requires a restricted independent oracle and a feasible project-owned gate exists | Missing, stale, failed, invalid, flaky, or contaminated evidence does not satisfy the gate |
| `optional` | A restricted oracle could add independent signal, but the route and risk floor do not require it | Result is advisory; absence/failure cannot silently become stop-ship |
| `not_applicable` | There is no executable semantic surface, or withholding a duplicate oracle adds no meaningful independence | Use the declared public test/verifier and record the rationale; do not create placeholder holdout artifacts |

`conditional` is not a final state. Resolve it from the deterministic predicates
before implementation. In the machine-readable task record, `optional` and
`not_applicable` are both represented by `not_required` plus the explicit
effective classification and rationale.

### Risk And Mode

| Risk | Default holdout treatment |
|------|---------------------------|
| `low` | Not required; use only when explicitly selected for a concrete independent signal |
| `medium` | Optional when visible tests create material proxy/overfitting risk; required only by an explicit task/policy route |
| `high` | Required when public-test overfitting/contamination risk is material and a restricted oracle is feasible; otherwise record the deterministic rationale and human decision |
| `critical` | Required when a restricted executable oracle is feasible; infeasibility needs a human-approved exception, compensating evidence, owner, and expiry/follow-up |

Lean-Core does not gain a holdout ritual for routine low/medium tasks. A
high/critical task receives its task-local floor in any mode. Strict does not
manufacture a holdout for prose-only or genuinely non-applicable work.

## Roles And Information Boundaries

| Role | Receives | Must not receive/do |
|------|----------|---------------------|
| Implementer | Public contract, acceptance criteria, public tests, and sanitized failure category | Restricted cases, exact expected outputs, case-level repeated feedback, or direct runner access |
| Holdout curator | Restricted cases, expected outcomes, coverage map, version/rotation ownership | Implement the target change or reveal cases as repair hints |
| Trusted runner | Exact target commit, protected suite/config, credentials needed to execute, output-redaction policy | Expose cases/raw logs to the implementation context |
| Test Critic/consolidated review | Sanitized aggregate result, suite version/digest, evidence reference, contamination state | Inspect/disclose restricted cases unless separately authorized; infer pass from missing evidence |
| Human authority | Evidence map, exception/risk record, sanitized results, owner attestations | Convert a failed required gate to pass |

Independence requires separate role/context and evidence ownership. Another model
or vendor is optional.

## Storage And Access Contract

Each project chooses and documents a restricted, access-controlled location,
such as a separate private repository, protected dataset/artifact store, or
trusted CI environment. The public project records only:

- suite ID, version, and content/config digest
- curator and runner owner roles
- covered acceptance-criterion categories, without case contents
- trigger and protected command identity/alias
- allowed consumers and access-review cadence
- retention, rotation, and deletion rules
- sanitized evidence location and approval boundary

Do not store restricted cases, exact case IDs/expected outputs, raw failure
payloads, or access credentials in public task records, prompts, implementation
logs, Test Critic reports, issues, or this repository. A secret manager may hold
runner credentials; it is not a substitute for dataset access control.

## Execution And Evidence

Run required public checks first. The trusted runner then evaluates the exact
reviewed commit/diff through a project-owned protected command or scorer. Limit
case-level feedback and declare a rerun budget before execution to avoid turning
the holdout into an interactive training oracle.

The sanitized evidence record contains:

| Field | Required content |
|-------|------------------|
| Scope | Task ID, exact commit/diff, risk, and resolved holdout classification |
| Suite identity | Suite ID, version, digest, and curator/runner owner roles |
| Execution | Protected command identity, trigger, timestamps, exit/status, environment/tool digest |
| Result | `pass`, `fail`, `invalid`, `flaky`, `contaminated`, `missing`, or `stale`; aggregate counts only when disclosure-safe |
| Failure class | Public-safe category such as contract mismatch, invariant failure, infrastructure/scorer failure, or suspected contamination |
| Redaction | Confirmation that stdout, stderr, scorer metrics, traces, and artifacts were sanitized |
| Evidence reference | Restricted receipt/bundle reference plus a public-safe status reference |
| Authority | Gate owner and required human completion/merge approval; receipts do not assign readiness |

Existing `command_receipt` and `EvidenceBundle` shapes may be reused when the
protected wrapper can sanitize their artifacts and retain them under the correct
ACL. A hash proves artifact integrity, not that its contents are safe to expose
or that the task is merge-ready.

## Result And Failure Handling

| Result | Meaning | Required-route action |
|--------|---------|-----------------------|
| `pass` | The exact scope satisfied the current restricted oracle | Record evidence; continue to remaining gates/authority |
| `fail` | Valid execution found a product/implementation mismatch | Stop-ship; give only sanitized contract/category feedback, repair via public evidence, and rerun within budget |
| `invalid` | Runner, environment, credential, scorer, or evidence production failed | Not a product failure, but gate remains unsatisfied; runner owner remediates |
| `flaky` | Repeated authorized runs disagree without a product change | Gate remains unsatisfied; quarantine/repair the oracle and do not tune implementation to unstable output |
| `contaminated` | Cases/outputs were exposed or repeated tuning undermined independence | Invalidate the result, rotate affected cases/version, and review access logs |
| `missing` / `stale` | Evidence is absent or no longer matches suite/commit/contract | Gate remains unsatisfied; rerun the current suite against the exact scope |

The implementer must not fix a restricted failure by seeing the exact case. The
curator may translate it into a public requirement, invariant, or non-identical
regression example. If a case must be disclosed for diagnosis, retire it from
the active holdout and replace/rotate it before using the suite as independent
evidence again.

## Contamination And Rotation

Prevent contamination by:

- excluding cases, expected values, raw failures, and protected configuration
  from implementer prompts/workspaces and public logs
- separating curator/runner access from implementation authority
- returning coarse failure categories rather than case-level oracle queries
- bounding authorized reruns and logging access/execution events
- scanning evidence exports for restricted payloads before publication
- never copying holdout output into public tests verbatim while it remains active

Rotate the suite or affected slice after disclosure, suspected leakage, repeated
tuning, contract/schema change, stale coverage, benchmark defect, or scheduled
review. Preserve lineage: old version/digest, invalidation reason/date, impacted
receipts, replacement version, and curator approval. Do not delete historical
evidence needed to explain a prior decision; retain it under the restricted
policy.

## Exception Record

When a risk floor requires holdout evidence but no safe feasible oracle exists,
stop before implementation and record the exception allowed by
`docs/merge_authority.md`: task/gate, owner, reason, infeasible capability,
compensating deterministic evidence, scope, decision date, expiry/follow-up, and
human approval. An exception is `accepted_risk`, not `pass`, and cannot be added
after observing a failed required holdout.

## Project Integration Checklist

- [ ] Resolved classification and predicate are in the task/evidence map.
- [ ] Curator, trusted runner, storage ACL, access log, and rotation owner exist.
- [ ] Public contract gives the implementer enough information without cases.
- [ ] Protected command identity and sanitized status schema are documented.
- [ ] Exact commit, suite version/digest, receipt/bundle, and redaction state are recorded.
- [ ] CI/phase/merge policy distinguishes `fail` from `invalid` and optional from required.
- [ ] Required result is consumed by independent review and human authority.
- [ ] No empirical improvement claim is made without pilot evidence.

## Related Protocols

- `docs/testing/test_first_protocol.md`
- `docs/evaluation/CI_EVAL_GATE.md`
- `docs/agent_harness/HARNESS_EVALUATION_PROTOCOL.md`
- `docs/merge_authority.md`
