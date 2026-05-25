# Operational Cognition Workflows

Version: 1.0
Last updated: 2026-05-25

---

## Architecture Change

1. Strategist builds a packet with architecture, decision log, relevant ADRs, eval state, and open findings.
2. Human approves whether the change is architecture-significant.
3. Write a proposed ADR if it changes runtime tier, capability profile, data boundary, eval policy, or control surface.
4. Update `docs/DECISION_LOG.md`.
5. Add implementation tasks with `Context-Refs` to the ADR and affected evals.
6. Reviewer checks implementation against the ADR and contract.

Packet command:

```bash
python3 tools/context_packet_builder.py \
  --manifest generated/cognition/index.json \
  --role strategist \
  --scope "runtime tier change" \
  --output docs/context-packets/strategist-runtime-tier-change.md
```

---

## Eval Regression

1. Start from failing eval command or metric row.
2. Retrieve previous baseline and exact eval source.
3. Retrieve task or ADR that last changed the affected boundary.
4. Retrieve prior review findings for the same boundary.
5. Decide: bug, acceptable tradeoff, stale eval, or baseline reset request.
6. If bug, open P1/P2 finding and add fix task with `Context-Refs`.
7. If acceptable tradeoff, document in eval regression notes and decision log.

Do not resolve an eval regression from a summary alone. The packet must cite the eval artifact and source command.

---

## Postmortem

1. Create `docs/postmortems/YYYY-MM-DD-short-slug.md`.
2. Link the failing test/eval/review evidence.
3. Explain why existing controls missed it.
4. Add corrective actions as tasks.
5. Update evidence index with postmortem and new regression tests.
6. File ADR if the fix changes architecture, contract, runtime, or eval policy.

---

## Strategist Context Assembly

Include:

- `docs/ARCHITECTURE.md`
- `docs/DECISION_LOG.md`
- relevant ADRs
- active eval artifacts
- evidence gaps
- project fit and adoption reality notes
- cross-project patterns only when linked to the same problem

Exclude:

- old implementation journals unrelated to the decision
- routine phase reviews with no open findings
- generated context packets unless they are the handoff source

---

## Reviewer Context Assembly

Include:

- current task acceptance criteria
- implementation contract rules
- changed file list
- active profile eval artifact
- prior findings for the same boundary
- evidence index rows proving old behavior
- relevant ADRs

Exclude:

- broad product strategy unless the review is strategy-specific
- unrelated archived audits
- semantic search snippets without source paths

---

## Research-to-Decision Flow

1. Create `docs/research/{slug}.md` only when external facts materially affect a decision.
2. Record sources, findings, caveats, and date.
3. Write ADR or decision log row that consumes the research.
4. Link research from the decision as supporting evidence.
5. Keep the decision as authority; research is evidence, not policy.

---

## Hypothesis Tracking

1. State the hypothesis in an eval artifact or `docs/hypotheses/{slug}.md`.
2. Define evidence required to support or reject it.
3. Link tasks that collect evidence.
4. Update state after eval or pilot data.
5. Convert supported architecture implications into ADRs.

Example:

```text
Hypothesis: Text-only RAG is sufficient for lead-response service-area questions.
Evidence needed: hit@3 >= 0.80, no-answer accuracy >= 0.90, no tenant leakage.
Decision link: ADR-002 production embedding provider.
State: testing.
```

---

## Cross-Project Retrieval

Use cross-project retrieval when:

- a project reuses a capability pattern from another repo
- a repeated finding appears in two or more repos
- an eval design should be standardized
- an ADR tradeoff recurs

Workflow:

1. Build or refresh project manifests.
2. Create a vault project map per repo.
3. Add a pattern note only when the reuse constraint is clear.
4. Link pattern note back to canonical project artifacts.
5. Add project task `Context-Refs` only if the pattern changes implementation behavior.

Example pattern candidates in the current portfolio:

- text-only RAG with explicit `insufficient_evidence`
- deterministic scoring before LLM synthesis
- bounded tool-use with unsafe-action gates
- single-user private assistant memory boundaries
- eval artifacts as phase-gate evidence

