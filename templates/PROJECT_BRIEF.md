# Project Brief Template

Use this document before running `prompts/STRATEGIST.md`. The goal is not to pre-design the system, but to give the Strategist enough context to choose the right solution shape, governance level, runtime tier, and model strategy without guessing.

Write short, concrete answers. If something is unknown, say `unknown` rather than inventing detail.

---

## 1. Project

- **Project name:**
- **One-sentence summary:**
- **Why this project exists:**
- **What success looks like in v1:**

## 1b. Problem Fit and Adoption Reality

Answer these before describing the desired architecture. The Strategist uses
this section to avoid designing a polished AI system around an unproven or
demo-only need.

- **Concrete operational pain:** What currently breaks, stalls, costs too much,
  or depends on fragile human effort?
- **Current workaround:** How is the team solving this today without the new
  system?
- **Why existing process is insufficient:** Why are checklists, CI, ordinary
  code review, scripts, or manual SOPs not enough?
- **First user / buyer / operator who feels the pain:**
- **What would make v1 not worth adopting:**
- **Adoption proof metric:** What measurable signal proves this is useful in
  practice, not only impressive in a demo?
- **Claims that are out of bounds before evidence:** e.g., "replaces an
  engineer", "fully autonomous", "production-ready agent swarm".
- **Work AI will not replace:** Which judgment, approval, accountability, or
  domain-expert work remains human-owned?

## 2. Users and Workflows

- **Primary users / operators:**
- **Main workflow 1:**
- **Main workflow 2:**
- **Main workflow 3:**

## 3. Scope

- **In scope for v1:**
- **Out of scope / non-goals:**

## 4. AI Scope

- **Where AI may be needed:**
- **Where AI is explicitly not wanted:**
- **External agent skills planned:** none / marketplace / GitHub / vendor / cross-project / unknown
- **If external skills are planned, source and install scope:**
- **External skill capabilities expected:** shell / network / file read-write / env secrets / MCP tools / persistent state / none / unknown
- **Possible retrieval / RAG need:**
- **If retrieval is needed, is text-only likely sufficient or is multimodal evidence truly required:**
- **If multimodal may be needed, which modalities and why:**
- **Possible tool-use need:**
- **Possible planning / agentic behavior need:**

## 5. Deterministic Candidates

List the parts that probably should stay deterministic unless the Strategist proves otherwise.

- **Validation / policy checks:**
- **Routing / decision rules:**
- **Calculations / transformations:**
- **Retries / idempotency / audit triggers:**

## 6. Human Approval Boundaries

- **What actions must require human approval:**
- **What can be automated safely:**
- **Why these boundaries matter:**

## 7. Risk and Error Cost

- **What is expensive if the system is wrong:**
- **What is expensive if the system is slow:**
- **What is expensive if the system is inconsistent / variable:**
- **Blast radius if it fails badly:**
- **Audit / explainability needs:**

## 8. Data

- **Primary data sources:**
- **Approximate data volume:**
- **Does data change frequently:**
- **Sensitive / regulated data present:**
- **Retention / deletion expectations:**

## 8b. Continuity and Evidence

- **Which decisions are likely to be revisited later:**
- **What prior evidence or proof will future agents need to find quickly:**
- **Will work span multiple sessions / agents / weeks:**
- **Any existing docs, ADRs, audits, or notes that should become retrieval anchors:**

## 9. Integrations

- **External APIs / services:**
- **Databases / storage:**
- **Auth / identity provider:**
- **Webhooks / messaging / queues:**

## 10. Constraints

- **Preferred stack:**
- **Deployment target:**
- **Budget constraints:**
- **Latency / throughput expectations:**
- **Compliance requirements:**
- **Network / security restrictions:**

## 11. Runtime and Operations

- **Should runtime stay simple (managed service / container) if possible:**
- **Any need for shell, package, or toolchain mutation at runtime:**
- **Any need for privileged actions or long-lived isolated workers:**
- **Recovery / rollback expectations:**

## 12. Model and Cost Expectations

Only fill what you know. The Strategist should still make the final recommendation.

- **Cost sensitivity:** low / medium / high
- **Latency sensitivity:** low / medium / high
- **Expected request / task volume:**
- **If AI is used, should the system prefer smaller / cheaper models by default:**
- **Any required capabilities:** reasoning / multimodal / function calling / long context / structured output
- **Preview-model tolerance:** none / low / medium / high
- **Per-run / per-task budget:**
- **Monthly project budget or budget ceiling:**
- **Who approves budget overruns:**
- **Should budget overruns warn, block, or require approval:**
- **Expected attribution needs:** per user / per tenant / per feature / per agent / per workflow
- **Allowed model escalation path:**
- **Maximum acceptable retries / tool calls / parallel agents:**
- **Expected workload classes:** architecture review / implementation fix / summarization / user-facing generation / evaluation / other
- **Prompt caching likely useful:** yes / no / unknown
- **Batch or async lane acceptable for any workload:** yes / no / unknown
- **Dynamic routing or cascades expected:** no / maybe / yes
- **If routing/cascades are expected, what quality floor must hold:**
- **What cost metric matters most:** cost per call / cost per successful task / monthly ceiling / per-user margin

## 13. Success Metrics

- **Business success metric:**
- **Quality metric:**
- **Latency metric:**
- **Cost metric:**
- **Operational metric:**

---

## Usage

1. Copy this template into your project notes or fill it inline in chat.
2. Send the completed brief to the Strategist.
3. Let the Strategist ask one batch of clarifying questions.
4. Use the resulting architecture package as the Phase 1 input to the rest of the playbook.
