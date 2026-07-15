# Test-First Roadmap Scope Manifest

Created: 2026-07-13
Purpose: exact review/approval input; not an approval record

## Scope Identity

| Field | Value |
|-------|-------|
| Base commit | `aea241a07a283150812a97c551bd165af93023ed` |
| Tracked changed files | 26 |
| Tracked binary diff SHA-256 | `6868275cedb93a5f1a12965cb6fb84ecacd1c1a799813a3050741c037e61a752` |
| New TFA artifact files | 74 |
| New-artifact tree SHA-256 | `8cce2296b23c1cefe319c79ce934e768ee5565bfa018e342a9b5378c43f6308f` |
| Combined scope SHA-256 | `63f3584234d93f431a91a68103b6a21e666270c31fbac2d4da895268b352f23a` |

The combined digest is SHA-256 over three newline-terminated values in order:
base commit, tracked diff digest, and new-artifact tree digest.

## Included Scope

The tracked digest covers the complete `git diff --binary` from the base commit.
The new-artifact digest covers files under these paths, sorted bytewise, with
each file represented by the output of `sha256sum`:

- `docs/TEST_FIRST_AGENTIC_ROADMAP.md`
- `docs/audit/`
- `docs/evaluation/CRITIC_CALIBRATION.md`
- `docs/evaluation/TEST_FIRST_PILOT_PLAN.md`
- `docs/evaluation/TEST_FIRST_PILOT_RESULTS.md`
- `docs/merge_authority.md`
- `docs/testing/`
- `prompts/IMPLEMENTER_TDD.md`
- `prompts/audit/PROMPT_TEST_CRITIC.md`
- `reports/test_first_pilot/`
- `reports/test_first_roadmap/`
- `templates/TEST_CRITIC_REPORT.md`

This manifest file excludes itself from the new-artifact digest. User-owned
`.codex` and `deep-research-report(1).md` are explicitly outside the approval
scope and were not modified by this workstream.

## Reproduction

```bash
git diff --binary | sha256sum

find docs/TEST_FIRST_AGENTIC_ROADMAP.md docs/audit \
  docs/evaluation/CRITIC_CALIBRATION.md \
  docs/evaluation/TEST_FIRST_PILOT_PLAN.md \
  docs/evaluation/TEST_FIRST_PILOT_RESULTS.md docs/merge_authority.md \
  docs/testing prompts/IMPLEMENTER_TDD.md \
  prompts/audit/PROMPT_TEST_CRITIC.md reports/test_first_pilot \
  reports/test_first_roadmap templates/TEST_CRITIC_REPORT.md \
  -type f ! -name SCOPE_MANIFEST_2026-07-13.md -print0 | \
  sort -z | xargs -0 sha256sum | sha256sum

printf '%s\n%s\n%s\n' \
  aea241a07a283150812a97c551bd165af93023ed \
  6868275cedb93a5f1a12965cb6fb84ecacd1c1a799813a3050741c037e61a752 \
  8cce2296b23c1cefe319c79ce934e768ee5565bfa018e342a9b5378c43f6308f | \
  sha256sum
```

Any implementation-content change invalidates the applicable component digest
and requires a new manifest. A later append-only human approval record may cite
this combined digest; it does not retroactively change the reviewed content.

