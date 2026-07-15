# PROMPT_PILOT_OUTCOME_CRITIC - Condition-Blind Human Review

You are the independent human Test Critic for one frozen pilot outcome pair.
Use only the supplied blind pair JSON. Do not access the protected mapping, raw
run, prompts, traces, agent prose, or repository history. Do not try to infer
which workflow produced A or B.

Review candidates A and B independently against the supplied task rubric.
Treat normalized verifier and scorer facts as evidence, not proof. Inspect the
allowed change content for semantic correctness, test weakening, hardcoding,
scope mismatch, and disagreement with those facts. A missing or invalid
required fact makes that candidate ineligible; it is not a loss for the other
candidate until adjudication admits the pair.

Record for each candidate:

- `eligible`: yes or no, with a concrete reason
- `rubric_result`: pass, fail, or unknown for every rubric item
- `oracle_concerns`: deterministic issue, bounded concern, or none
- `evidence_consistency`: consistent, inconsistent, or incomplete

Then record exactly one pair outcome: `A`, `B`, `tie`, or `inconclusive`.
Choose A or B only when both candidates are eligible and one has a materially
better rubric result. Use `tie` when eligible outcomes are equivalent. Use
`inconclusive` for invalid evidence, unresolved ambiguity, or a blinding leak.
Do not make an adoption decision or claim empirical improvement.

Write the result with `templates/PILOT_OUTCOME_CRITIC_REPORT.md`. Freeze the
completed report before a separate adjudicator accesses the protected mapping.
