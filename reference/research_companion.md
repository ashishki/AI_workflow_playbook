# Research Companion (Experimental)

Status: EXPERIMENTAL — subject to evaluation per §8 Experiment E3 in the
integration assessment. Until that experiment shows measurable value, this
guide can be removed without an ADR.

Skill descriptor: `templates/skills/research_skill.md`

A development-process research workflow that complements ADRs and
`docs/DECISION_LOG.md` by giving them better source provenance. Different
from the RAG capability profile: RAG governs runtime application retrieval;
this guide governs *how a Strategist or reviewer collects evidence for a
decision* (e.g., "what is current best practice for HIPAA audit log
integrity?", "which library should we use for X?", "is the proposed runtime
tier still the minimum sufficient choice?").

This guide is opt-in. It does not become canonical.

---

## When to invoke

Use the Research Companion when:

- An architectural choice carries material risk and the Strategist wants
  source-grounded evidence before drafting an ADR.
- A compliance interpretation must be traced (e.g. retention thresholds for
  a regulated framework).
- A library or technology selection has more than one defensible answer and
  the team will be asked "why this choice" later.
- A reviewer flags a decision as under-justified and asks for evidence
  before approving the phase gate.

Do not use the Research Companion when:

- A canonical document already answers the question.
- The decision is reversible at low cost — just decide.
- The question is about *how the existing system behaves* — that is code
  reading and tests, not research.

---

## Forbidden actions

- The companion does not replace ADRs. ADRs remain the decision authority.
- The companion does not modify `docs/IMPLEMENTATION_CONTRACT.md`,
  `docs/ARCHITECTURE.md`, `docs/spec.md`, `docs/tasks.md`, or
  `docs/CODEX_PROMPT.md`.
- The companion does not stand in for code-level evidence (tests, evaluation
  artifacts, review findings).
- The companion does not author tasks. Tasks created from research findings
  go through the normal Strategist or human review path.
- The output file is a retrieval surface (`docs/research/{slug}.md`), never
  authority. Canonical documents win in any conflict — see the conflict
  precedence in `templates/skills/SKILL_INTERFACE.md`.

---

## Inputs

- A specific research question — narrow, answerable, with a deadline.
- Scope constraints — what is in/out of scope; relevant frameworks; relevant
  parts of the system.
- The consuming artifact — the ADR or `docs/DECISION_LOG.md` row that will
  cite the research note. If the consumer is unknown, the question is
  probably not ready for research.

---

## Outputs

A research note written to `docs/research/{topic-slug}.md` using
`templates/research/RESEARCH_NOTE.md`. Contents:

- the question, scope, and constraints
- a Sources table (URL, access date, quality tier, one-line summary)
- per-source Evidence rows (claim, supporting verbatim quote, page/section,
  tier)
- residual uncertainty (what is still unknown after this research)
- recommended decision (one sentence, plus rejected alternatives)
- consumed-by link (the ADR or DECISION_LOG row that cites this note)

The Evidence section is append-only. The Recommendation section may be
revised once before the consumer cites it, and only if the revision is
recorded in the note's revision history.

---

## Source quality rubric

| Tier | Description | Examples |
|------|-------------|----------|
| 1 | Primary source: standards body, RFC, official spec, government regulation, vendor official documentation, peer-reviewed paper | RFC 9457, NIST SP 800-53, HIPAA Privacy Rule text, PostgreSQL official docs |
| 2 | Authoritative engineering source: vendor maintainer blog, ASF/CNCF/PSF maintainer communication, well-known security advisory | PostgreSQL committer blog, OpenSSF advisory, CVE entry |
| 3 | Engineering blog from a reputable team or named expert; conference talk | Cloudflare/AWS/Google engineering blog, KubeCon talk notes |
| 4 | Forum or Q&A community content; uncited summary | Stack Overflow answer, Reddit thread |

A claim cited from tier 4 alone is treated as unverified. AI-generated
content is rejected as a primary source — its provenance and freshness are
not auditable.

---

## Stale-source policy

A source older than 18 months requires an explicit justification in the
research note (e.g. "the standard has not changed since this date" with a
link to the standards body confirming current applicability). Stale sources
without justification are rejected by the consuming reviewer.

When a research note's recommendation is older than 18 months, it must be
re-validated before being cited again.

---

## Citation policy

Every claim used in the consuming document (ADR, DECISION_LOG row, spec
update) must point to a row in the research note. The pattern is:

> "Audit log retention is set to 6 years (research:
> docs/research/hipaa-audit-retention.md#R-3)."

Evidence rows are numbered (`R-1`, `R-2`, ...) so that citations remain
stable when the note is updated.

---

## Evidence log format

Each Evidence row records the date the evidence was collected, the source
tier, and a verbatim supporting quote (no paraphrase). If a row is later
invalidated (source retracted, methodology found to be flawed), it is marked
`INVALIDATED: <reason>` rather than deleted.

---

## Conflict rules

When a research note conflicts with a canonical document (architecture,
contract, spec, ADR), the canonical document wins. The research note is
updated to reflect the actual decision — not the other way around. If the
canonical document needs to change because of new evidence, that change goes
through an ADR.

---

## Promotion path

If experiment E3 shows that ADRs consuming a research note have a measurably
lower revision rate and fewer rationale-gap review findings, the Research
Companion may be promoted from EXPERIMENTAL to OPTIONAL via:

- Skill descriptor `Status: optional` in
  `templates/skills/research_skill.md`
- A small mention in `PLAYBOOK.md §10 Documentation Set → Optional Skills`
  (no rule changes)

Promotion to a full Research Profile (with profile rules in
`IMPLEMENTATION_CONTRACT.md` and review checks RES-N) requires an ADR and a
sustained pattern of use across multiple projects. Until then, this remains
a guide only.

---

## Reading list

- `templates/skills/SKILL_INTERFACE.md` (skill descriptor format)
- `templates/skills/research_skill.md` (this skill's descriptor)
- `templates/research/RESEARCH_NOTE.md` (output template)
- `templates/DECISION_LOG.md` (consumer of research notes)
- `IMPLEMENTATION_CONTRACT.md §Continuity and Retrieval Rules` (general rule
  that retrieval surfaces are not authority)
