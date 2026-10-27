# Privacy boundary design checks

Use the sections relevant to the target system. These are engineering review
questions and proposed invariants, not a ready-made runtime or a compliance test.

Contents: [contract](#boundary-contract), [identity](#detection-and-identity),
[mapping](#mapping-and-lifecycle), [retrieval](#retrieval-and-secondary-destinations),
[output](#output-and-execution), [failures](#failure-decisions),
[sources](#source-notes-and-scope).

## Boundary contract

Record one row per route or sensitive attribute, not just per entity type:

| Source / data | Actor and tenant | Purpose / action | Destination | Outcome | Permitted release |
|---|---|---|---|---|---|
| Synthetic task owner | Authorized project member | Summarize tasks | External model | Mask | Display name to this member only |
| Synthetic private phone | Same member, no phone permission | Summarize tasks | Model or tool | Block/remove that attribute | None |

Decide whether to reject the whole request or safely omit a field without
changing the requested meaning. Record the reason and policy version. Obtain
identity from authenticated service context; ignore identity claims in prompt
text and reject spoofed client identity headers at the trusted ingress.

## Detection and identity

- Keep detector evidence (span, type, confidence when meaningful, source) apart
  from the final policy decision. Assess regex, NER, language coverage, and
  bounded decoding against the actual corpus; do not mandate a particular model.
- Normalize for matching without destroying original offsets or conflating
  people. Inflection and transliteration are candidate matches, not proof of
  identity. A surname shared by two people stays ambiguous without evidence.
- Distinguish an entity from its attributes: permission to name a person does
  not authorize their phone, salary, health data, or customer relationship.
- Reserve the alias namespace. Escape or reject literal alias-like input before
  issuing trusted references, and retain provenance through retrieved documents
  and tool responses. An attacker can reproduce an already issued token;
  unpredictable formatting alone cannot fix disclosure authorization.
- Keep canonical IDs stable only inside the authorized retrieval system. Avoid
  exposing raw identifiers, deterministic name hashes, or global aliases that
  enable correlation across otherwise separate contexts.

## Mapping and lifecycle

Keep the entity registry separate from the temporary alias-to-entity mapping.
Bind every lookup to the authorized tenant, actor/conversation boundary, request,
and policy context; a shared conversation needs an explicit participant policy.
Specify atomic allocation, uniqueness, immutable entries, and concurrency tests.

Set retention, capacity, and deletion requirements from the product's purpose.
On expiry, revocation, overflow, or store failure, withhold the protected result
or return an independently safe redacted result. Never silently rebuild a stale
mapping from model text. Remap retained history coherently or invalidate it.
Longer-lived investigative mappings need separate encrypted storage, access
control, key management, and audited reveal; do not add that storage by default.

## Retrieval and secondary destinations

Check ingestion as well as query time: raw text may already have left through an
embedding API, document parser, reranker, or analytics SDK before chat masking.
Apply source ACLs before external processing and context assembly. An entity
directory cannot broaden those ACLs. Recheck authorization at release when
permissions can change during a request.

For an external index, decide which metadata and representations may leave;
masked text or embeddings can retain identifying context. For an internal index,
restrict canonical IDs and raw values to that service. Keep aliases coherent
across the query and selected documents; do not use independently numbered
document placeholders as cross-document identity keys. Compare retrieval on a
synthetic authorized baseline with the proposed representation.

Inspect cached responses, vector metadata, logs, traces, exception messages,
queue payloads, retries, exports, backups, and model evaluation records. Define
their isolation and deletion rules. Audit release decisions with safe references
and outcomes; do not log the plaintext mapping as evidence of auditing.

## Output and execution

| Surface | Required design decision |
|---|---|
| Text, citations, URLs | Validate all emitted content; restore only permitted attributes for this recipient. |
| JSON and other structures | Parse and enforce an allowed schema/field policy; do not run global string replacement over serialized output. |
| Tool calls | Allowlist the tool and argument shape, check the action against current user permissions, and resolve permitted aliases only in the trusted adapter before execution. |
| Tool results | Reclassify and transform before another model call; include errors and retries. |
| Streaming | Buffer complete output for strict pre-release checking; a bounded window needs an explicit residual-risk decision and boundary-spanning tests. Post-scanning cannot retract released bytes. |

Unknown tokens never trigger a directory search. Known tokens still require
recipient, field, action, and source permission checks. Scan for both unexpected
aliases and raw sensitive output; a model can emit personal data without using
an alias. Evaluate indirect identifiers and contextual re-identification too.

## Failure decisions

Specify safe outcomes for a missing detector, unavailable policy/mapping,
ambiguous identity, unsupported document type/language, malformed output, denied
tool call, and revoked source. Distinguish a useful redacted answer from a silent
allow. Keep authorization outside the LLM, including any LLM-based safety judge.

## Source notes and scope

- [Andrey Nepryakhin / AGIMA, original article](https://habr.com/ru/companies/agima/articles/1081356/):
  conceptual basis for separating identity from hidden values and retaining
  useful search relationships through a protected mapping. The article's local
  deployment settings and operational claims are not acceptance evidence here.
- [OWASP, Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html):
  primary guidance for deny-by-default decisions and authorization on each request.
- [OWASP, LLM Prompt Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html):
  primary guidance for untrusted retrieved content, tool validation, and least privilege.
- [Presidio, anonymization operators](https://presidio.dataprivacystack.org/anonymizer/):
  examples of transformation primitives; selecting an operator does not implement
  the application's identity, authorization, or state-management contract.

This Playbook adaptation adds explicit alias-collision handling, concurrency,
revocation, ingestion/telemetry checks, and utility gates. These are design
recommendations to verify in the target system, not quoted implementation facts
about AGIMA. No article text or third-party executable is vendored. Reversible
mapping is not a claim of anonymity or a legal opinion about any jurisdiction.
