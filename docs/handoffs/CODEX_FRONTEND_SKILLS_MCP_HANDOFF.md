# Handoff: Playbook Native preview.6

Updated 2026-09-19. Branch `docs/codex-frontend-skills-mcp-20260919`.
Candidate implementation: `64df8b37a0416fbcb184aa9e0740cfed5527d524`;
previous package: `f342162688003a0de801b24864a972cc144c4877`.
Master remains `d570163`; no downstream changes, public release, rights changes,
host configuration changes or subscriber contact.

## Product and decisions

Users open the prepared project in **Codex** and describe a task. START.html is
optional help with a collapsed prompt builder; no browser-to-chat handoff is
required. New/existing, create/fix/check and automatic/plan-first/extended remain
independent and controllable in chat. Quick reduces ceremony and retains checks.

Two skills, a short project block and the existing automatic Role Runner are the
whole runtime package. The entry skill/block now occupy 3,683 bytes versus 8,094;
this is static size, not a token-saving claim. A native plugin serves existing
projects; technical skill names differ between repo-local and plugin delivery.
No mandatory MCP, orchestrator, process forms or new laboratory.

The user explicitly chose automatic independent review and Windows/macOS/Linux.
Keep both. The bundled engine matches canonical `tools/` sources, needs Python
3.10+ and authenticated Codex CLI, and has no Git/governed registry prerequisite.
Missing or denied review remains an explicit gap; do not weaken access or retry
through an alternate route. Reviewers never start reviewers.

## How to continue development

Follow the [author protocol](../native/DEVELOPMENT_RU.md). Product comparisons use
**plain agent as the main baseline**, with the previous package added for
regression analysis. A comparison between two Playbook versions cannot by itself
answer why someone should install it. Keep changes only for an observed need;
if benefit is unshown, narrow the promise and simplify.

Use the existing [Harness Lab Native suite](../../evals/native/harness/README.md).
It has backend, plan, review, frontend, booking and contacts cases. New acceptance
checks are outside editable fixtures and tested against broken code, controls and
mutants. General Lab false-success metrics do not grade unstructured final claims;
read the trace and final answer. Missing usage/cost remains unknown.

[This increment's protocol](../../evals/native/VALUE_CHECK_RU.md) freezes a
plain/current/lean comparison: 2 tasks × 3 conditions × 2 trials, at most 240s each.
It is an instruction-only comparison with reviewer explicitly unavailable in all
arms. It cannot establish full-product or Role Runner benefit. Preserve failures,
partial outputs and frozen evidence. Results and decision belong in the
[value report](../../reports/native/2026-09-19-value/REPORT_RU.md).

Observed result: 12 attempts, 8 completed and 4 timed out; all 12 resulting
code snapshots passed their original external checks. Plain/current have matching
comparison fingerprints. Lean used a different `--package` path in its command
template, so formal comparison rejects it: retain its results as diagnostics,
never edit the saved fingerprints. All 12 bundles verify; 49 frozen source files
matched at the end. Plain Codex used fewer tokens/time on both completed contact
exports with the same checked outcome. Overall product benefit remains unproved.

After the frozen batch, suite 3.1.0 / contacts v2 added CLI and hard-link checks.
All six copied contact outputs passed the expanded checks; original bundles and
scores are untouched. Future experiments use one pair and fake-CLI compatibility
preflight before paid inference. The compact package stays experimental.

## Verification and artifact

20 Native tests and 11 distribution/runtime tests pass. Extracted START passed a
real Chromium probe: optional helper, 48 combinations, cards/help, clipboard stub
and fallback, 390/1280 px; screenshots inspected, no page errors/external requests.
[Native CI](https://github.com/ashishki/AI_workflow_playbook/actions/runs/35453887729)
passed integration and all three OS package jobs for the candidate. Their ZIPs
match the local build byte for byte. This is not a desktop newcomer trial.

ZIP `Playbook-0.1.0-preview.6.zip`: 60,323 bytes, 26 files.
SHA256 `5cca6e09bab83d80e48e1faeb8b16ce01509d7d6e178da3f509ef47449a13668`.
Local build `.playbook-artifacts/native-value-20260919/kit/`.
No lab, model logs, reports, credentials or test fixtures enter the subscriber ZIP.

Integrity passes with two existing generated-cognition warnings. The previous
full run had 226 pytest passes, 12 skips and two frozen-pilot failures; the broader
validator had six old missing task references. This increment does not repair
those historical failures or claim the whole repository is green.

## Remaining product work

1. Use the trial results to decide what the instructions justify; do not infer
   product superiority from packaging or static text reduction.
2. Evaluate the full implementation/review/fix cycle where review and browser are
   legitimately available. Prior standalone review found a defect; nested CLI was
   blocked in this host. Keep those distinct from instruction-only trials.
3. Observe actual desktop onboarding, result opening and continuation on all three
   OSes. Use the [small pilot](../native/PILOT_RU.md) after the owner's rights and
   distribution decision. No novice usability, real OS clipboard or Claude Code
   compatibility is claimed yet.
4. Handle frozen-pilot/toolchain mismatches in separate maintenance. Do not rewrite
   frozen manifests to make checks green.

The [revised product plan](../research/CODEX_FRONTEND_IMPLEMENTATION_PLAN_RU.md)
prioritizes demonstrated value and direct entry. Governed remains for explicit
use and existing projects; no automatic migration. The 45 removed historical
Native artifacts remain available at the [pinned Git archive](../../reports/native/README.md).
Ground Truth Lab is deferred by the user.
