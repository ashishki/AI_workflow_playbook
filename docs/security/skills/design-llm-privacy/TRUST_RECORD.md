# Design LLM Privacy — source trust record

Status: draft
Owner: Playbook maintainers
Last updated: 2026-10-27

## Skill Identity

| Field | Value |
|---|---|
| Skill name | design-llm-privacy |
| Source URL | https://github.com/ashishki/AI_workflow_playbook/tree/feat/llm-privacy-skill-20261027/engineering/skills/design-llm-privacy |
| Publisher / maintainer | Playbook maintainers; original repository-authored adaptation |
| License / terms | Repository terms in `docs/LEGAL_STATUS.md`; no new license grant. Article is conceptual provenance, not vendored text/code. |
| Version / tag / commit SHA | Content-addressed bundle; see manifest below |
| Artifact hash | SHA-256 `4835b79bf5235f69d6d2cae9d0274a2634d665a868e84e02f24e2135143192a5` |
| Install scope | project-local candidate; no installation or activation performed |
| Intended agent(s) | Claude Code and Codex design/review sessions |
| Update policy | Manual review and repinning; automatic update forbidden |

## Purpose and Skill Card

- One-sentence behavior: inspect a scoped LLM/RAG design and propose privacy
  boundaries, synthetic acceptance checks, and implementation tasks.
- Intended users/workflows: Engineering design/review; optional Governed strategy
  and review roles, preserving the target project's authority.
- Output type and format: chat or an explicitly requested design/audit Markdown
  note; proposed tasks stay within that note.
- Known risks: advice can omit a data route, mistake identity for authorization,
  or overstate pseudonymization; a host can load instructions unexpectedly.
- Mitigations: explicit scope/invocation, evidence-linked findings, conservative
  unknown-policy behavior, separate utility/security criteria, host invocation
  controls, and normal implementation/review gates.
- Skill card: `templates/skills/design_llm_privacy_skill.md`.

## Capability Declaration

| Capability | Used? | Scope | Justification |
|---|---|---|---|
| Shell execution | conditional | Existing authorized offline checks and targeted file search only; no bundled executable | Inspect evidence within the agreed task |
| Network egress | no | None during skill execution | Source links are references, not fetch/install commands |
| File read | yes | Applicable instructions and named provider/retrieval/auth/output/logging configuration/synthetic test files | Ground findings in implementation |
| File write | conditional | Agreed design/audit report path only; test-generated scratch output when already authorized | Save requested findings; no application, test, canonical-plan, or settings edits |
| Environment / secrets | no | No credential files, production dumps, or private logs | Synthetic inputs only |
| MCP tools / external tools | no | No required connector or MCP access | Portable instructions |
| Dependency installation | no | None | No bundled runtime dependencies |
| Persistent state / cron / startup | no | None | Monitoring is only a proposed task |
| External APIs | no | No live provider calls or evaluations | Offline design/review scope |

## Scan Evidence

| Check | Result | Evidence |
|---|---|---|
| SkillSpector static scan | not run | CLI unavailable in this authoring environment; no scanner result claimed |
| SkillSpector semantic scan | not run | No external model scan authorized or required for authoring |
| SARIF report | absent | No scanner executed |
| Dependency vulnerability check | not applicable | Bundle contains Markdown and declarative YAML only |
| Source/structure inspection | pass | Four-file inventory, frontmatter/YAML, local links, visible text, descriptor fields, and byte-identical copies in both host directory layouts checked |
| Skill frontmatter validator | pass | Skill Creator `quick_validate.py`: `Skill is valid!` |
| Repository offline checks | pass | 50 `tests/vnext` tests; `vnext_check.py`: `contracts_valid`; `sync_runtime.py --check`: `Runtime copies: current` |
| Draft trust triage | pass with warning | Explicit `--skill` selected this bundle; CLI reported one skill and skipped unavailable SkillSpector |
| Independent source review | completed; finding corrected | Read-only reviewer found Codex discovery gap; explicit candidate/installed-copy commands added to Engineering guide and rechecked |
| Fresh-assistant design exercise | completed | Synthetic support-assistant request: captured ingestion exposure, permanent-alias correlation, ambiguous accounts, current ACLs, UI/email release, missing vendor policy, and a bounded implementation handoff |
| Native Claude Code / Codex host exercise | not run | Neither native host was used in this authoring environment |

Alternative checks are suitable for preparing this instruction-only source
candidate: frontmatter/YAML parsing, complete bundle inventory, relative links,
visible text, capability/behavior review, synthetic assistant exercise, and
repository offline checks. They are not a SkillSpector substitute for a future
executable version or evidence of downstream installation approval.

Draft triage command (does not grant approval or imply a scanner ran):

```bash
python3 tools/skill_security_gate.py --root . \
  --skill engineering/skills/design-llm-privacy --allow-draft-trust
```

Other observed offline commands on 2026-10-27:

```bash
python3 -m unittest discover -s tests/vnext -v
python3 tools/vnext_check.py --root .
python3 distribution/native/sync_runtime.py --check
git diff --cached --check
```

The skill validator came from the platform-provided Skill Creator bundle;
it is not a runtime dependency of this skill. Local structure checks parsed YAML,
resolved Markdown links, rejected hidden format characters/comments, verified
all descriptor fields, and compared copied bytes. A clean copy layout is not
evidence that either native host loaded or obeyed the skill.

The design exercise supplied the skill and a new hypothetical architecture,
without expected findings or this review's conclusions. The assistant returned
design advice and proposed tests, distinguished supplied facts from verified
code, and performed no application changes or external calls. This is one
qualitative exercise, not a scored benchmark or an executed application test.

## Findings Triage

- Critical/high risk acceptance: no

| Finding | Severity | Decision | Owner | Mitigation / Risk Acceptance |
|---|---|---|---|---|
| Scanner and native-host evidence unavailable | Evidence limitation | Keep source experimental and installation decision deferred | Adopting project owner | Apply target project's acceptance before activation; no scanner or host success claimed |
| Claude can load a normal portable skill implicitly | Invocation constraint | Use host setting documented in Engineering guide | Adopting project owner | `user-invocable-only`; source body also requires explicit scope |

## Signature / Integrity

| Check | Result | Evidence |
|---|---|---|
| `skill.oms.sig` present | no | No publisher signature |
| Signature verified | not applicable | No signature verification claimed |
| Certificate / trust anchor | none | Not a signed artifact |
| Unsigned files allowed | candidate only | Review exact bundle and pin downstream source before adoption |
| Commit/hash pinned | yes | Exact content manifest below; branch URL alone is not the pin |

### Bundle manifest

The bundle is only the four files under `engineering/skills/design-llm-privacy/`.
Compute SHA-256 for each file. Sort their relative POSIX paths, then hash the
UTF-8 concatenation of `path + NUL + file_sha256_hex + LF` for each entry. The
trust record is outside the bundle, so recording the digest is not recursive.

| Relative path | SHA-256 |
|---|---|
| `SKILL.md` | `c8a52e69324ff8a36dc70737f0fbb6f0aa008c3f71a687c31203c56327462611` |
| `agents/openai.yaml` | `e7d276bc4f3302fdf8ed8d946b0b3282d324b84cbbc1af8c2a1d4d175948ad61` |
| `references/design-checks.md` | `21995ded0aaa3425856334d05850e8cf50f01d57ab75be0f12b35a96bf4e8cd6` |
| `references/evaluation.md` | `c0b7e51c1488c1d18f52296a02c995bc0b86ee5e2c62cbdcccfabb97f3ffa894` |

## Architecture Impact

- New capability profile required: none; this is design guidance.
- Runtime tier impact: none.
- Tool Catalog update required: no.
- Contract update required: no.
- Cost budget impact: no live calls or scheduled work introduced.
- Tasks required: downstream adoption, implementation, and runtime evidence use
  the target project's existing process. Native/Product packages are unchanged.

## Approval Decision

- Decision: deferred
- Approved install scope: none; source preparation only.
- Conditions: review the pinned bundle, capabilities, target host controls, and
  required local evidence before downstream installation or broader rollout.
- Reviewer: no human or independent runtime approval asserted.
- Date: 2026-10-27
- Re-review trigger: changes to source, permissions, invocation, dependencies,
  executable content, installation scope, or runtime/host behavior.

Do not use a successful draft-triage exit code as approval. Roll back an adopted
copy to its previous reviewed bundle, or remove only that skill's local folder
and associated setting; preserve other skills and project settings.
