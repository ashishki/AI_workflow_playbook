# Evaluation scenarios and evidence

Evaluate the eventual application using synthetic examples. A scenario list is
a test plan, not an executed test suite or proof that a gateway is secure.

## Application checks to propose

Use a fake provider/transport that captures outbound requests, tool effects, and
released chunks. Assert what crossed each boundary, not only a detector's label.
Reuse existing offline tests; hand off new test implementation through the
project's normal task process. Keep any unmasked comparison inside the test
boundary, with synthetic fixtures only.

| Case | Synthetic setup | Observable acceptance condition |
|---|---|---|
| Identity continuity | One person in six Russian cases and Latin transliteration | Correct authorized identity and consistent alias across query/results; no raw identifier in captured external payload. |
| Ambiguous name | Two people share a surname | No false merge or arbitrary identity selection; explicit ambiguity handling. |
| Attribute policy | Name allowed for display, phone denied | Name permission does not release the phone in any output or tool argument. |
| Literal-token collision | User/document contains the exact alias format before issuance | Literal content cannot acquire the authority of a subsequently issued reference. |
| Known-token abuse | Output repeats a valid alias in a forbidden field/recipient route | Mapping membership alone does not authorize disclosure. |
| Unknown-token probe | Output guesses an unissued alias | No global lookup, reveal, or hidden fallback. |
| Scope and replay | Same alias text in another user, tenant, or expired conversation | No cross-scope restoration; retained history cannot resurrect expired permissions. |
| Concurrent allocation | Parallel requests mention different entities | No reassignment, overwritten mapping, or identity mix-up. |
| Source ACL/revocation | User lacks a source, or access is revoked after retrieval | Unauthorized context never reaches an external processor; release rechecks current rights. |
| Structured output | Alias in disallowed JSON path, nested value, citation, or URL | Parse/field policy rejects unauthorized release; no blanket replacement. |
| Tool boundary | Model requests an unauthorized tool/argument; tool returns PII | Zero unauthorized effects; returned data is transformed before the next outbound call. |
| Streaming | Sensitive value/alias spans chunks or appears late | In strict mode no output is released before complete validation; record weaker-mode residual exposure separately. |
| Failure/fallback | Detector, policy, mapping, or provider fails; capacity exceeded | No raw-data fallback through retries, backup models, or error messages. |
| Ingestion and telemetry | Sensitive text enters embeddings, reranking, logs, cache, export | Captured sinks contain only policy-permitted data; storage isolation and retention are exercised. |
| Indirect identification | Unique role/event plus dates remains after masking | Residual identifiability is assessed; direct-identifier removal is not counted as anonymity. |
| Retrieval utility | Labeled queries with expected authorized documents | Identity-aware retrieval remains useful under a predeclared comparison gate. |

Record unsupported languages, modalities, routes, and omitted cases with reasons.
Include adversarial document instructions that ask for mapping or raw data;
check data release and tool effects, not whether the model verbally refuses.

## Separate metrics

| Dimension | Measure and decision rule |
|---|---|
| Detection | Precision/recall by entity type and language; state labeled count and missed classes. |
| Resolution | Correct matches, false merges, and unresolved cases separately; do not reward guessing to reduce ambiguity. |
| Authorization | False allows and false denies on labeled actor/source/attribute/action/destination decisions. |
| Disclosure | Unauthorized values, cross-scope reveals, and unauthorized tool effects: zero in the tested cases, with denominator and route coverage stated. |
| Retrieval/task utility | Recall@k or nDCG@k plus task success against the same authorized synthetic baseline; choose k and acceptable degradation before observing the candidate. |
| Cost/latency | p50/p95 added latency and resource cost, including detection and streaming buffers; set the budget from the product. |

Never combine these into one protection percentage. Zero observed leaks is a
necessary regression gate for the tested cases, not proof of zero deployment
risk. Report source revision, fixture/version, route, policy, model/configuration
where applicable, commands, observed results, and what was not run. Propose a
synthetic canary only when operational monitoring is in scope; never schedule it
or choose a paid frequency as a side effect of this skill.
