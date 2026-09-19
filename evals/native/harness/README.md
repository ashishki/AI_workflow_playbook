# Native cases in the existing Harness Lab

Maintainer surface. Product decisions follow
[the short development protocol](../../../docs/native/DEVELOPMENT_RU.md).
Ground Truth Lab is deferred. This suite reuses Harness Lab's command adapter,
runner, receipts, evidence verification and comparison. Native telemetry extends
comparison with primary/reviewer counters; unavailable verification is classified
as an invalid environment run. There is no second lab or runner.

| Task | Automated acceptance | Still reviewed by a person |
|---|---|---|
| `backend` | Seven slug cases, including the original defect; unrelated files preserved | Agent's verification claims and clarity |
| `plan` | Every captured project file unchanged after skill delivery | Whether the plan is useful and the final answer honest |
| `review` | Source unchanged; temporary review evidence allowed | Whether the defects are correctly identified |
| `frontend` | Existing independent Chromium form/mobile probe | Visual quality, agent browser use and final claims |

Both arms receive the **same** task text. `baseline` is plain Codex by default;
`playbook` receives the canonical skills and project block in a disposable fixture.
Use `--baseline-package` to compare a previous Native snapshot with the candidate.
The adapter refuses pre-existing agent instructions and never installs globally.
The CLI inherits the host's model/effort and general instructions. This is not a
clean-profile or desktop test. The synthetic fixture is not a security sandbox
for adversarial code. No downstream repository is used.

## Local checks (no inference)

From the repository root, using the existing development environment:

```bash
.venv/bin/python -m unittest discover -s evals/native -p 'test_*.py' -v
.venv/bin/python -m ai_workflow_harness_lab.cli validate-suite evals/native/harness
```

`test_harness.py` supplies an explicitly fake `codex` executable. It exercises
real Lab bundles and comparison, including an unfixed bug, plan mutation,
corrupt/incomplete trace, timeout and overwrite refusal. It does not measure AI.
The original buggy helper fails external acceptance even though its own test passes.

If the Lab is not installed in the development environment, follow its
[setup](../../../companion/ai_workflow_harness_lab/README.md) or run
`.venv/bin/pip install -e companion/ai_workflow_harness_lab`.

## Real diagnostic run (external terminal / worker)

Use a separate worker on copied fixtures, including when a maintainer agent
starts it at the user's explicit request. A task agent must not recursively launch
an experiment. Use authenticated Codex with working tool execution. Record the actual
model, effort, CLI version and common host instructions before running. Do not
change the global model or permissions to make a test pass.

Set `PLAYBOOK_MODEL_ID` and `PLAYBOOK_REASONING` to the observed session values.
Choose a fresh `PLAYBOOK_RUN` directory for each experiment. The example spends
at most four 300-second main attempts: two selected tasks × two conditions × one trial.
Automatic review consumes tokens within that budget; allow a longer main timeout
when evaluating the full review/fix loop. The frontend case needs existing
Playwright/Chromium and `PLAYBOOK_EVAL_PLAYWRIGHT_MODULE`; missing verifier access
is an invalid run, not a task failure.
It is a diagnostic, not evidence of a general improvement.

```bash
: "${PLAYBOOK_MODEL_ID:?Set the observed Codex model ID}"
: "${PLAYBOOK_REASONING:?Set the observed reasoning profile}"
PLAYBOOK_RUN="$PWD/.playbook-artifacts/native-lab/first-diagnostic"
PLAYBOOK_COMMAND="\"$PWD/.venv/bin/python\" \"$PWD/evals/native/harness_adapter.py\" --workspace \"{workspace}\" --prompt-file \"{prompt_file}\" --output-dir \"{output_dir}\" --condition {condition} --task-id {task_id} --timeout 300"

for condition in baseline playbook; do
  .venv/bin/python -m ai_workflow_harness_lab.cli run \
    --suite evals/native/harness --task-id backend --task-id plan --adapter command \
    --command-template "$PLAYBOOK_COMMAND" --adapter-timeout 330 \
    --condition "$condition" --trials 1 --output "$PLAYBOOK_RUN/$condition" \
    --empirical-comparison --provider openai --model-id "$PLAYBOOK_MODEL_ID" \
    --cli-version "$(codex --version)" --reasoning-profile "$PLAYBOOK_REASONING" \
    --permission-policy workspace-write-never \
    --delivery-profile native-repo-skills-v1 --fail-on-invalid-run || break
done

.venv/bin/python -m ai_workflow_harness_lab.cli compare \
  --baseline "$PLAYBOOK_RUN/baseline" --candidate "$PLAYBOOK_RUN/playbook" \
  --output "$PLAYBOOK_RUN/comparison" --min-trials-per-task 1 \
  --require-empirical --fail-on-invalid-run --fail-on-hard-gate
```

For a previous Native version, append
`--baseline-package /absolute/path/to/frozen/playbook-native` to the **same**
`PLAYBOOK_COMMAND` before running either arm. `--package` can select a frozen
candidate too. Use paths quoted for the shell if they contain spaces. Keep the
suite, adapter and acceptance checker unchanged throughout the comparison.
The summary records hashes of the installed package; freeze source revisions
and experiment settings alongside the result. Do not edit output bundles.

For repeated trials use `--trials 2` or more, or alternate arms with
`--trial-start N --trials 1 --append`. A repeated diagnostic remains development
evidence. Add a fresh case before making a broader product claim.

## Interpret results

`compare` verifies bundle integrity and compatible conditions. Read each task's
score and failures: its exit code alone does not enforce absence of quality
regressions. Nonzero adapter execution is an invalid run, not model success.
Task acceptance can fail after a completely valid model turn.

The command adapter does not extract structured claims from the final answer.
Its aggregate `false_success_rate` therefore does **not** evaluate Native's
honesty; inspect the final message and trace. The comparison includes primary and captured review tokens; missing counters
remain unknown. Main wall time includes reviews once. Time/token data do not
establish monetary cost. The automatic plan check hashes file content (excluding `.git`);
it does not audit empty directories, permission bits or activity outside the
fixture. Browser/lifecycle probes remain in [the evaluation index](../README.md).

Keep raw output under `.playbook-artifacts/`. Commit a concise result with source
versions, counts, failures, limits and decision. Publish a stable evidence archive
if making an externally reproducible claim. Never call these small cases a complete
frontend, onboarding, usability or product-quality evaluation.
