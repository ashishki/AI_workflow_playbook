# Handoff: Playbook Native preview.3

Updated 2026-09-19. Branch `docs/codex-frontend-skills-mcp-20260919`.
This change starts at `4eb96cc`; original proposal base `d070f4e`.
Only this branch/repository changed. Master remains `d570163`; no downstream,
public release, licensing change, host config change or subscriber contact.

## Current result

A [small offline kit](../../distribution/native/README.md) gives newcomers a
three-step start: extract, open START.html, select the prepared project in Codex
and describe the task. No terminal, hidden file copying or process manuals.
For existing projects, the same canonical source is a native plugin.

The user-selected dimensions remain independent: new/existing; create/fix/check;
automatic/plan-first/extended. Quick reduces ceremony and retains checks.
Plain language is the user entry: native plugin skill names are namespaced, so
`$playbook` is not promised as a universal alias. The host picker remains available.

Two skills, six payload files, a 22-line block. No new agent runtime, hooks,
mandatory MCP, model routing, receipts or project bureaucracy. Maintainer build
and eval tools are not installed in users' projects.

Read the [beginner quick start](../native/QUICKSTART_RU.md),
[onboarding report with evidence](../../reports/native/2026-09-19-onboarding/REPORT_RU.md),
[product decision](../research/CODEX_FRONTEND_SKILLS_MCP_ADOPTION_RU.md) and
[release plan](../research/CODEX_FRONTEND_IMPLEMENTATION_PLAN_RU.md).

## Observed outcomes

- ZIP reproducibility, extraction, hashes and protected output/symlink cases pass.
  The extracted page passes 48 selector combinations and mobile/desktop probes.
- Native CLI install/reinstall/update/remove and fresh-session discovery pass in
  clean offline containers; user workspace files are preserved. Extracted starter
  skills are discovered without Git. This is not a desktop onboarding test.
- Independent agent connect/reconnect/update preserved custom instructions and
  user changes. Initial remove exposed an active customized skill with a missing
  reference. Fixed by preserving the whole skill outside discovery; follow-up
  regression and parent hash checks pass.
- Independent agent built a new demo, used Chromium, viewed screenshots, fixed
  observed defects and provided double-click opening. Parent separately verified
  the form, mobile layouts and file:// operation. Mid-conversation plan-only
  request preserved every captured file. Different host from earlier blocked CLI.
- Clean-container model discovery trial still could not read the skill due to
  tool failure. Both attempts are retained; successful installation and exit 0
  are not counted as successful skill execution.

## Current verification

| Check | Result |
|---|---|
| Native plugin and both skill validators | PASS |
| Package unit tests | 5 PASS |
| Existing eval harness unit tests | 5 PASS |
| Extracted ZIP launcher | PASS; clipboard API stub + real selection fallback; OS clipboard untested |
| Native lifecycle + archive discovery | PASS on CLI 0.155.1 Linux; not desktop/windows/macOS |
| Parent browser probe of task output | PASS; Chromium 149.0.7827.55 |
| Full repository pytest | 222 passed, 12 skipped, 2 pre-existing failures |
| Integrity check | PASS, 2 pre-existing generated-content warnings |
| Local links / Python and JS syntax / diff whitespace | PASS; 144 local links checked |

The two pytest failures are `test_frozen_asset_manifest_matches_full_execution_closure`
and `test_frozen_permission_profile_denies_sibling_auth_and_network_access`.
Both were independently reproduced at unmodified `d070f4e` in the earlier work.
No frozen evidence or toolchain hash was rewritten. The full 26-check verifier
was not rerun in this increment; its prior 24/26 result and six historical missing
references remain recorded in the [preview.2 report](../../reports/native/2026-09-19/REPORT_RU.md).
Do not present this as a completely green repository or remote CI.

## Remaining product work

1. Observe the actual desktop first run, including extraction, Codex folder choice,
   plugin setup for an existing project, and real OS clipboard behavior.
2. Resolve reuse rights; the repository intentionally has no project-level license.
   The prepared archive and [pilot message](../native/PILOT_RU.md) are reviewable,
   but have not been distributed to subscribers.
3. Run a small newcomer pilot, fix observed stumbling points, then choose the
   public channel. No proof of speed/quality improvement over ordinary Codex.
4. Continue targeted compatibility tests (another UI stack, wrong/stale preview,
   monorepo/collisions) where they affect the supported release scope.

Skills and context files are guidance, not enforcement. Preserve actual failures
and host limits. Do not revive CF-00–CF-09 or add an installer framework to make
unverified claims look complete.
