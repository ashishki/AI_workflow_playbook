# Solution References

This catalog keeps external AI workflow, runtime, proof, and memory references
out of the mandatory playbook path while preserving them for concrete design
decisions.

Use this file to decide where to look when a project needs a specific pattern.
Do not treat any source here as a dependency.

| Reference | Use When | Useful Pattern | Authority | URL |
|-----------|----------|----------------|-----------|-----|
| Claude dynamic workflows | Large migration, audit, or parallel review needs executable orchestration | JavaScript workflow, parallel subagents, independent verification, saved progress, token-cost warning | Official product docs/blog | https://claude.com/blog/introducing-dynamic-workflows-in-claude-code |
| Cybos workflow explorer | You need examples of public workflow shapes by category | Pattern discovery: `parallel-fanout`, `multi-phase`, `judge-panel`, `adversarial-verify`, `structured-output` | Community index | https://www.cybos.ai/workflows |
| Bun port workflow | Broad language/runtime port with many independent failing tests | One build per round, parallel survey, bounded fix agents, two-vote review | Public source code | https://github.com/Microck/bun-rust-port-claude-artifacts/blob/main/.claude/workflows/phase-g-mega-swarm.workflow.js |
| Salesforce `auto-build-wi` | Enterprise work-item automation around PRs and CI | Claim/plan/build/review/draft PR loop, idempotent updates, CI triage, verified findings | Public source code | https://github.com/forcedotcom/salesforcedx-vscode/blob/develop/.claude/workflows/auto-build-wi.js |
| Hermes Agent | Persistent higher-autonomy runtime is explicitly required | Agent runtime, skills, memory, profiles, tool execution | Project docs/source | https://github.com/NousResearch/hermes-agent |
| Hermes Guide wiki | You need field notes on Hermes setups, memory, profiles, messaging, or coding workflows | Community operational pitfalls and setup patterns | Community wiki | https://hermesguide.xyz/wiki/ |
| Mythos Router | You need filesystem claim verification or receipt discipline | Strict write discipline, snapshots, receipts, verification commands | Project source | https://github.com/thewaltero/mythos-router |
| Entropy Core | You need optional proof/evidence vocabulary | Claims, receipts, verifier records | Project/reference policy | `docs/entropy_core_proof_layer_protocol.md` |
| Gensyn / CodeZero | You need inspiration for diverse solver/evaluator/referee patterns | Role diversity and referee-style review | Research/product reference | https://docs.gensyn.ai/testnet/rl-swarm/how-it-works/codezero |
| Cline Memory Bank | You need repo-local markdown memory patterns | Structured markdown project memory | Product docs | https://docs.cline.bot/best-practices/memory-bank |
| GitMark Memory Bank | You need simple markdown/git knowledge-base patterns | README index, Markdown notes, git-native memory | Public source | https://github.com/vakovalskii/gitmark-memory-bank/blob/main/README.md |
| Aider lint/test | You need post-edit deterministic verification | Auto lint/test after AI edits | Product docs | https://aider.chat/docs/usage/lint-test.html |
| NVIDIA SkillSpector | You need to vet third-party or cross-project agent skills before installation | Static + optional semantic skill scanning, SARIF/Markdown reports, risk scoring across prompt injection, exfiltration, supply chain, MCP poisoning, and dangerous code patterns | Official repo/docs | https://github.com/NVIDIA/SkillSpector |
| NVIDIA skill trust pipeline | You need release-gate structure for external skills | Scan report + skill card + detached signature/integrity verification before install | Official docs | https://docs.nvidia.com/skills/agent-skill-trust-pipeline |

## Adoption Rules

- Adapt patterns, not whole external systems.
- Prefer source code and official docs over community summaries.
- Re-check dates and compatibility before using fast-moving runtime references.
- Record the adopted pattern in `docs/DECISION_LOG.md` or an ADR when it changes
  project workflow, runtime, or review behavior.
- Never run a public workflow script without code review and tool/permission
  review.
