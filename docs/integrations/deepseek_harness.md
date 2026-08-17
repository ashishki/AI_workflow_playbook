# DeepSeek Harness Experimental Execution Backend

Status: implemented mechanism; live model screening pending

## Purpose

DeepSeek Harness is an optional empirical execution backend for Harness Lab. It
runs the existing baseline/candidate suites through a pinned DeepSeek Harness
Python SDK runtime and exports Playbook-compatible evidence.

It does not replace:

- Project Brief, task, Feature Design, or slice contracts;
- deterministic project verification;
- Playbook review and human acceptance;
- Harness Lab scoring and comparison;
- Codex-specific validation.

The boundary is:

```text
Playbook defines the task and required evidence
→ DeepSeek Harness executes one fresh trial
→ Harness Lab scores and compares results
→ evaluation gate/human decides what may be promoted
```

## Pinned upstream identity

- Release: `dsh-v0.1.0-rc.7`
- Commit: `99f6f02fecdb7dff40c3fbc9470f5907c29f74ca`
- Python distributions:
  - `deepseek-harness-sdk==0.1.0rc7`
  - matching `deepseek-harness-runtime-bin==0.1.0rc7`

DeepSeek Harness is still a developer preview. Never auto-update this dependency
inside an empirical series. A new release requires a new screening identity.

## Security profile

The adapter uses the checked-in profile:

```text
companion/ai_workflow_harness_lab/src/ai_workflow_harness_lab/
  profiles/deepseek_workspace_write.cordis.yml
```

The profile is intentionally:

- headless;
- `workspace-write`;
- sandboxed for Bash and filesystem mutations;
- session-JSONL backed;
- skills disabled;
- telemetry-free;
- without Web UI, subagents, or `danger-full-access`.

The DSH sandbox governs filesystem effects, not network access. For a strict
network-off experiment, run the screening command inside a disposable container
or namespace with network disabled.

The adapter temporarily replaces the parent process environment while the DSH
runtime starts. Credential-shaped variables are removed except
`DEEPSEEK_API_KEY`. This is a name-based defence, not a complete secret scanner;
use a dedicated shell and disposable workspaces.

## Install

```bash
python -m pip install -r requirements-dev.txt
python -m pip install -r requirements-deepseek-harness.txt
python -m pip install -e companion/ai_workflow_harness_lab
```

## Preflight

```bash
harness-lab dsh-doctor \
  --profile companion/ai_workflow_harness_lab/src/ai_workflow_harness_lab/profiles/deepseek_workspace_write.cordis.yml \
  --require-credential
```

Doctor verifies the profile, platform, SDK/runtime installation, matching pinned
versions, wheel `RECORD` fingerprints, and credential presence without making a
model call.

## Run the 12-run screening

```bash
export DEEPSEEK_API_KEY='...'

python tools/run_deepseek_harness_screening.py \
  --trials 3
```

This executes:

```text
2 tasks × 2 conditions × 3 trials = 12 logical runs
```

The two conditions use the existing `real_mini_repo_v1` baseline and Playbook
prompts. Every trial receives a fresh fixture Git repository, a fresh DSH home,
a fresh session id, the same model, the same profile, and the same scorers.

Optional prices may be passed for cost calculation rather than hard-coded:

```bash
python tools/run_deepseek_harness_screening.py \
  --trials 3 \
  --input-price-per-million <price> \
  --output-price-per-million <price>
```

## Resume after a limit

A rate-limited trial is moved under:

```text
.playbook-artifacts/deepseek-harness-screening/quarantine/rate-limit/
```

It is excluded from the empirical sample and the command exits `75`.
After quota recovery:

```bash
python tools/run_deepseek_harness_screening.py \
  --trials 3 \
  --resume
```

Credential pauses return `76`. Other invalid runs remain visible in evidence and
make the recommendation inconclusive or rejected rather than disappearing.

## Outputs

```text
.playbook-artifacts/deepseek-harness-screening/
  doctor.json
  screening_state.json
  baseline/<task>/trial-*/
  playbook/<task>/trial-*/
  comparison/
    comparison_report.json
    comparison_report.md
    loc_delta.json
    loc_delta.md
    runtime_metrics.json
    recommendation.json
    recommendation.md
  quarantine/
```

Each valid trial includes:

- DSH events and notifications;
- durable session JSONL;
- final response and stderr;
- adapter summary;
- command-style receipt;
- required project-verification receipt;
- scorer outputs;
- post-state manifest;
- HarnessEvalUnit;
- EvidenceBundle.

Harness identity includes provider/model, SDK and bundled-runtime versions,
wheel fingerprints, upstream release/commit, restricted-profile hash, system
prompt hash, tool-schema hash, permission policy, and environment digest.

## Metrics and decision

Hard guardrails:

- task success;
- required verification;
- false completion;
- policy violations;
- scope violations;
- evidence correctness;
- baseline/candidate identity compatibility.

Target metrics:

- code/docs/test LOC changed;
- files touched/created through existing diff scorers and manifests;
- token usage;
- tool calls/failures;
- turns/steps;
- latency;
- optional cost.

The generated recommendation is advisory:

- `promote`: at least 10% changed-LOC reduction with no observed guardrail
  regression and complete paired evidence;
- `accept_without_claim`: guardrails pass but target improvement is below the
  promotion threshold;
- `inconclusive`: missing, invalid, rate-limited, or incompatible evidence;
- `reject`: a hard guardrail regressed.

`human_decision` remains `pending`. A DeepSeek + DSH result does not prove the
same effect for Codex; run a separate Codex series when limits permit.
