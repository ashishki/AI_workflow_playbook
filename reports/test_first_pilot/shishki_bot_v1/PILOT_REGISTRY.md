# Frozen Pilot Registry - shishki_bot CI Supply Chain

Registry version: `shishki_bot_ci_v1/1.0.0`
Status: frozen candidate; execution approval pending
Pilot owner: pending human designation
Repository/data owner: Artem Shishkin (`ashishki`), exact-scope approval pending
Adoption authority: pending human designation

This registry prepares a paired real-repository pilot. It is not permission to
run a model, merge generated code, publish evidence, adopt a workflow, or claim
an empirical improvement.

## Repository Identity And Data Boundary

| Field | Frozen value |
|-------|--------------|
| Repository | `https://github.com/ashishki/shishki_bot` |
| GitHub owner | `ashishki` (connector-authenticated profile: Artem Shishkin) |
| Visibility | public |
| Repository license | no license file observed; owner authorization is required for this internal pilot use |
| Data class | public source, minimized evaluator fixture |
| Fixture contents | CI workflow, supply-chain test, staged public RED tests, `.gitignore` only |
| Explicit exclusions | application/runtime code, images, personal profile text, bot configuration, production data, credentials, Telegram access, Git history, and Git remotes |
| Retention proposal | raw artifacts under project ACL for 90 days after decision; sanitized reports for 365 days; credentials never retained |

The sparse fixtures are derived from exact source commits. They deliberately
exclude unrelated public personal imagery and runtime material. They are not
represented as full-repository clean clones. Source commits and full archive
digests remain recorded for provenance.

## Frozen Tasks

| Field | `pin_ci_actions` | `reject_unapproved_ci_actions` |
|-------|------------------|---------------------------------|
| Real-task provenance | `https://github.com/ashishki/shishki_bot/pull/2` | `https://github.com/ashishki/shishki_bot/pull/3` |
| Base commit | `59ff47bdbcfb32fb1f128fcf6ac37f6fa0bd8c26` | `5f9adb4f7421c7cc03e74c8dd30c127f3ecfd31d` |
| Base Git tree | `c6591a8432c619bea0994d60817845cd1605ee00` | `d0776724a24d12fe22534f8d893345f05aab7977` |
| Base full-archive SHA-256 | `2d15a1b1de7a535d573bd883ebdb18054a93f4065ef8838591cdf5f9a6867f33` | `4b34a03f293202a1ec5be7b69f8fe0a1cc03ae5bfdeecfb5f68624dd0206edd9` |
| Historical accepted commit | `5f9adb4f7421c7cc03e74c8dd30c127f3ecfd31d` | `798bb0ed68f7dacdf7e6f697381b7a3222949d74` |
| Historical patch SHA-256 | `1b8c18fe8f2a068bc08d9261598ec9d92b6298f68566d2038dec6b10f61f6515` | `9b4803fb71219ea6f8d805ffdd68d1106a336d9385bb7d95a06e7964f1aaee76` |
| Scoped accepted-file patch SHA-256 | `ea1911e4505cbfef7bb1c3b3e3b58d73c4aa89c4a4fec3e956165f4680bef7b7` | `9b4803fb71219ea6f8d805ffdd68d1106a336d9385bb7d95a06e7964f1aaee76` |
| Allowed mutation | `.github/workflows/ci.yml` | `tests/test_ci_supply_chain.py` |
| Prompt-side verifier | `python -m pytest -q pilot_tests/test_ci_pins.py` | `python -m pytest -q tests/test_ci_supply_chain.py pilot_tests/test_unapproved_action.py` |
| Independent required verifier | Bubblewrap read-only workspace: `python -m pytest -q -p no:cacheprovider pilot_tests/test_ci_pins.py` | Bubblewrap read-only workspace: `python -m pytest -q -p no:cacheprovider tests/test_ci_supply_chain.py pilot_tests/test_unapproved_action.py` |
| Expected initial state | RED: mutable major tags | RED: missing reusable all-`uses:` guard |
| Risk level | high: CI supply-chain trust boundary | high: regression guard for the same boundary |
| Public tests | required | required |
| Test Critic | required, condition-blind procedure after execution; inference risk retained | required, condition-blind procedure after execution; inference risk retained |
| Holdout | not required; all acceptance facts are public | not required; persisted public mutation is the oracle |
| Mutation | not required | required and supplied by the public mutation regression |
| Property/UI | not required / not applicable | not required / not applicable |

The historical accepted commits and patches are provenance/scorer references.
They are not present in agent workspaces or prompts. Because the fixes are
public on GitHub, the run disables web search, command network access, remotes,
and full history. Residual memorization risk remains a limitation and must be
reported; the pilot cannot be described as a secret benchmark.

PR #2 also introduced the later supply-chain test, so its full patch is broader
than `pin_ci_actions`. The scoped digest covers only the accepted workflow
mutation used as that task's oracle; the full PR digest remains provenance and
is not represented as the allowed pilot diff.

## Frozen Conditions

Both arms receive byte-identical `Task Facts` sections, fixture contents,
allowed scope, model, tools, correction budget, and verifier commands.

| Arm | Difference under test |
|-----|-----------------------|
| `baseline` | scoped implementation, focused verification, one bounded corrective pass, and evidence-based completion from the pre-TFA workflow |
| `playbook` | the same facts plus an explicit RED-to-GREEN test-first route, AC mapping, final gate rerun, and intentional-RED accounting |

Prompt and fixture digests are frozen in `ASSET_MANIFEST.sha256`. Any content
change creates a new registry version and requires fresh critic and approval.

## Execution Boundary And Budget Proposal

| Field | Frozen proposal |
|-------|-----------------|
| Codex auth | saved ChatGPT subscription login; no API key or paid fallback |
| Codex CLI | `codex-cli 0.144.4` |
| Model | `gpt-5.6-sol` |
| Reasoning / service tier | `medium` / `default` |
| Model permission profile | `test_first_pilot`: copied fixture write; project `.venv` and Codex runtime read; sibling repositories and model-shell access to saved auth denied |
| Model process containment | pinned Bubblewrap PID namespace; wrapper termination destroys the descendant namespace before scoring; file/network policy remains owned by the Codex permission profile |
| Verifier sandbox | frozen Bubblewrap binary; fixture read-only; environment cleared; network/host namespaces unavailable |
| Codex configuration | approval policy `never`; user config/rules, apps/plugins, browser/computer use, collaboration, and fan-out disabled |
| Provider transport | Codex CLI broker may contact the subscription service; generated commands cannot use that transport |
| Network/search | model-shell network `false`; web search `disabled`; no remotes |
| Host configuration isolation | non-login command shell; inherited Git environment/system/global config, templates, hooks and signing disabled; pilot preflight pytest external plugins and `conftest.py` disabled |
| Evidence trust boundary | trusted single-writer host; no concurrent mutation; runner writes `COMPLETED_RUN.json` last and review verifies it twice; the seal detects ordinary drift but is not a signature or independent attestation |
| Toolchain | local host-specific Python, full regular-file `site-packages` closure, pytest, jsonschema, harness, Bubblewrap, shell/system binaries, OS, and Codex launcher/native package paths and digests in `TOOLCHAIN.json`; host drift requires a new freeze |
| Codex executions | complete schedule and ceiling of 12: 2 tasks x 3 trials x 2 arms; an early invalid stop can produce fewer and remains inconclusive |
| Internal inference calls | provider-managed and not bounded or equated with the 12 agentic executions |
| Retry/correction executions | zero reruns; invalid/quota failure stops the pilot as inconclusive |
| In-execution correction limit | one prompt-level corrective pass; not process-enforced; trace-derived repair candidates are adjudication evidence, not proof of compliance |
| Critic/judge executions | zero during execution; deterministic scorers plus later condition-blind review |
| API/CI/storage spend | USD 0 incremental paid API/CI/storage; existing ChatGPT subscription price is not represented as zero |
| Per-call timeout | 1,200 seconds; outer adapter 1,260 seconds |
| Credentials | saved Codex login is used by the CLI broker only; secret environment variables are removed and the model shell cannot read the auth file |
| Launcher | named human operator in a separate shell or CI; active Codex sessions are rejected |

Subscription quota is not a monetary charge but is a finite usage budget. A
quota failure consumes the attempted call, stops execution, and produces no
replacement call under this version.

## Counterbalanced Schedule

| Pair | Task | Trial | First arm | Second arm |
|------|------|-------|-----------|------------|
| P01 | `pin_ci_actions` | 0 | baseline | playbook |
| P02 | `reject_unapproved_ci_actions` | 0 | playbook | baseline |
| P03 | `pin_ci_actions` | 1 | playbook | baseline |
| P04 | `reject_unapproved_ci_actions` | 1 | baseline | playbook |
| P05 | `pin_ci_actions` | 2 | baseline | playbook |
| P06 | `reject_unapproved_ci_actions` | 2 | playbook | baseline |

Each invocation gets a fresh copied fixture and a unique logical trial path.
The harness refuses collisions and appends only through an explicit immutable
run index. The external runner performs no automatic retry and no adoption
comparison. After execution, an independent reviewer admits or rejects matched
pairs, creates a content-addressed comparison input, and only then runs the
comparison.

The three trials are isolated repeated executions, not seeded deterministic or
statistically independent samples. The provider build identifier is not exposed
by this interface and remains `unknown`; model, CLI, local toolchain, prompts,
fixtures, order, and permissions are frozen instead. No independence or power
claim may be derived from the repetition count.

## Metrics And Missing Values

The preregistered primary observations are public-verifier pass, policy/diff
scope pass, valid-run status, paired pass/win/loss/tie rows, and false-success
events. The frozen event ledger can supply verifier-attempt counts, first-GREEN
and final-model-gate duration, trace-derived repair candidates, terminal class,
and the non-interactive intervention record when every relevant event validates.
Missing or malformed events make the affected observation `unknown`.

Cost in USD and exact provider tokens remain `unknown`. Repair-candidate count
is not relabeled as repair turns, and the prompt correction limit is not claimed
as hard-enforced. Rollback/reopen is `not_observed` because no pilot change is
merged. Holdout/property/UI metrics are `not_applicable` from the frozen routes.
There is no composite score and no statistical-sufficiency claim at six pairs.

## Frozen Outcome Review

`tools/prepare_test_first_pilot_review.py` requires a valid completed-run seal,
the approved governance copies, exactly twelve valid compatible bundles in the
frozen non-overlapping schedule, one object-only raw Codex JSONL stream per arm,
and an event ledger that exactly matches its independent reconstruction. It
verifies the seal before reading evidence and again before writing outputs, then
records the seal digest in the protected mapping. It creates six
cryptographically shuffled A/B packages with three swaps in each direction.
The reviewer sees task rubric, allowed artifact content, normalized required
verification, scorer facts, and failure counts, but no condition, source path,
prompt, raw trace, time stamp, or process telemetry. Real labels, bundle sources,
digests, and process observations stay in the protected mapping.

Literal labels are hidden, but output content can still let a reviewer guess a
workflow. The reviewer records suspected inference or any blinding leak; the
adjudicator makes the affected pair `inconclusive` when independence is not
credible.

The mapping's local `0700` directory and `0600` file are only accidental-access
protection. A separate custodian account or equivalent ACL must make that mapping
and the raw run unavailable to the reviewer until all six reports are frozen and
the reviewer attests to non-access. The later adjudicator may then join reports
to labels. This pilot does not calibrate critic false-alarm or miss rates; the
human outcome critic is advisory and cannot make the adoption decision.

## Approvals Still Required

1. TFA-7.1 pilot-owner approval of the frozen manifest after a fresh independent critic.
2. TFA-7.2A repository/data-owner approval of both exact bases, sparse fixture boundary, provenance, and retention.
3. TFA-7.2B budget/operator approval of exactly 12 subscription-backed Codex executions, unbounded internal inference count, zero paid fallback/retries, and the external boundary.
4. TFA-7.2C scorer/adjudicator approval of prompt, suite, wrapper, schema, schedule, missing-value rules, and the separate reviewer/custodian boundary.
5. A final explicit execution decision citing the frozen manifest SHA-256.

The user's earlier instruction authorized repository selection and ordinary
local tests. It did not approve these previously unknown exact pilot assets,
Codex-execution budget, retention decision, or execution manifest.
