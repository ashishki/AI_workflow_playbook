# Codex Role Harness A/B Pilot

Status: empirical matched comparison complete; `accept_without_claim`.

## Frozen experiment

| Field | Value |
|---|---|
| Target repository | Georgia Community Navigator |
| Commit | `0f7299197883a7c2e926b6e3b9d152769df25743` |
| Task | `T30` |
| Model | `gpt-5.6-terra`, reasoning `high` |
| Permission policy | read-only |
| Baseline | direct suggested `codex exec` |
| Candidate | `tools/run_codex_role.py run` |

The first medium-effort candidate run was excluded before comparison because the
target review policy requires Terra/high. Every admitted pair used the same
rendered prompt after normalising only the two temporary worktree paths.

The baseline was a direct suggested `codex exec`, captured as
`declared_baseline` evidence. Candidate results were revalidated with
`run_codex_role.py verify` before import and are marked
`role_runner_verified`. This difference is provenance, not a claim that direct
Codex output is invalid.

## Admitted matched pairs

| Trial | Role | Baseline verdict | Candidate verdict | Prompt semantics | Candidate verification |
|---|---|---|---|---|---|
| 0 | `program_design_review` | STOP_SHIP | STOP_SHIP | identical after worktree-root normalisation | passed |
| 1 | `program_design_review` | STOP_SHIP | STOP_SHIP | identical after worktree-root normalisation | passed |
| 2 | `maintainability_review` | STOP_SHIP | STOP_SHIP | identical after worktree-root normalisation | passed |

All three pairs used the same commit, task, feature/slice identity where
applicable, model, high reasoning profile, read-only sandbox, policy, and one
attempt per arm. No arm changed its clean target worktree.

## Formal Harness Lab result

Both arms were imported through `harness-lab import-role-run` into ordinary
EvidenceBundles, all six bundles passed `verify-bundle`, and
`harness-lab compare --require-empirical --min-trials-per-task 2` returned
`empirical comparison` with no compatibility errors.

| Aggregate (3 paired reviews) | Baseline | Candidate | Candidate delta |
|---|---:|---:|---:|
| Valid reviews | 3/3 | 3/3 | 0 |
| False completion / policy violation / write drift | 0 / 0 / 0 | 0 / 0 / 0 | no regression |
| Retries / observed human interventions | 0 / 0 | 0 / 0 | 0 |
| Input tokens | 2,263,831 | 1,503,992 | -33.6% |
| Output tokens | 19,904 | 16,689 | -16.2% |
| Tool calls | 76 | 86 | +13.2% |
| Mean wall latency | 181.3 s | 153.0 s | -15.6% |
| Cost per valid review | unknown | unknown | pricing data was not captured |

The formal bridge reads public Codex JSONL token/tool counters and timestamps;
it does not infer price or judge whether a STOP_SHIP finding is substantively
correct. The candidate's result, prompt, context, report, trace and event ledger
were cryptographically revalidated. A manual direct-exec baseline has trace and
receipt evidence, but intentionally cannot claim the runner's ledger
attestation.

Both reports found concrete completion blockers; neither falsely returned PASS.
The candidate result revalidated successfully, including prompt/context/report/
trace hashes, current HEAD, and event-ledger linkage.

## Decision

Accept the Role Runner as the default execution path for the four supported
fresh read-only reviewer roles. This is an execution/provenance decision, not a
claim that its reviewer findings are intrinsically better or that it may approve
work. The hard guards did not worsen in three matched reviews, provenance became
revalidatable, and latency/token use improved materially.

This remains bounded: the real-repository sample covers program-design and
maintainability reviews only, all three findings were STOP_SHIP, and no
independent human adjudication compared finding quality. Continue to retain the
direct-exec escape hatch, record any runner failure as an invalid review rather
than silently falling back, and add product-design and slice-review samples
before making a broad quality claim. Cost remains unknown until a versioned
pricing source and billing convention are recorded.
