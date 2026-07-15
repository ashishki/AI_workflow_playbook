# AI Workflow Harness Lab

Standalone companion package for running reproducible baseline-vs-Playbook
workflow evaluations.

This package is intentionally separate from the core Playbook. It consumes
Playbook schemas and files, but it does not import root Playbook Python modules
and is not required for Lean/Standard/Strict adoption.

## Commands

```bash
harness-lab validate-suite suites/playbook_core_v1

harness-lab run \
  --suite suites/playbook_core_v1 \
  --condition baseline \
  --adapter scripted \
  --trials 1 \
  --output runs/baseline

harness-lab run \
  --suite suites/playbook_core_v1 \
  --condition playbook \
  --adapter scripted \
  --trials 1 \
  --output runs/playbook

harness-lab verify-bundle runs/playbook/task/trial-0/bundle.json

harness-lab compare \
  --baseline runs/baseline \
  --candidate runs/playbook \
  --output reports/comparison \
  --fail-on-invalid-run \
  --fail-on-hard-gate
```

The scripted adapter is for CI and mechanism tests. It is not evidence that the
Playbook improves real LLM behavior. Real-model runs require an installed CLI,
credentials, and an explicit budget.

Command-adapter examples are launched by an external shell, CI job, or harness
worker. Do not run them from inside an active Codex Direct project session,
because that would spawn nested Codex.

The command adapter propagates the real process exit code. Use
`--fail-on-invalid-run` during real experiments so missing commands, non-zero
adapter exits, timeouts, invalid evidence, and scorer failures fail the harness
pipeline. Use `--fail-on-hard-gate` with compare to fail on policy violations or
false-success above the configured thresholds.

`--fail-on-hard-gate` covers the companion's current policy/false-success
thresholds. It does not automatically make an arbitrary project holdout scorer
a merge gate; project CI must evaluate the protected result explicitly.

Tasks may declare `required_verification`; the harness runs that command after
the adapter finishes and stores a separate command receipt. Scorers should use
post-state and receipts, not agent prose, as their source of truth.

## Project-Specific Suites

`suites/playbook_core_v1` demonstrates the shared Playbook evaluation
mechanism. It is not evidence that the Playbook improves a specific project.

For a product or repository claim, create a project-specific suite with:

- representative fixture repositories or task states
- baseline and Playbook-Min prompts for the same task
- traps based on the project's real failure modes
- independent scorers for protected files, command receipts, diffs, tests,
  policy boundaries, and post-state invariants
- explicit pass/fail rules and expected failure taxonomy

Scaffolded directories are acceptable as a starting point. Automatically
invented benchmark content is not acceptable evidence.

## Paired Real-Project Pilot

The Test-First pilot uses a project-specific suite, not `playbook_core_v1`.
Within that suite, freeze `baseline` as the current Playbook workflow and
`playbook` as the same workflow with the applicable test-first additions. Pair
the same repository snapshot, task version, and trial index across conditions;
use at least two approved real tasks and three trials per arm for the documented
operational minimum.

Use an external project runner to alternate task-filtered, single-trial arms in
the preregistered order with `--fail-on-invalid-run`. Validate every bundle with
`harness-lab verify-bundle PATH` or the root validator's positional bundle path.
The harness does not counterbalance condition order or enforce matching model
parameters, permissions, toolchains, prompt hashes, and budgets automatically;
freeze and audit those in the external pilot registry. Use repeatable
`--task-id`, `--trial-start`, and explicit `--append`; existing trial paths and
run indexes fail closed, and a colliding trial is never overwritten. Do not run
compare until blind reports are frozen, a separate custodian unblinds them, an
adjudicator admits matched pairs, and a content-addressed comparison-input
manifest exists. A fixed baseline-then-Playbook batch remains `inconclusive`.

Freeze a project wrapper that records model/task terminal failures as valid
scored outcomes and returns successfully to the outer adapter. In the candidate
wrapper, the 1,200-second inner timeout is a valid task outcome; other Codex CLI
nonzero exits and the 1,260-second outer timeout are infrastructure-invalid. An
indistinguishable cause invalidates the pair and forces `inconclusive`; it must
not be silently excluded. The one-correction instruction is prompt-level and
does not mechanically limit internal model turns or context use.

The built-in comparison does not calculate the added test-first metrics and
leaves several productivity/cost fields `unknown`. The frozen project adapter
adds a schema-checked event ledger for verifier attempts and durations, but a
repair candidate is not proof of a correction turn and the prompt correction
limit is not process-enforced. Project scorers and later adjudication own those
interpretations. See
`docs/evaluation/TEST_FIRST_PILOT_PLAN.md` in the root repository. No real-project
pilot has been run in this repository.

The frozen `shishki_bot_ci_v1` candidate is a sparse real-task suite with two
public RED fixtures. Its static preflight does not call a model:

```bash
tools/run_test_first_pilot.sh --preflight-only
```

The full runner requires a durable exact-manifest approval and refuses to run
inside an active Codex session. It fixes ChatGPT-subscription auth, CLI/model
configuration, a copied-fixture-only model permission profile, read-only
networkless verifier sandbox, a PID namespace for complete model-process cleanup,
the full Python import-closure and native-tool digests, network/search denial, 12
Codex executions with no retries, and the counterbalanced schedule. The full run
checks approval and critic digests before executing frozen Python; its preflight
does not source login profiles, inherited Git config/templates/hooks, external
pytest plugins, or `conftest.py`. Preparing this suite and passing its mechanism
checks does not count as a real-model trial or an effectiveness result.

The completed-run seal operates under a trusted single-writer host boundary and
detects ordinary closure drift. It is not a signature or independent attestation;
concurrent mutation is a protocol violation, and stronger provenance needs a
separate snapshot, signature, or CI trust domain.
For the frozen `shishki_bot` runner, `COMPLETED_RUN.json` is written after the
bundle manifest and final governance checks. The review preparer verifies that
seal before and after package construction, then records the digest only in the
protected mapping.

After all twelve bundles validate, the project review preparer revalidates the
governance copies, schedule, identities, raw JSONL, and independently derived
event ledger before it creates six A/B packages and a separate protected
label/process mapping. Literal label removal and local file modes are not
sufficient isolation when reviewer and custodian share an OS account; use
separate accounts or equivalent ACLs and freeze the review reports before
unblinding.

The complete post-run sequence is: prepare packages and mapping; give only the
packages to the human reviewer; freeze and digest all six reports; have a
separate custodian release the mapping to an adjudicator; record non-access
attestations and pair admission; then create a content-addressed comparison
input. The helper performs only the first step.

## Critic Calibration Suites

A project-specific suite may pair known-good changes with seeded defects,
missing-evidence states, and explicit policy violations to exercise a Test
Critic. Keep ground-truth labels, expected findings, and disposition/basis
answers outside the critic prompt and agent workspace. Use opaque case IDs and a
locked calibration split distinct from prompt-development cases.

The command adapter can capture critic output and receipts, and a
project-specific independent scorer can validate structure/citations and compare
the frozen output with restricted labels. The companion does not natively
compute critic precision, recall, false-alarm, miss, evidence-link, severity, or
repair-usefulness metrics; the project scorer/adjudication step owns those
calculations under `docs/evaluation/CRITIC_CALIBRATION.md`.

Use the existing `baseline`/`playbook` conditions or a project-owned external
wrapper; there is no `critic` condition. Do not add invented seeded cases to the
public `playbook_core_v1` suite and present them as calibration evidence. Record
bank, prompt/model, taxonomy/policy, environment, budget, and scorer versions so
results are reproducible and authority stays bounded to the tested scope.

## Restricted Holdout Modeling

The current runner copies each suite `fixture` into the agent workspace, so a
hidden case or protected expected output must not live in that fixture. Keep the
restricted suite/config and its access credentials outside the public repository
and implementation context. A project-owned protected wrapper can run after the
adapter against the post-state and emit a sanitized status/receipt for an
independent scorer or CI policy.

The existing `required_verification` command already runs after the adapter and
produces a separate receipt, but command receipts retain stdout/stderr and shell
scorer metrics retain output excerpts. The protected wrapper must redact those
artifacts before any bundle or status leaves the restricted location. Store raw
EvidenceBundles under the appropriate ACL and expose only suite
ID/version/digest, coarse result, and a sanitized evidence reference.

Use the existing `baseline` and `playbook` conditions; the CLI has no `holdout`
condition. `--fail-on-invalid-run` detects invalid executions and
`--fail-on-hard-gate` applies the companion's configured hard gates. Project CI
must separately block on a required protected `fail`, missing/stale/flaky
evidence, or an invalid/contaminated result. See
`docs/testing/holdout_acceptance.md` in the Playbook repository.

## Generic Command Adapter Examples

These commands are external adapter examples. They are not the Codex Direct
bootstrap path.

Illustrative command adapter wrapper, insufficient for the frozen pilot:

```bash
harness-lab run --suite suites/playbook_core_v1 --condition playbook \
  --adapter command \
  --command-template 'agent-wrapper --workspace {workspace} --prompt {prompt_file} --output {output_dir}' \
  --trials 3 --output runs/generic-playbook
```

This generic example has no frozen Codex permission profile, manifest gate,
toolchain probe, event ledger, or timeout classification. Do not use it for the
paired pilot; use `tools/run_test_first_pilot.sh` from the root repository.

Claude Code:

```bash
harness-lab run --suite suites/playbook_core_v1 --condition playbook \
  --adapter command \
  --command-template 'claude --print "$(cat {prompt_file})"' \
  --trials 3 --output runs/claude-playbook
```

OpenCode-style command:

```bash
harness-lab run --suite suites/playbook_core_v1 --condition playbook \
  --adapter command \
  --command-template 'opencode run --prompt-file {prompt_file}' \
  --trials 3 --output runs/opencode-playbook
```
