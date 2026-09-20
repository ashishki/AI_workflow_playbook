# AI Workflow Playbook — Maintainer Plan

Updated: 2026-09-19. Current product candidate: **Playbook Native**.
Existing formal tooling: **Governed** (Lean-Core / Standard / Strict).

## Product Direction

The next user-facing product should connect a repository to its coding agent
with a small instruction block and focused skills. Users ask for an outcome;
the agent implements, runs meaningful checks, verifies the real UI when relevant,
fixes observed issues, and reports the result. A new orchestration framework,
mandatory MCP, and a copied governance system are outside the default path.

The source preview lives in `plugins/playbook-native/`. The
[product decision](research/CODEX_FRONTEND_SKILLS_MCP_ADOPTION_RU.md) explains the
tradeoffs and external research. The [delivery plan](research/CODEX_FRONTEND_IMPLEMENTATION_PLAN_RU.md)
defines actual acceptance scenarios and supersedes CF-00–CF-09.

## Next Deliverables

1. **Reliable connection and distribution:** test native discovery, existing
   instructions/overrides, repeated setup, update, and removal; resolve reuse
   rights and prepare one versioned install artifact. No public release claim
   before host-level checks.
2. **A complete frontend loop:** isolated fixtures, real agent/browser runs,
   screenshots actually inspected, wrong-build/stale-evidence traps, and a
   non-frontend negative trigger. Reuse existing tools before adding adapters.
3. **Small subscriber pilot:** onboarding and first-task usability, honest A/B
   against competent native Codex, and a short install/remove guide. Obtain
   permission before external recruitment/publication or downstream work.

Use the [current handoff](handoffs/CODEX_FRONTEND_SKILLS_MCP_HANDOFF.md) for the
actual verification status. Package structure and repository tests do not prove
skill selection, real-user value, or frontend quality.

## Compatibility And Governed Maintenance

Existing governed projects keep their contracts, reviews, schemas, and release
requirements. Native is not another initializer mode and does not silently
migrate those projects. Governed remains appropriate when formal records and
independent approvals have a concrete consumer.

Keep its currently tested helpers stable. Prioritize actual defects separately
from Native delivery:

- External skill discovery: `.agents/skills`, plugin/user scope, and an honest
  statement of what the old scanner does and does not inspect.
- Required context rendering: prevent silently omitted or truncated mandatory
  material; add behavior tests before claiming coverage.
- Formal browser evidence: observed build identity for remote/release checks,
  without turning every local UI fix into a provenance ledger.
- The existing `AWP-PI-010` sequential changeability runner and other historical
  mechanism tasks remain separate maintenance work, not Native prerequisites.

Keep RAG evaluation, cost architecture, cognition, receipts, and Role Runner as
specialized governed capabilities. Do not copy them into the Native package or
weaken them to make the new quick start appear smaller.

## Rules For Further Product Work

- Add instructions only when they change a useful decision; delete duplication
  of host behavior. Add executable helpers after a repeatable failure warrants one.
- Keep the package independent of a service, database, project framework, model,
  subscription tier, and global user configuration.
- Preserve existing project instructions and authorization. Ask at real product,
  access, cost, or external-effect boundaries, not each routine local step.
- Keep verification claims specific: static validation, observed runtime,
  independent review, and external-user validation are different evidence.
- Do not repair historical frozen experiment records by regenerating their
  hashes merely to obtain green CI on a different toolchain.
