# Native pilot — protocol fixed before runs

> Historical diagnostic protocol. New changes follow [the author protocol](../../docs/native/DEVELOPMENT_RU.md) and use [the existing Harness Lab](harness/README.md).

Date: 2026-09-19. Starting package: `f650301` / `0.1.0-preview.1`.
Scope: synthetic isolated repositories; no downstream project or public release.

## Questions and decision rules

| Question | Observation | Decision supported |
|---|---|---|
| Does setup preserve an existing project? | Bytes outside its block, existing changes and effective override survive; re-run adds no duplicate | Keep agent-mediated setup only while preservation checks pass; narrow/fix on failure |
| Does the Native bundle improve a frontend task? | Same fixture/prompt/tools/model in baseline and Native; independently exercise submit and layout | Keep useful instructions; no speed or quality benefit claim from a single pair |
| Does the agent distinguish working code from passing unit tests? | Real submit, error state, narrow/wide screenshots and their inspection | Browser verification needs a concrete capability, not another review role |
| Does missing browser capability produce false success? | Code checks plus explicit unverified UI boundary | Reject unsupported "UI verified" claims |
| Do startup intents respect requested boundaries? | Plan/review does not modify application files; implementation finishes the task | Keep one entry with clear intent; do not make a speed mode lower quality |
| Does frontend guidance spill into backend work? | Backend fix/tests without browser or frontend skill load | Narrow triggers if unrelated work activates the skill |

## Shared task and scoring

Frontend prompt: fix the subscription form on a narrow screen, preserve the
current visual style, verify successful subscription and invalid email, check
the running UI and show the result. Both arms receive this competent request.
The initial fixture has a passing input-validator test. External browser checks
inspect the actual user journey and layout; they do not accept an agent verdict.
A screenshot file existing is insufficient evidence of visual inspection.

Score separately: valid submit confirmation; invalid input feedback; no horizontal
overflow at 390 and 1280 px; control reachable with keyboard; no page exception;
useful final verification disclosure; source scope preserved. These checks do
not constitute a complete accessibility or design-quality audit.

Store original fixture/source hashes, exact prompt, CLI arguments, observed
model configuration, elapsed time, event usage, command/image events, final
message, source diff, and external check results. Unknown usage/cost stays
unknown. Do not substitute a script for a model run or silently drop failures.

Baseline has the same project README, browser runtime, commands and user task;
Native adds only the package skills and project block. Both use fresh repos and
fresh Codex sessions, the currently configured model/effort, and workspace-write
permissions. Do not change model, toolchain or permissions to improve one arm.
Both may see host-level instructions; record that limitation. No external web access or global installation is added to a fixture.
An additional paired condition may supply the same isolated local browser MCP
to both arms, through transient CLI configuration. Record tool versions,
permissions and failed preflights; never weaken approval to obtain a pass.

## Boundaries

This first pilot is diagnostic: one pair cannot establish superiority, causality
of an individual skill, or general usability. Same-model self-evaluation is not
an independent human review. Repeat across tasks/seeds/order and with newcomers
before claims about improved outcomes. Tests used to fix a discovered skill bug
become development cases; a later release needs fresh holdout cases.

A failed environment preflight is recorded separately from task failure, with
raw trace retained. Do not relabel it as a completed comparison. Source changes
after the pilot are a new package revision, and affected cases must be repeated.

The evaluation code is maintainer-only; it is not installed by Playbook Native.

## Environment findings and second revision

The initial shell-browser pair hit the host sandbox: localhost bind and Chromium
launch were denied. A separate local MCP pair then hit tool approval (`never`),
and one read-only snapshot exposed Chromium's root-user sandbox limitation.
Those attempts remain in the report; they are not a successful browser pair.
Fixing Chromium initialization does not grant approval for agent tool calls.
The external evaluator can exercise the resulting apps, but its checks do not
retroactively become agent browser verification.

Revision `0.1.0-preview.2` adds the requested three independent dimensions and
one `$playbook` entry. Test existing/create/plan, new/create/plan,
existing/check/extended and backend/fix/automatic. Compare application bytes
before/after for plan/review, and inspect traces for unrelated frontend loading.
The launcher exercises all 48 selections including automatic inference; this
is UI state coverage, not 48 agent trials or proof of intent understanding.

Setup revision: skill availability must precede writing the AGENTS block.
Retest the demonstrated protected-directory failure for unchanged user files and
no partial instructions; successful installation/idempotence remains separate.

Review follow-up: the first extended review preserved source but exhausted its
300-second deadline while preparing temporary findings after browser failure.
Narrow the instruction to task-relevant findings in conversation unless a file
report was requested, and link the browser reference explicitly. Repeat the case
with a disclosed 420-second diagnostic deadline; no latency improvement claim.
Add an explicit quick-mode trial (360-second deadline): implementation plus
meaningful verification, no new process documents or implied browser pass.
