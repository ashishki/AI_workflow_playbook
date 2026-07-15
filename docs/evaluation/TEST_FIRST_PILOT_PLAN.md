# Test-First Paired Pilot Plan

Status: frozen candidate plan; exact-scope approvals pending; real-project pilot not run.

## Claim Boundary

This plan compares a frozen current Playbook workflow with a frozen test-first
workflow on the same real project tasks. It defines evidence collection; it is
not evidence that either condition is better.

Keep three claims separate:

1. A scripted mechanism smoke shows that the harness, scorers, receipts, and
   comparison path execute. It says nothing about real-model behavior.
2. A completed minimum real-project pilot may support a directional decision
   for its frozen repositories, tasks, models, and run policy.
3. A stable or general productivity/quality claim requires a preregistered
   precision or power rationale and the achieved denominators, not merely this
   operational minimum.

The existing `playbook_core_v1` scripted bundles are claim level 1 only. They
must not be counted as pilot trials.

## Readiness And Owners

TFA-7.2 must not start until a human records all of the following in a frozen
pilot registry:

| Required owner or approval | Responsibility |
|----------------------------|----------------|
| Pilot owner | Freezes protocol, registry, exclusions, and amendment log |
| Repository/data owner | Approves each real fixture, snapshot, license, and redaction class |
| Budget owner | Approves model, CI, storage, and human-review ceilings |
| Holdout curator | Keeps protected cases and raw results outside agent context |
| Independent scorer/adjudicator | Freezes scorers and labels outcomes without condition-derived relabeling |
| Merge/adoption authority | Makes the recorded decision; agents and critics do not self-certify it |

Readiness also requires an external shell or CI runner, provider credentials,
the data-retention record, project-specific scorer commands, and enough approved
budget to execute both arms of every admitted pair. The candidate runner,
ChatGPT-subscription login, scorers, and local storage exist, but their exact
use and retention still require the frozen-scope approval. Until then, the run
status is `blocked - not run` and valid pilot runs equal zero.

## Project Fixture Registry

Selected candidate: the minimized `ashishki/shishki_bot` CI supply-chain suite
defined in `reports/test_first_pilot/shishki_bot_v1/PILOT_REGISTRY.md`.
It contains two real historical tasks: immutable GitHub Actions pinning from PR
#2 at base `59ff47bdbcfb32fb1f128fcf6ac37f6fa0bd8c26`, and the mutation-found
all-`uses:` allowlist repair from PR #3 at base
`5f9adb4f7421c7cc03e74c8dd30c127f3ecfd31d`. Only the relevant workflow,
supply-chain test, and staged public RED tests enter the fixtures. Exact
repository/data-owner approval is pending, so selection does not authorize a
model run.

The minimum directional pilot uses at least one human-approved real repository
with at least two representative project tasks. A second repository is preferred
when the intended adoption scope crosses projects.

Each task row in the frozen registry must contain:

- repository identity, immutable snapshot commit and content digest
- task ID/version, real-task provenance, task text, acceptance criteria, and
  allowed diff scope
- `Risk-Level` plus all public-test, critic, holdout, mutation, property, and
  visual routing declarations
- public verifier, independent scorer, expected failure taxonomy, and scoring
  rubric/version/digest
- holdout, mutation, property, and UI applicability with protected references,
  never restricted case contents
- fixture/toolchain/environment digest, data classification, redaction policy,
  retention class, and owner approval reference

Captured tasks must reflect the project's real risk surface. Generic example
tasks, generated placeholder fixtures, or the five `playbook_core_v1` mechanism
tasks do not satisfy this registry.

## Frozen Conditions

Use the harness labels as transport labels for these project-specific prompt
bundles:

| Harness condition | Frozen workflow |
|-------------------|-----------------|
| `baseline` | Current Playbook workflow as captured before the TFA-1 through TFA-6 test-first additions |
| `playbook` | Same workflow plus the applicable frozen TFA-1 through TFA-6 test-first routing, prompts, oracles, critic, and authority rules |

Do not weaken the baseline, remove its existing checks, or give one arm extra
task facts. Both arms receive the identical task text, acceptance criteria,
fixture snapshot, public verification contract, model ID/build and parameters,
adapter/CLI version, permissions, toolchain, environment, timeout, context and
correction budget, and retry policy. Freeze full prompts or prompt digests and
all scorer digests before the first run. Any material amendment creates a new
pilot version; it is not applied retrospectively.

The companion checks matching task/trial sets, repository, task-spec version,
and adapter version. Its immutable scheduling flags support a task filter,
logical trial start, and explicit append without overwriting evidence. It still
does not enforce matching model parameters, toolchain, permissions, run order,
prompt hashes, or budgets. The frozen registry, external adapter, runner, and
adjudicator own those fields.

For `shishki_bot_ci_v1`, the external contour freezes those additional fields.
The Codex CLI broker may contact the subscription service. The model shell
receives write access only to its copied fixture and read access
to the project `.venv` and Codex runtime; it cannot read sibling repositories or
the saved Codex auth file, and network/search are disabled. User config, rules,
apps, plugins, browser/computer use, and multi-agent features are disabled. Each
model adapter also runs inside a pinned Bubblewrap PID namespace, so ending the
wrapper ends its descendant process namespace before scoring; this layer does
not replace the model permission profile's file and network restrictions. The
post-model verifier and shell scorers execute through a separate Bubblewrap
sandbox with a read-only fixture, cleared environment, no host network, and no
access to the agent's writable namespace.

Before a full run executes manifest-listed Python, the pinned Bash/checksum
bootstrap matches the approval and critic records to the proposed manifest and
requires one terminal approval/ALLOW decision in each record. The runner then
checks every frozen asset, rejects added links or special entries in execution
trees, and uses an isolated no-site verifier to hash the complete regular-file
`site-packages` closure and pinned native executables. Cache and bytecode files
are redirected away from fixtures and are not part of that import closure. This
bootstrap uses a non-login shell, disables inherited Git system/global config,
templates and hooks, and runs its pilot tests without external plugins or
`conftest.py`. This is a host-specific local freeze, not independent attestation
of the host OS.

The approved evidence boundary is a trusted single-writer host with no
concurrent mutation of run or review inputs. The completed-run seal detects
ordinary added, removed, changed, linked, or special entries under that boundary;
it is not a signature and does not defend against the trusted host owner
rewriting and resealing evidence. A stronger claim requires a separate snapshot,
signature, or CI trust domain.
The frozen runner writes `COMPLETED_RUN.json` as its final run-root action after
all 12 bundles, governance files, and bundle manifests validate. The blind-review
preparer verifies that seal before reading evidence and again before it writes
review outputs; the protected mapping records the seal digest.

## Pairing And Minimum Trials

The paired unit is `(repository snapshot, task ID/version, trial index)`. Run
each arm from a fresh copy of the same snapshot using the same trial indexes.
Predeclare and record arm order. A comparative or adoption conclusion requires
counterbalancing by an external project runner. The frozen `shishki_bot` runner
uses task-filtered single-trial invocations with the preregistered AB/BA schedule
in its registry, balanced across six pairs. Do not call the order randomized:
it is deterministic counterbalancing. A generic fixed baseline-then-Playbook
batch still has the temporal-drift confound and forces `inconclusive`.

Operational floor for a directional pilot:

- one repository
- at least two project-specific tasks
- three valid paired trials per task
- two conditions
- a complete schedule of 12 separate Codex executions in total

Two repositories at the same floor require at least 24 executions. Prefer at
least three tasks per repository when budget permits. These counts avoid a
single-run comparison and exercise task variation; they are not statistical
sufficiency. Before execution, the pilot owner must preregister the exact task
count and any calibration denominators/thresholds required by
`CRITIC_CALIBRATION.md`, with a precision, power, risk, and budget rationale.

The frozen adapter-wrapper classification boundary treats its 1,200-second inner
limit as a valid `task_timeout` outcome and returns successfully so required
verification can score the resulting state. Other nonzero Codex CLI exits are
declared provider/CLI infrastructure failures and remain invalid. The harness's
1,260-second outer timeout is reserved for a hung or failed wrapper. The PID
namespace is the process-tree cleanup boundary for either timeout, including
descendants that create another process group or session. If later evidence
makes any cause ambiguous, preserve the attempt, mark the pair invalid/unknown,
and force the comparison decision to `inconclusive`; never silently exclude a
possible treatment failure.

An infrastructure-invalid arm invalidates the pair. It may be rerun only under
the frozen retry rule and remaining paired budget. Valid model/task failures
stay in the dataset. Every invocation writes to a new immutable pilot/attempt path;
never rerun into an existing output directory because the frozen runner
rejects colliding task/trial directories. Preserve all attempted runs and
exclusion reasons. Build a separate immutable comparison-input set containing
only admitted matched pairs, with source bundle paths and digests in its
manifest. Independent scorers and human adjudicators remain blind to condition
when the artifacts can be safely normalized.

## Metrics And Missing Values

The preregistration stores each metric's applicability, numerator, denominator,
source, threshold or report-only status, and missing-value rule. There is no
composite score. Report raw paired win/loss/tie rows plus per-task counts and
medians.

| Metric | Pilot definition |
|--------|------------------|
| Public test pass rate | Applicable valid trials whose frozen task-level public verifier reaches its expected pass state / applicable valid trials |
| Holdout pass rate | Sanitized protected `pass` results / all valid pilot trials whose frozen route resolves holdout to required; missing, stale, invalid, flaky, or contaminated required results are non-pass. Report executed optional holdouts as a separate slice |
| Mutation score | Killed valid non-equivalent mutants / valid non-equivalent mutants on preregistered critical modules |
| Property failures caught before merge | Target seeded or real invariant violations detected before merge / applicable target violations |
| Critic false-alarm and miss rates | Human-adjudicated known-good and seeded-defect rates under `CRITIC_CALIBRATION.md`, including required risk/category slices |
| Critic severity/link/usefulness | Separate severity accuracy, evidence-link accuracy, and repair usefulness; block rate is not a quality metric |
| Repair turns | Unexpected corrective attempts after the first implementation; the intentional RED step is not a repair turn |
| Time to green | Adapter start to first pass of the declared public verifier; also report time to the final required gate |
| Rollback/reopen rate | Human-approved merged tasks reopened or rolled back within the preregistered 14-day observation window / eligible merged tasks |
| UI behavior/visual evidence | Behavior pass and independently confirmed pre-merge visual defects only for tasks whose UI route applies |
| Safety and evidence | False-success, policy violations, evidence completeness/correctness, invalid-run rate, and required-gate failures |
| Cost and intervention | Cost per attempted/successful task, tokens, latency, tool calls, retries, and human intervention when measured |

Use `not_applicable` only from the frozen route. Missing telemetry is `unknown`,
never zero. A task that did not merge or whose observation window is unfinished
has rollback/reopen value `not_observed`, not a success. Cost, provider tokens,
rollback/reopen, and any event absent from validated evidence remain `unknown`
or `not_observed`; they are not inferred from agent prose.

The frozen `test_first_pilot.event.v1` append-only ledger records adapter bounds,
declared verifier commands, file-change events, first GREEN, repair candidates,
the model's final verifier observation, and the non-interactive intervention
policy. Events link pilot, attempt, condition, task, and trial IDs. They are
derived from Codex JSONL, so missing, malformed, or unmatched source events make
the related metric `unknown`. A `repair_candidate` means only that a verifier
failed after an observed file change; it is not proof of one correction turn.
The one-correction limit is prompt-level and is not process-enforced. The blind
outcome reviewer does not receive process telemetry; a separate adjudicator sees
it only from the protected mapping after the blind report is frozen.

## Budget Boundary

The initial executable budget remains zero until the budget owner records an
approval ID. The freeze candidate proposes a complete schedule and ceiling of
12 ChatGPT-subscription Codex executions, zero incremental paid API/CI/storage
spend, zero execution retries or model-judge executions, and stop-on-invalid
behavior. An early invalid or quota failure stops the schedule with fewer than
12 completed executions and an `inconclusive` result; it does not authorize a
replacement. Internal inference calls, turns, and context use within one agentic
execution are provider-managed and not bounded or represented as twelve calls.
USD 0 does not mean the ChatGPT subscription itself has no price. Approval must
confirm those exact ceilings plus:

- baseline inference, candidate inference, critic/judge calls, and failed attempts
- model/pricing snapshot, CI minutes, human-review minutes, storage, and total
  cost
- per-pair cost and correction/retry limits

Do not start a pair unless both arms fit the remaining budget. Every attempted
call counts. A budget increase, cheaper-model substitution, or reduced arm
budget is a protocol amendment requiring human approval and a new version when
it changes comparability.

## Retention And Redaction

Unless a stricter project/legal policy is recorded, use this pilot default:

- raw fixture copies, prompts, traces, receipts, bundles, and adjudication inputs:
  project ACL, then delete 90 days after the adoption decision
- sanitized comparison reports, manifests, digests, decisions, and deletion log:
  retain 365 days after the adoption decision
- raw holdout cases/results: curator ACL and the holdout rotation policy; never
  publish or copy into the agent workspace
- credentials and provider secrets: never retain in pilot artifacts

The project policy wins when it requires longer or more restrictive treatment.
PII, proprietary data, and secrets require repository-owner review and redaction
before execution. Record deletion owner, date, and evidence in the registry.

## Human Boundaries And Stop Rules

Named human approval is required for preregistration, real repository/data use,
paid or networked execution, credentials and permissions, protected holdout
access/export, critical-task execution, budget changes, protocol amendments,
actual merge, publication, and adoption. Seeded defects remain in isolated
fixture copies.

Stop and classify the pilot rather than silently repairing the protocol when:

- conditions are not comparable or a frozen artifact digest changes
- protected data leaks, a fixture is contaminated, or permissions exceed the
  approved boundary
- remaining budget cannot fund both arms of every admitted pair
- an invalid-run or retry ceiling is reached
- a required scorer, holdout, receipt, or adjudicator is unavailable
- safety or explicit stop-ship policy requires human escalation

## External Execution Commands

Run subscription-backed or networked command adapters from an external shell or
CI process, never from an active Codex Direct session. The frozen runner refuses
an inherited `CODEX_THREAD_ID`, clears the inherited environment, verifies the
approval and critic against the proposed manifest before frozen Python runs,
then checks the full asset/toolchain closure, ChatGPT login, CLI version,
execution count, and unique output path. It rechecks frozen assets, toolchain,
approval, and critic digests throughout the exact counterbalanced schedule.
After the approval record exists, a human operator runs:

```bash
export TFA_PILOT_APPROVAL_RECORD=/absolute/path/to/durable-approval.md
export TFA_PILOT_APPROVAL_ID=<approval-record-id>
export TFA_PILOT_ID=<new-immutable-run-id>
tools/run_test_first_pilot.sh
```

The static no-model check is safe in the current session:

```bash
tools/run_test_first_pilot.sh --preflight-only
```

After all twelve bundles validate, the review helper independently checks the
governance copies, exact schedule and identities, twelve non-overlapping valid
arms, one object-only raw Codex JSONL stream per arm, and exact reconstruction of
the append-only ledger. A custodian then prepares six condition-blind packages
and a separate protected mapping:

```bash
python3 tools/prepare_test_first_pilot_review.py \
  --run-root reports/test_first_pilot/shishki_bot_v1/runs/<pilot-id> \
  --review-output /reviewer-acl/<pilot-id> \
  --mapping-output /custodian-only/<pilot-id>
```

The local `0750`/`0700` directories and `0640`/`0600` files prevent accidental
sharing; they do not isolate two people using the same OS account. The custodian
must enforce a separate account or equivalent ACL so the reviewer cannot access
the mapping, raw run, prompts, traces, workflow labels, or process telemetry
until the report is frozen. Critic accuracy is not calibrated by these six
pairs, so the outcome critic remains advisory evidence rather than a judge with
measured reliability.

The helper stops after writing A/B packages and their protected mapping. It does
not freeze reviewer reports, enforce separate human identities, unblind results,
adjudicate invalid pairs, or build comparison input. The reviewer must freeze and
digest all six reports before the custodian releases the mapping. A separate
adjudicator then records the non-access attestations, joins labels, admits or
rejects each pair, and creates the immutable comparison input. Its manifest must
map every copied or linked bundle and report to the immutable source and digest;
do not edit bundle contents or reuse a path to make pairs compatible. Any access
leak, missing attestation, or unresolved pairing decision forces
`inconclusive`.

The project runner must additionally execute protected holdouts, stronger
oracles, UI evidence, critic calibration, and telemetry collection when their
frozen routes require them. `--fail-on-hard-gate` covers only the companion's
current policy and false-success gates. Any execution that does not match the
preregistered counterbalanced schedule is an amendment and remains
`inconclusive` until separately reviewed.

## Evidence And Decision

TFA-7.2 records the frozen registry and approvals, command receipts, every raw
bundle, bundle-validation output, protected-result summaries, validated event
ledger, paired metric table, invalid/excluded pairs, failures as well as wins,
and the observation-window state in `reports/test_first_pilot/`. The companion's
comparison report always labels itself a mechanism demonstration; the pilot
results document must apply this plan's separate human-adjudicated claim rules.

The adoption authority records exactly one result: `default`, `Strict-only`,
`optional`, `rejected`, or `inconclusive`. Missing approvals, minimum counts,
required telemetry, protected evidence, valid pairs, or observation windows
force `inconclusive`; they cannot be narrated into a positive result. Gaps become
canonical follow-up tasks in `docs/tasks.md`.
