# Codex Role Harness A/B Pilot

Status: preliminary empirical pair; `inconclusive`.

## Frozen pair

| Field | Value |
|---|---|
| Target repository | Georgia Community Navigator |
| Commit | `0f7299197883a7c2e926b6e3b9d152769df25743` |
| Task / role | `T30` / `program_design_review` |
| Model | `gpt-5.6-terra`, reasoning `high` |
| Permission policy | read-only |
| Baseline | direct suggested `codex exec` |
| Candidate | `tools/run_codex_role.py run` |

The first medium-effort candidate run was excluded before comparison because the
target review policy requires Terra/high. The admitted pair used the same
rendered prompt after normalising the two temporary worktree paths.

## Results

| Metric | Baseline | Candidate |
|---|---:|---:|
| Review verdict | STOP_SHIP | STOP_SHIP |
| Wall latency | 222 s | 139 s |
| Input tokens | 1,019,025 | 464,200 |
| Output tokens | 8,088 | 4,682 |
| JSONL events | 38 | 22 |
| Write drift | 0 | 0 |
| Marker / trace / ledger | manual trace + marker | valid marker, trace, hash-chain ledger |

Both reports found concrete completion blockers; neither falsely returned PASS.
The candidate result revalidated successfully, including prompt/context/report/
trace hashes, current HEAD, and event-ledger linkage.

## Decision

Do not promote the runner to the default path from one pair. The pair shows a
practical provenance advantage and lower observed token/latency use, but it has
no independent human finding-quality adjudication, no pricing source for cost,
and no repeated or multi-role sample.

The next experiment must import both arms into ordinary EvidenceBundles and run
the existing Harness Lab comparison command. The required bridge must only
normalise role-run artifacts into existing `RunResult`, scorer output, and
EvidenceBundle contracts; it must not introduce a second evaluation framework.
