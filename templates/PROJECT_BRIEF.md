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
- **Service delta:** What improves besides FTE savings — cycle time, SLA,
  error rate, throughput, coverage, operator correction time, or customer
  experience?

## 1c. Evidence Plan From Day 1

Fill this before proposing architecture. If unknown, write `unknown` and let the
Strategist design a discovery task.

- **First proof metric:**
- **Evaluation dataset source:** production sample / human labels / synthetic
  seed set / replay logs / manual fixture / unknown
- **Minimum eval set size for v1:**
- **Known failure slices:** ambiguity / no-answer / stale data / permission
  boundary / tool failure / long context / unsafe output / other
- **Human review owner and budget:** role, sample size, expected minutes per
  item
- **Can an LLM judge be used:** no / advisory only / maybe after calibration /
  unknown
- **Judge calibration requirement:** none / required before release / unknown
- **Cost boundary for evaluation:** per run / per release / monthly / unknown
- **Release gate:** manual approval / CI eval gate / advisory report / unknown

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
- **Minimum sufficient shape expected:** deterministic / workflow / bounded
  tool-use / bounded agent / autonomous routine / hybrid / unknown
- **Why deterministic may be insufficient:**
- **Why fixed workflow may be insufficient:**
- **External agent skills planned:** none / marketplace / GitHub / vendor / cross-project / unknown
- **If external skills are planned, source and install scope:**
- **External skill capabilities expected:** shell / network / file read-write / env secrets / MCP tools / persistent state / none / unknown
- **Possible retrieval / RAG need:**
- **If retrieval is needed, is text-only likely sufficient or is multimodal evidence truly required:**
- **If multimodal may be needed, which modalities and why:**
- **Possible tool-use need:**
- **Possible planning / agentic behavior need:**
- **If tool-use or agentic behavior is likely, is a harness card required:**
  yes / no / unknown
- **Harness concerns already known:** tools / memory / retries / recovery /
  permissions / trace / human handoff / cost / latency / unknown

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

## 8a. Data Readiness

Use this section for RAG, extraction, analytics, or any AI behavior that depends
on external knowledge.

- **Source owners known:**
- **Formats involved:** PDF / DOCX / HTML / tickets / chats / database rows /
  spreadsheets / images / audio / other
- **Parser/OCR quality known:**
- **Duplicate or stale data risk:**
- **Required metadata:** source ID / date / owner / ACL / version / language /
  document type / other
- **Access-control boundary:**
- **PII or regulated fields requiring redaction:**
- **Gold evidence available:** query-to-document, input-to-output, or
  human-labeled examples

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
- **Evaluation budget:** per PR / per release / monthly / unknown
- **Expected judge cost:** none / advisory judge / calibrated judge / unknown
- **Expected human review cost:** minutes per item and sample size / unknown
- **Latency class:** interactive / human-blocking async / background batch /
  scheduled routine / unknown
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
- **Service delta metric:** cycle time / SLA / error rate / throughput /
  coverage / operator correction rate / other

---

## Usage

1. Copy this template into your project notes or fill it inline in chat.
2. Send the completed brief to the Strategist.
3. Let the Strategist ask one batch of clarifying questions.
4. Use the resulting architecture package as the Phase 1 input to the rest of the playbook.
