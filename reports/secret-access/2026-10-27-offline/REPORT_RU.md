# Secret Access — partial experiment results

Tested experiment commit: `ab96f3859e14f8289257b7a1cc823a0b3bee3029`. This report includes offline checks, two initial model sessions, a separate live synthetic Relic probe and independent read-only review. It does not claim completion of the planned lifecycle.

| Comparison | Decision | Evidence |
|---|---|---|
| Method B/A | KEEP_EXPERIMENTAL | The initial A and B sessions were blocked before completing the cases; no effectiveness comparison is available. |
| Relic C/B | KEEP_EXPERIMENTAL | A separate synthetic CLI probe succeeded, but complete comparable C/B lifecycle trials were not run; additional value and cost are unknown. |

## What happened

The owner authorised Codex subscription use, up to $10 total and 30 minutes per complete trial. They described an application that reads `.env` itself: normally they create that file, and sometimes ask an agent to find keys and put them in the project root. Source inspection in one local project confirmed the dotenv call without opening its `.env`. A later disposable copy of its configuration successfully loaded an artificial `.env`; an earlier attempt failed because a synthetic numeric field had the wrong format and was preserved separately. Neither observation establishes the owner's complete current workflow; the review correctly leaves `current_workflow_observed` false.

A nine-run plan was prepared. C-1 was first in its order but was not attempted because the separate Relic project was unavailable; its skip time was not recorded. A-1 and B-1 were then attempted in that order. This deviation and the incomplete baseline limit comparability.

| Session | Result | Adapter time | Recorded model usage |
|---|---|---:|---|
| A-1 | BLOCKED: agent reported the frozen protocol and baseline were unavailable. | 34.68 s | 114,786 input tokens (106,496 cached), 1,531 output |
| B-1 | BLOCKED at setup; remaining cases NOT_RUN. The method file was present and read, but protocol/baseline handoff was missing. | 45.43 s | 131,950 input tokens (121,216 cached), 2,837 output |

These durations cover initial agent sessions, not complete lifecycles or human effort. Bundle verification passed for both, but the harness scorer checked command-receipt presence only. Exit code zero does not mean the eight cases passed. The generated `results.json` records 9 BLOCKED, 63 NOT_RUN, zero PASS, and unknown complete-cycle time, human time and cost. The A-1 case timestamps all refer to the one initial session; the individual cases were not independently attempted.

Two earlier minimal model preflights consumed 14,091 input / 5 output tokens and 22,782 input / 130 output tokens respectively; the latter exercised a synthetic access canary. Costs of these calls, the two initial sessions and independent reviews under the subscription are unknown, not zero. Reported token counts do not establish billed cost. Those initial sessions did not use Relic or real application credentials.

After the owner asked the assistant to perform the setup, the assistant created a synthetic `.env` in a disposable workspace. A separate agent then invoked the synthetic application successfully; its bundle verified. This limited observation used 49,540 input tokens (45,312 cached) and 951 output tokens. It demonstrates a delegated synthetic setup, not the owner's usual self-performed setup, the full process for finding keys, or an A/B lifecycle. Human time and cost remain unknown.

## Checks and follow-up

- On the current experiment source, 33 experiment tests and 50 vNext tests passed, the vNext contract check passed, and bundled runtime copies were current. Offline prepare → smoke → scan → report also behaved as expected; the deliberate synthetic-leak scan returned its expected finding. These checks do not demonstrate live effectiveness or isolation.
- An initial model preflight returned its expected response but reported a missing code-mode host. A later agent preflight, using a restricted Codex profile, tested readability of an artificial canary path outside its workspace and reported DENIED while creating a workspace file. The supervisor separately confirmed the canary existed on the host; its bundle verified. This covers one tested path and tool, not every access channel.
- A later separate test used Relic 0.10.2 in a disposable non-root container and a dedicated unshared test project. An independent second machine and the complete lifecycle remain NOT_RUN.
- Fixture preparation was corrected in `c348462` to supply the protocol and baseline handoff consistently to all arms, with the method only in B/C. The 32 experiment tests and a fresh offline prepare → smoke → scan → report passed. A fresh plan was prepared; its complete model trials were not run. The common information available to all conditions changed and could reduce the measured incremental contribution of the method; the original blocked runs remain preserved, including their cost and possible learning effect.
- The observed configuration copy, a restricted local network prototype and the model preflights do not establish a production-grade sandbox or a complete baseline. Real comparison remains blocked pending observation of the complete usual workflow, complete cost accounting, and a complete operator procedure.

## Separate live Relic probe

On 2026-10-27, after the owner authorised the account, isolated test project and synthetic import, a separate disposable project and test environment were created. The account initially listed no projects; the selected project was unshared and contained only the test environment and folder. The pinned Relic 0.10.2 release archive matched its published digest and the harness at commit `b34498495ca5046f74b131de2d183110b8439178` was used. The owner explicitly approved the import after a dry-run showing one new artificial key and no conflict. The import exited successfully; a subsequent names-only query found exactly that one synthetic key.

This is an operational probe, not a completed C trial or a comparison with B:

| Probe | Observation | Limit |
|---|---|---|
| Relic `check` and `run` | PASS: exit 0 and expected semantic JSON from the fixed synthetic probe. The launcher excluded inherited application keys and implicit Relic selectors. | Supports synthetic injection under the recorded execution, not real application behavior, model behavior, MCP, or security isolation. |
| Missing key / wrong environment | Relic `check` returned exit 1 and JSON `ok: false` for a missing synthetic key; `run` targeting an environment absent from the saved project snapshot returned exit 1; its precise cause was not independently verified. | The retained helper output records these assertions and hashes, not the original command output. |
| Wrong synthetic version | The consumer exited 4 when its expected digest did not match. | Tests the synthetic consumer, not revocation by a real provider. |
| Conflict preview | A dry-run for the second synthetic value reported a conflict; a subsequent v1 consumer exited 0. The operator recorded that no overwrite was authorised or performed. | This is not the full conflict case; unrelated-key preservation, source preservation, cancellation and actual update were not established. The conflict-preview output was not scanned for v2 canary representations. |
| CLI output boundary | The intentionally cooperative test program printed the raw, base64 and split synthetic value through `relic run`. Each appeared in the captured output. | A process receiving a secret can disclose it; this checks CLI output, not MCP masking or all trace channels. |
| CLI file boundary | The first file attempt exited 1 after about 31 seconds and the expected file was absent. A separately recorded retry in a fresh disposable directory exited 0 and wrote the artificial value to a file. | Cause of the first failure was not established. The retry demonstrates that a program receiving the key can persist it. |

The CLI probe took seconds per successful command; it does not measure complete setup or human effort. The owner login, project setup and import were part of the experiment. Total subscription allocation and any service cost remain unknown, so compliance with the $10 total cannot be verified. The real A/B/C comparison, fresh agent session, second machine, rotation/revocation and outage/exit cases remain BLOCKED or NOT_RUN. The initial blocked A/B records and their generated `results.json` are preserved separately from this probe and are not rewritten as C passes.

The probe receipts contain hashes and assertions rather than full provider process, environment and output records. Same-UID local artifacts can be altered, and hashes alone do not establish provenance. Raw intentional synthetic outputs were discarded. The import receipt records owner approval but does not itself independently authenticate the approval or preserve the command arguments. These limitations prevent the reviewer from reproducing or independently verifying every claimed output.

## Independent review

A separate read-only reviewer (`Codex /root/independent_review`) checked both initial session bundles, commands, evidence and the resulting case records. The reviewer confirmed the partial results and the fingerprint in `results.json`; the review is limited to these records, uses the same host UID and does not attest independent provenance, full-cycle behavior or actual costs. The reviewer also identified the missing handoff and the premature baseline-observed label, which was corrected to false. A later review of the proposed fixture correction found no new blocking permission error, while noting the changed shared information and the need for a fresh plan.

The reviewer also checked the later synthetic delegated-setup observation and its bundle, and did not find the known synthetic canary representations in the reviewed outputs. The review confirmed that this observation does not establish the complete usual owner workflow. A further read-only review checked the synthetic Relic plan, import and probe records and identified the provenance, v2 scan and file-attempt limitations above.

Do not adopt the method or Relic on the strength of these results. No private traces, source `.env` files, authentication material or synthetic values are published here.
