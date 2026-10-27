# Secret Access — offline assessment

Tested source commit: `09632c025eb09822e6a82c9eee766dafccf559e3`
Date and environment: 2026-10-27, Linux, Python 3.12.3.

| Comparison | Decision | Evidence |
|---|---|---|
| Method B/A | KEEP_EXPERIMENTAL | No real agent trials; benefit and safety are unverified. |
| Relic C/B | KEEP_EXPERIMENTAL | Relic was not run; its additional value and cost are unknown. |

The plan prepared one run per arm; only B-1 has the reviewed offline smoke receipt, and all 24 live observations are NOT_RUN. Time and cost are unknown, including the cost of the independent review. They must not be interpreted as zero. The owner approved an overall budget of up to $10, Codex subscription use, a 30-minute limit per complete trial, and identified `.env` as the current baseline; the precise loading procedure still needs to be established before freezing a comparable baseline.

## Checks

- The experiment's offline unit/integration suite: PASS (29 tests). The fixed commit passed prepare → smoke → scan → report. The scan intentionally returned exit code 1 for a synthetic leak and did not find known canaries in the offline receipt. This scanner is not a general secret detector.
- On the initial branch commit before the experiment-only fixes: vNext tests (50), `tools/vnext_check.py` and `distribution/native/sync_runtime.py --check`: PASS.
- `harness-lab validate-suite engineering/experiments/secret-access`: BLOCKED; the experiment's own suite format lacks Harness Lab's `suite_id`. A compatible project suite/adapter is needed before live trials, preserving the prepared order and matching conditions. A scripted adapter is not live evidence.
- Real A/B/C model runs, Relic, a second machine and the live lifecycle: NOT_RUN. A disposable Relic project and a separate test OS user or VM remain to be prepared. The Relic CLI was not found in PATH; no installation, login, import, production access or rollout was performed. The owner has authorised preparation of a test environment and project.

## Independent review

A separate Codex agent (Terra 6.1, high reasoning) reviewed the offline evidence read-only. It found two defects: smoke previously relied only on exit codes, and budget assessment used pair costs rather than the total experiment cost. Both were fixed and regression tested. The reviewer inspected the fixes and the new offline receipt, plan, assessment and results, and found no further blocking issue.

Local B-1 receipt SHA-256: `f13f79add500f7a615000c6c97c7829c41e37db1a82683e9957c749b9fa57a2d`. This receipt is not referenced by the observations and is not covered by the results fingerprint. Raw stdout/stderr was not retained; the reviewer checked the receipt and synthetic file. Both agents used the same OS environment, so hashes do not establish the provenance of events. The review assessed offline evidence only; `independent_review_current` remains false because no fingerprint-bound review is recorded in observations. There is no live evidence to review.

Do not adopt either the method or Relic on this evidence. Future decisions require comparable live trials, documented costs and independent review. No production keys, real project data or private logs are included here.
