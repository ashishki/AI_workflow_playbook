# Vault Usage Protocol

The cognition vault is a navigation and context-routing layer. It is useful
only when it helps an agent or operator start from the right project artifacts,
compare related projects, or detect drift across repos.

It is not a second source of truth.

## Authority Order

Use this order whenever surfaces disagree:

1. Project repo canonical artifacts: task graph, ADRs, evals, findings,
   implementation journal, architecture docs, and review archives.
2. Local README indexes as navigation only: `README.md`, `docs/README.md`,
   folder READMEs.
3. Repo-local `docs/COGNITION_MANIFEST.md`.
4. Vault project map and generated context packets.
5. Chat memory.

If the vault disagrees with the project repo, fix the project repo first, then
refresh or update the vault.

## When To Use The Vault

Use the vault for:

- agent cold start across a large project;
- orchestrator or reviewer context packets;
- cross-project strategy, portfolio status, and dependency review;
- checking whether a pattern from one repo should influence another repo;
- finding canonical artifacts without loading the whole repo into context;
- detecting stale links, missing references, or status drift.

## When Not To Use The Vault

Do not use the vault for:

- closing tasks;
- changing project status;
- recording decisions, eval results, findings, or customer evidence;
- replacing `docs/tasks.md`, ADRs, or review archives;
- runtime application behavior;
- CI requirements that make Obsidian or the vault mandatory.

## Agent Startup Rule

For a project task, the orchestrator may pass:

```text
Read README.md, docs/README.md if present, docs/CODEX_PROMPT.md, docs/tasks.md,
docs/COGNITION_MANIFEST.md, and the vault project map if available. Treat
project files as authority and use README files and the vault only for
navigation and cross-project context.
```

For a review task, also pass the scoped packet if one exists:

```text
../engineering-cognition-vault/10-projects/<project>.md
../engineering-cognition-vault/90-context-packets/<role>-<project>-<scope>.md
```

The agent must verify every vault claim against cited project files before
using it to make or review a change.

## Local And VPS Sync

Expected sibling layout:

```text
ai-stack/
|-- projects/<repo>/
`-- engineering-cognition-vault/
```

After meaningful project commits:

```bash
cd ../engineering-cognition-vault
./scripts/sync_from_projects.sh --commit --push
```

Before a review:

```bash
cd ../engineering-cognition-vault
./scripts/ensure_fresh_for_project.sh <project-id> --commit --push
```

Dirty project repos are skipped by design. This prevents vault sync from
pulling over local work. The vault can still regenerate from the local files
already present on disk.

## Useful Outcome Test

The vault is earning its keep if it reduces one of these:

- cold-start time for an agent;
- repeated re-reading of unrelated repo history;
- stale project status;
- broken Context-Refs;
- duplicated cross-project documentation;
- missed dependency between Playbook, Entropy Core, and product repos.

If a vault note does not help routing, verification, or cross-project recall,
shorten it or archive it.
