# Handoff: Playbook Native preview.2

Updated: 2026-09-19. Branch: `docs/codex-frontend-skills-mcp-20260919`.
Current work starts from `f650301`; original proposal base was `d070f4e`.
Scope: this repository only; no master/downstream edits or public release.

## Current result

The user selected three independent dimensions: new/existing project,
create/fix/check, automatic/plan-first/extended control. A single `$playbook`
entry infers and announces a useful approach; explicit user choices win.
Quick mode reduces ceremony while retaining checks. Check-only does not fix
source; plan-only does not implement or connect the repository.

The optional [offline start page](../native/start.html) composes a request for
Codex, with manual choices and scenario cards. It is a working interface, not
a connected agent service. No framework, backend, analytics or new runtime.

Read the [actual diagnostic pilot](../../reports/native/2026-09-19/REPORT_RU.md),
[quick start](../native/QUICKSTART_RU.md), [package](../../plugins/playbook-native/README.md)
and [release plan](../research/CODEX_FRONTEND_IMPLEMENTATION_PLAN_RU.md).

## Decisions based on observation

- Ordinary Codex and Native both repaired the frontend fixture. External browser
  checks pass for both; no demonstrated quality/speed advantage for Native.
- Both accurately reported missing agent browser verification. The shell sandbox
  blocked Chromium/local bind, and the separate MCP trial required approval
  unavailable under `never`. No permission bypass was used to declare success.
- Setup originally left a project block after protected `.agents` prevented skill
  installation. Fixed ordering; the retry preserves every original file and
  leaves no partial instructions. Successful installation is still unproven.
- New/existing plan-only cases preserve files. Backend work does not read the
  frontend skill. Extended review and explicit quick mode have separate records,
  including the original review timeout; see the pilot for exact outcomes.
- The default stays small: two skills, five payload files, 22-line project block.
  Connection detail loads only when needed. No mandatory records/roles/MCP.

These are real model trials in synthetic repositories, not a newcomer study,
clean-host test or completed end-to-end subscriber journey. The local unregistered
marketplace was not auto-discovered; no global plugin was installed. Models,
global configuration and downstream projects were not changed. No outside users
were contacted. There is no marketplace listing or new reuse license.

## Current validation

The pilot records launcher browser checks, external behavior/layout probes,
harness tests, package validators and repository checks. Raw local logs live
under ignored `.playbook-artifacts/native-pilot/`; committed results include
source/fixture hashes, exact prompts, finals, source diffs and evidence hashes.
Do not call the external evaluator's browser access an agent verification pass.
A complete model turn or a correct manifest also does not prove task success.

## Prior verification at f650301

These checks exercised the edited working tree before commit. No green remote
CI or real-agent compatibility result is implied.

| Check | Observed result |
|---|---|
| Plugin Creator `validate_plugin.py plugins/playbook-native` | PASS |
| Skill Creator `quick_validate.py` for both skills, using system `python3` | PASS |
| Copy the four skill payload files into temporary `.agents/skills`; validate both and resolve internal resources | PASS; packaging smoke only |
| Local Markdown links in changed/new documents | PASS |
| `git diff --check` | PASS |
| `.venv/bin/python tools/integrity_check.py --root .` | PASS, with two existing missing-generated-content warnings |
| Full `.venv/bin/python -m pytest -q` | 222 passed, 12 skipped, 2 failed |
| `tools/verify_playbook.py` with repo-local artifact directory | 24/26 checks passed; `pytest` and `playbook_validate` failed as below |
| Runtime tests at f650301 | Not yet run at that revision; superseded by the pilot below |

The two failing pytest cases were reproduced independently in a detached
worktree at the unmodified starting commit `d070f4e`:

- `test_frozen_asset_manifest_matches_full_execution_closure`: historical
  frozen pilot manifest is stale.
- `test_frozen_permission_profile_denies_sibling_auth_and_network_access`:
  installed Codex CLI version differs from that frozen pilot's toolchain.

`playbook_validate` reports six missing references to the historical
`shishki-tfa7-20260715` run/review/approval artifacts and two warnings for absent
generated cognition content. Its complete findings match `d070f4e` exactly.
No historical evidence, policy, or frozen hash was rewritten to hide these
failures. The other verifier checks, including generated-project matrices,
hooks, compilation, evidence fixtures, and RAG comparison, passed.

The first verifier invocation put artifacts outside the repository and hit a
RAG comparison path-scope error. It was rerun using the supported repo-local
layout. Final command:

```bash
.venv/bin/python tools/verify_playbook.py --root . \
  --output .playbook-artifacts/native-candidate-verification.json \
  --artifact-dir .playbook-artifacts/native-candidate
```

The local ignored report retains individual commands and output paths. It is
execution evidence from this checkout, not a committed release attestation.
A structural validator does not prove that an agent follows a skill or that a
host loads it. The delivery plan retains the full release matrix. Self-review caught and clarified preservation of modified skill
files on removal; no independent reviewer run is claimed.

## Next useful work

1. On a supported host, exercise actual plugin installation, fresh-session skill
   discovery, connection/reconnection/update/removal. No changes to downstream.
2. Complete a full agent browser trial where navigation and image viewing are
   legitimately available. A standalone browser preflight is insufficient.
3. Use fresh tasks for paired comparison: a new screen, another framework,
   stale/wrong preview trap, manual mode change mid-task. Keep failures and
   compare equal tools/permissions. Do not optimize against the development fixture.
4. After rights are decided, test first-run understanding with 3–5 newcomers.
   Prepare the concrete release artifact before seeking publication approval.

The sole immediate owner decision is reuse rights for subscriber distribution;
`docs/LEGAL_STATUS.md` intentionally grants no project-level license. The
technical delivery gaps above require implementation/testing, not another design
approval. Do not revive CF-00–CF-09 or install governance by default.
