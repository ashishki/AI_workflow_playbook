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
- The experiment's original suite format was rejected by `harness-lab validate-suite` because `suite_id` was missing. A subsequent builder at `4e8c8b2` prepared a nine-task suite: Harness Lab validation and the builder's full inventory check passed, as did 30 experiment tests. The builder records command receipts only; operator sequencing and lifecycle adjudication remain necessary. A scripted adapter is not live evidence.
- A separate minimal model preflight through the command adapter completed, returned the expected response and its bundle verified. It requested `gpt-6.1-terra` with high reasoning and recorded 14,091 input tokens (12,160 cached) and 5 output tokens. This was a connectivity check, not an A/B/C lifecycle trial. The output also reported that the code-mode host executable was missing; the model response did not prove agent tools worked. Subscription cost is unknown.
- Real A/B/C model runs, Relic service use, a second machine and the live lifecycle: NOT_RUN. A disposable Relic project is not yet available. A local container with a dedicated non-root OS user and no host home or Docker socket was prepared, initially without network. Relic 0.10.2 was installed only in this test environment from the pinned release; the downloaded archive matched GitHub's published SHA-256, and version/help ran without network. A successor container was connected to a Docker bridge for the owner's Codex login; that network is not an egress allowlist. The owner logged in to Codex in the test environment. No Relic login or import, production access or rollout was performed. Container preparation does not establish the second-machine case or complete the environment's security assessment.
- A later test image includes the missing code-mode host and bubblewrap. However, a networkless non-root sandbox preflight failed: bubblewrap could not initialize in the container, even when tested without the default seccomp and AppArmor profiles. Live lifecycle runs remain blocked pending an environment with a working sandbox; no agent run was attempted with sandbox bypass.
- A host bubblewrap prototype hid the normal home and Docker socket and successfully started a nested sandbox. Its read-only review identified that the prototype retained host-network access, including localhost. It is not an independent OS user or VM, and it has not been used for model trials; network access and baseline details must be resolved before live use.
- At `a73e1df`, all 32 experiment tests and a new offline prepare → smoke → scan → report passed; all 24 live observations remained NOT_RUN and both decisions remained KEEP_EXPERIMENTAL. The added synthetic app models the owner's description that the application reads `.env`, without claiming that a concrete existing project was observed. For C, `--require-injected` prevents `.env` fallback; the operator still has to verify that the value actually came from Relic.
- A later local network-namespace prototype passed limited reachability and negative connectivity checks, but independent review found unresolved access and comparison-integrity issues, including the exposure of Codex's own authorization directory to the agent and possible Unix socket paths in shared directories. It was not used for model trials. The broker is stopped and does not constitute a verified security boundary.

## Independent review

A separate Codex agent (Terra 6.1, high reasoning) reviewed the offline evidence read-only. It found two defects: smoke previously relied only on exit codes, and budget assessment used pair costs rather than the total experiment cost. Both were fixed and regression tested. The reviewer inspected the fixes and the new offline receipt, plan, assessment and results, and found no further blocking issue.

The same reviewer examined the subsequent suite builder and identified the need to detect drift and unexpected objects before use. The builder now checks the full expected inventory and contents; changes between checking and execution remain possible, and the operator must enforce and verify the schedule.

For the later dotenv fixture, the reviewer identified a possible false success from fallback in C; the injection-only mode and regression tests address that case. The reviewer also rechecked the later offline assessment and fixture receipt. The receipt exercises the probe, not the new application, and does not establish real agent or Relic behavior.

Local B-1 receipt SHA-256: `f13f79add500f7a615000c6c97c7829c41e37db1a82683e9957c749b9fa57a2d`. This receipt is not referenced by the observations and is not covered by the results fingerprint. Raw stdout/stderr was not retained; the reviewer checked the receipt and synthetic file. Both agents used the same OS environment, so hashes do not establish the provenance of events. The review assessed offline evidence only; `independent_review_current` remains false because no fingerprint-bound review is recorded in observations. There is no live evidence to review.

Do not adopt either the method or Relic on this evidence. Future decisions require comparable live trials, documented costs and independent review. No production keys, real project data or private logs are included here.
