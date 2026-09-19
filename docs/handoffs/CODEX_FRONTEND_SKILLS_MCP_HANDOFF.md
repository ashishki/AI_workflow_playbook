# Handoff: Playbook Native product candidate

Updated: 2026-09-19. Branch: `docs/codex-frontend-skills-mcp-20260919`.
Starting commit: `d070f4e`. Scope: this repository only; no master/downstream edits.

## Current result

The user explicitly authorized challenging the original proposal and changing
this branch. CF-00–CF-09 is superseded, not an approved architecture waiting for
execution. The new default candidate is a small native agent package with a
repository connection skill, one frontend delivery skill, and a short project
instruction block. Existing governed tooling remains a separate opt-in path.

Read these in order:

1. [Product model and current research](../research/CODEX_FRONTEND_SKILLS_MCP_ADOPTION_RU.md).
2. [Preview package](../../plugins/playbook-native/README.md) and its actual skills.
3. [Delivery and release plan](../research/CODEX_FRONTEND_IMPLEMENTATION_PLAN_RU.md).
4. [Quick start](../native/QUICKSTART_RU.md).

The package is authored, not installed in the user's environment, published,
licensed for subscriber reuse, or empirically validated. No browser/server was
added to a downstream repository. No model/permission settings were changed.
No outside users were contacted. There is no marketplace listing for this package.

## Decisions already made for the candidate

- Codex-first; existing host planning, tools, sessions, and instructions.
- One plugin as the intended distribution channel; the same source skills in
  `.agents/skills` as the fallback. No simultaneous duplicate installation.
- Always-loaded rules stay small; skill detail loads for the relevant task.
- One agent normally implements and checks; fresh review when useful or required
  by project risk/policy. Self-check is labeled accurately.
- Browser capability matters; MCP transport is optional. Desktop and CLI/IDE
  have different browser availability. No mandatory transport bake-off.
- Run the actual app and inspect its current rendered state. Missing capability
  remains a limitation; it does not become PASS.
- No mandatory task registries, receipts, role prompts, formal design approvals,
  or pixel baselines for an ordinary Native task.
- Existing Governed contracts are not silently disabled or migrated.

## Evidence and limitations

The initial proposal was written without a working checkout. This revision has
an actual checkout and local execution; do not repeat the old DNS/no-Codex claim.
`codex --version` returned `codex-cli 0.155.1`. Reading `codex plugin --help` and
`codex plugin add --help` established the local CLI surface, not plugin install
success. Official source pages were read again on 2026-09-19 and are linked in
the product document.

The initializer footprint was measured in temporary repositories with each
mode, no optional packs, and a minimal valid verification command. Lean-Core
created 35 files (17 tools, 8 schemas), Standard 81, Strict 82. These are scaffold
measurements, not a user productivity experiment.

### Final local checks

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
| Native plugin install/discovery, skill behavioral trials, browser trials, newcomer pilot | NOT RUN; release work |

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
host loads it. The two skills' behavioral acceptance scenarios remain in the
delivery plan. Self-review caught and clarified preservation of modified skill
files on removal; no independent reviewer run is claimed.

## Next useful work

Perform delivery A's isolated connect/reconnect/update/remove/discovery trials,
then delivery B's real browser trial. Keep tests in scratch fixtures, not a
working downstream product. Choose the host/browser actually available; do not
install every candidate. Use the final acceptance table rather than reviving
CF-00 or creating a new feature-approval ceremony.

Public distribution needs an explicit rights decision: `docs/LEGAL_STATUS.md`
intentionally grants no project-level reuse license. Prepare the actual release
artifact and checks before requesting publication approval. Neither license nor
public release is implied by this source preview.

Known Governed issues remain separately scoped: old skill discovery misses native
`.agents/skills`; required context can be clipped/skipped; formal browser records
lack observed build identity. Native does not use those mechanisms. The old
security gate must not be cited as validation of this plugin.

## Starting prompt for a later session

```text
Продолжи Playbook Native в AI_workflow_playbook на ветке
 docs/codex-frontend-skills-mcp-20260919.
Прочитай текущий handoff, product decision, пакет и delivery plan.
Проверь git status; сохрани мои изменения. CF-00–CF-09 уже заменён.
Следующая техническая работа — изолированные испытания подключения,
обновления, удаления и native discovery, затем реальный frontend trial.
Исправляй наблюдаемые проблемы; не добавляй governance по умолчанию.
Не меняй master/downstream и не публикуй пакет. Не меняй лицензию без решения
владельца. Сообщай реально выполненные проверки и оставшиеся ограничения.
```
