# Cognition Layer Migration Plan

Version: 1.0
Last updated: 2026-05-25

---

## Phase 1: Minimum Viable Cognition Layer

Goal: make each repo retrievable without changing runtime behavior.

Actions:

- add `docs/COGNITION_MANIFEST.md`
- identify canonical truth files
- identify missing governance artifacts
- add `Context-Refs` only to risky or active tasks
- generate optional `generated/cognition/index.json`
- do not backfill every old decision

Exit criteria:

- a new agent can find architecture, contract, tasks, decisions, evals, evidence, and open findings from files alone
- no Obsidian dependency exists

---

## Phase 2: Eval Linkage

Goal: connect memory to proof.

Actions:

- make every active eval artifact record exact eval source and date
- add evidence index rows for eval baselines and regressions
- link eval-affecting tasks to eval artifacts through `Context-Refs`
- create postmortems for major regressions instead of relying on chat recall

Exit criteria:

- reviewer can answer "what proved this before?" without archive archaeology
- eval regressions link to task, decision, and evidence

---

## Phase 3: Retrieval Automation

Goal: produce deterministic manifests and bounded packets.

Actions:

- run `tools/cognition_index.py` per repo
- add a lightweight CI check for manifest generation where useful
- generate context packets for phase reviews, architecture changes, and regression investigations
- keep generated packet count low

Exit criteria:

- strategist, reviewer, and orchestrator packets can be built from repo files only
- packets cite canonical artifacts and remain bounded

---

## Phase 4: Cross-Project Graph

Goal: reuse patterns across projects without centralizing authority.

Actions:

- create an Obsidian vault or separate markdown graph repo
- create one project map per repo
- create pattern and anti-pattern notes only when at least two projects share the lesson
- link cross-project notes back to canonical repo files

Exit criteria:

- cross-project retrieval finds reusable architecture patterns and prior eval lessons
- no vault note is required to run or govern a project

---

## Phase 5: Optional Semantic Retrieval

Goal: improve discovery in large archives.

Actions:

- index selected markdown and source files only
- exclude secrets, raw private data, caches, and generated noise
- require citations in every result
- use semantic hits only to propose deterministic links or packet candidates

Exit criteria:

- semantic search improves discovery but does not become authority
- deterministic packet generation still works without vectors

