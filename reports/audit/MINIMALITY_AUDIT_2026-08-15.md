# Minimality Audit — AI Workflow Playbook

Date: 2026-08-15
Base commit: `965612aa463fca1a35a55104633d0e09da33d615`
Status: read-only structural audit and cleanup backlog

## Decision

Freeze new capability work until the repository has:

1. one green portable core baseline;
2. an explicit boundary for environment-specific pilot checks;
3. fewer default artifacts in generated projects;
4. a smaller set of tests mapped to unique invariants.

This report does not authorize deleting security, verification, evidence,
approval, or release gates. It identifies where the same responsibility appears
through multiple files, tests, fixtures, or execution paths.

The repository does not install the external Ponytail plugin. The useful idea is
adapted as a small internal implementation rule: reuse first, extend an existing
authoritative path, add the minimum proof-bearing change, and never minimize
trust boundaries or evidence.

## Protected Invariants

Do not remove or weaken tests that are the only protection for:

- false completion and failed required verification;
- path traversal, absolute paths, `..`, and symlink escape;
- stale or tampered hashes, receipts, reviews, and acceptance artifacts;
- model/agent self-approval;
- exact-HEAD release decisions and dirty-tree blocking;
- required design review and human high-risk slice acceptance;
- security, privacy, secrets, billing, destructive actions, and supply chain;
- task / feature / slice scope consistency.

A cleanup may consolidate these tests, but the invariant and its negative case
must remain executable.

## High-Confidence Findings

### MIN-01 — The portable core baseline is mixed with host-specific pilot checks

Current full verification is reported as red because frozen pilot checks depend
on a particular Codex/toolchain version and `/usr/bin/bwrap`, while the focused
core suites pass.

Action:

- classify checks as `portable_core` or `environment_pilot`;
- make the default repository gate prove the portable core everywhere;
- run environment pilots only when their declared prerequisites are present;
- never treat a skipped environment pilot as positive capability evidence.

Expected result: contributors stop learning to ignore a permanently red gate.

### MIN-02 — `docs/tasks.md` mixes active work with a large completed history

The active task graph contains extensive completed workstreams and historical
evidence paths. This increases context cost and keeps stale references inside a
file that agents are told to read before every task.

Action:

- keep only active and near-term tasks in `docs/tasks.md`;
- move completed work to one historical task archive;
- keep stable task IDs and evidence references;
- make the validator ignore the archive unless an explicit historical audit is
  requested.

Expected result: smaller default context without losing provenance.

### MIN-03 — `templates/CODEX_PROMPT.md` carries too many inactive capability states

The standard prompt template combines session state, cost state, external skill
state, RAG, tool-use, agentic, planning, compliance, NFR, evaluation history,
compaction rules, and long operational instructions in one default artifact.

Action:

- retain one compact current-state summary and continuity pointers;
- generate capability-specific state blocks only when the capability is active;
- keep detailed protocols in their authoritative documents and load them on
  demand;
- do not create a replacement mega-template.

Expected result: less repeated context and fewer stale placeholder fields.

### MIN-04 — The initializer owns repeated file-copy lists and an embedded runtime

`tools/init_playbook_project.py` repeats lists of tools and schemas across modes
and embeds the generated project verifier as a large string.

Action:

- replace repeated copy lists with one declarative file manifest;
- select entries by mode and capability flag;
- move the generated verifier to one versioned runtime template;
- preserve generated-file hashes and backward compatibility.

Expected result: one authoritative bootstrap inventory and smaller initializer
code.

### MIN-05 — Optional capability packs leak into default bootstrap scope

Audited execution and other experimental capability schemas/tools should not be
copied into every downstream project merely because they exist in the Playbook.

Action:

- gate optional packs behind explicit initializer flags or selected execution
  profiles;
- keep `direct_codex` and ordinary project verification minimal by default;
- test that Lean-Core output does not contain inactive experimental artifacts.

Expected result: generated projects contain only the mechanisms they use.

### MIN-06 — Test count is growing faster than the invariant inventory

Several test modules contain many setup-heavy variants around Feature Workflow,
review records, acceptance, and generated projects. Some duplication is valid,
but the suite lacks one visible map from each test cluster to a unique invariant.

Action:

- inventory invariants first;
- parameterize repeated state-transition and path-safety cases;
- merge fixtures that differ only by one field;
- remove tests of thin wrappers, constants, stdlib behavior, or schema behavior
  already proved by the schema validator;
- keep a focused negative test for every known bypass.

Expected result: fewer tests with equal or stronger failure detection.

### MIN-07 — Documentation repeats operating-model explanations

README, PLAYBOOK, usage guide, adoption modes, tool docs, protocol docs, and
implementation reports repeat parts of the same workflow.

Action:

- choose one authoritative protocol for each concept;
- replace other copies with a short summary and link;
- mark implementation reports as historical evidence, not live instructions;
- prevent new docs from restating an existing contract.

Expected result: fewer contradictory explanations and lower maintenance cost.

### MIN-08 — Historical reports and generated outputs need a retention rule

Committed reports are useful when they support an ADR, empirical claim, release,
or regression. Generated smoke output and superseded implementation snapshots
otherwise become permanent navigation noise.

Action:

- keep a current evidence index;
- retain durable decision/claim evidence;
- archive or delete superseded generated outputs after their claim is retired;
- keep ordinary runtime output under ignored `.playbook-artifacts/`.

Expected result: the repository remains inspectable without losing evidence.

## Needs-Experiment Findings

### MIN-X1 — Do not split `feature_workflow.py` only because it is large

A large coordinator is not automatically worse than several thin modules. Only
extract a pure helper when it has at least two real consumers, reduces repeated
logic, or makes a trust boundary independently testable.

### MIN-X2 — Do not merge schemas merely to reduce file count

Separate schemas are justified when they are independently consumed, versioned,
or validated. Merge only schemas that always travel and change together and
have no independent consumer.

### MIN-X3 — Ponytail modes require a local A/B before becoming default

A future experiment may compare Codex with and without a minimality instruction
on the same tasks. Keep the model, repository commit, permissions, verification,
and timeout constant. Measure production LOC, test LOC, files, artifacts,
correctness, hidden edge cases, policy violations, tokens, and time.

Do not enable an always-on external plugin globally before that experiment.

## Cleanup Slices

Execute these independently. Each slice should be net-negative in files or LOC
and should not add a new framework to perform cleanup.

1. **MIN-S1 — Green portable baseline**
   - classify environment pilot checks;
   - make the portable core gate green;
   - record exact commands and remaining optional prerequisites.

2. **MIN-S2 — Active task graph extraction**
   - archive completed task blocks;
   - leave only active/near-term work in `docs/tasks.md`;
   - preserve IDs and provenance.

3. **MIN-S3 — Prompt-template reduction**
   - reduce default `CODEX_PROMPT` state;
   - materialize capability blocks only when active;
   - measure context reduction.

4. **MIN-S4 — Initializer file manifest**
   - deduplicate copy lists;
   - extract the generated verifier template;
   - preserve generated-project matrix behavior.

5. **MIN-S5 — Optional pack gating**
   - keep experimental audited/RAG packs out of inactive modes;
   - add one initializer matrix assertion per capability flag, not per file.

6. **MIN-S6 — Test invariant consolidation**
   - create an invariant map;
   - parameterize repeated state/path cases;
   - delete tests with no unique failure mode.

7. **MIN-S7 — Documentation authority map**
   - name one authority per concept;
   - replace repeated protocol prose with links;
   - remove superseded navigation entries.

8. **MIN-S8 — Evidence retention cleanup**
   - classify committed reports as current, historical, or removable;
   - delete only artifacts with no live claim, ADR, task, or release reference.

## Acceptance Rule For Every Cleanup Slice

A cleanup slice is eligible only when:

- the diff is net-negative in code, tests, files, or loaded context;
- no protected invariant loses its executable negative case;
- no permission, approval, evidence, or release boundary is weakened;
- focused verification passes;
- the portable canonical gate passes or the slice explicitly fixes the last
  known blocker;
- no new abstraction is introduced solely to organize the cleanup.

## First Action

Start with `MIN-S1`. Do not perform broad deletions while the canonical baseline
is red, because regressions cannot be distinguished reliably from pre-existing
host-specific failures.
