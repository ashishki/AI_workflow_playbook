# Secret Access — partial experiment results

Tested experiment commit: `ab96f3859e14f8289257b7a1cc823a0b3bee3029`. This report includes offline checks, two initial model sessions, and their independent read-only review. It does not claim completion of the planned lifecycle.

| Comparison | Decision | Evidence |
|---|---|---|
| Method B/A | KEEP_EXPERIMENTAL | The initial A and B sessions were blocked before completing the cases; no effectiveness comparison is available. |
| Relic C/B | KEEP_EXPERIMENTAL | Relic service trials were not run and its additional value and cost are unknown. |

## What happened

The owner authorised Codex subscription use, up to $10 total and 30 minutes per complete trial. They described an application that reads `.env` itself: normally they create that file, and sometimes ask an agent to find keys and put them in the project root. Source inspection in one local project confirmed the dotenv call without opening its `.env`. A later disposable copy of its configuration successfully loaded an artificial `.env`; an earlier attempt failed because a synthetic numeric field had the wrong format and was preserved separately. Neither observation establishes the owner's complete current workflow; the review correctly leaves `current_workflow_observed` false.

A nine-run plan was prepared. C-1 was first in its order but was not attempted because the separate Relic project was unavailable; its skip time was not recorded. A-1 and B-1 were then attempted in that order. This deviation and the incomplete baseline limit comparability.

| Session | Result | Adapter time | Recorded model usage |
|---|---|---:|---|
| A-1 | BLOCKED: agent reported the frozen protocol and baseline were unavailable. | 34.68 s | 114,786 input tokens (106,496 cached), 1,531 output |
| B-1 | BLOCKED at setup; remaining cases NOT_RUN. The method file was present and read, but protocol/baseline handoff was missing. | 45.43 s | 131,950 input tokens (121,216 cached), 2,837 output |

These durations cover initial agent sessions, not complete lifecycles or human effort. Bundle verification passed for both, but the harness scorer checked command-receipt presence only. Exit code zero does not mean the eight cases passed. The generated `results.json` records 9 BLOCKED, 63 NOT_RUN, zero PASS, and unknown complete-cycle time, human time and cost. The A-1 case timestamps all refer to the one initial session; the individual cases were not independently attempted.

Two earlier minimal model preflights consumed 14,091 input / 5 output tokens and 22,782 input / 130 output tokens respectively; the latter exercised a synthetic access canary. Costs of these calls, the two initial sessions and independent reviews under the subscription are unknown, not zero. Reported token counts do not establish billed cost. No Relic login or import, real application credentials, production changes or rollout occurred.

After the owner asked the assistant to perform the setup, the assistant created a synthetic `.env` in a disposable workspace. A separate agent then invoked the synthetic application successfully; its bundle verified. This limited observation used 49,540 input tokens (45,312 cached) and 951 output tokens. It demonstrates a delegated synthetic setup, not the owner's usual self-performed setup, the full process for finding keys, or an A/B lifecycle. Human time and cost remain unknown.

## Checks and follow-up

- The offline fixture tests passed; after the dotenv fixture was added, 32 experiment tests passed. Offline smoke and the deliberate synthetic-leak scan behaved as expected. These do not demonstrate live effectiveness or isolation.
- An initial model preflight returned its expected response but reported a missing code-mode host. A later agent preflight, using a restricted Codex profile, tested readability of an artificial canary path outside its workspace and reported DENIED while creating a workspace file. The supervisor separately confirmed the canary existed on the host; its bundle verified. This covers one tested path and tool, not every access channel.
- The Relic 0.10.2 archive matched the published release digest and its version/help were checked in a disposable non-root container. No Relic login, project creation or import was performed. A separate test project, independent second machine and full lifecycle remain NOT_RUN.
- Fixture preparation was corrected in `c348462` to supply the protocol and baseline handoff consistently to all arms, with the method only in B/C. The 32 experiment tests and a fresh offline prepare → smoke → scan → report passed. A fresh plan was prepared but not run. The common information available to all conditions changed and could reduce the measured incremental contribution of the method; the original blocked runs remain preserved, including their cost and possible learning effect.
- The observed configuration copy, a restricted local network prototype and the model preflights do not establish a production-grade sandbox or a complete baseline. Real comparison remains blocked pending a confirmed workflow, complete cost accounting, a prepared operator procedure and the missing Relic resources.

## Independent review

A separate read-only reviewer (`Codex /root/independent_review`) checked both initial session bundles, commands, evidence and the resulting case records. The reviewer confirmed the partial results and the fingerprint in `results.json`; the review is limited to these records, uses the same host UID and does not attest independent provenance, full-cycle behavior or actual costs. The reviewer also identified the missing handoff and the premature baseline-observed label, which was corrected to false. A later review of the proposed fixture correction found no new blocking permission error, while noting the changed shared information and the need for a fresh plan.

The reviewer also checked the later synthetic delegated-setup observation and its bundle, and did not find the known synthetic canary representations in the reviewed outputs. The review confirmed that this observation does not establish the complete usual owner workflow.

Do not adopt the method or Relic from these results. No private traces, source `.env` files, authentication material or synthetic values are published here.
