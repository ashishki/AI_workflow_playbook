Diagnose and repair a synthetic fulfillment replay incident in this repository.
The replay application joins warehouse operations, checkout revisions and refund
provider deliveries. Current records show missing holds, incorrect checkout
state and refund totals. Three independently reproducible source defects interact.
Establish their causes from source and current evidence; distinguish stale
historical advice from records for build r31. Preserve unrelated behavior.

Read README.md, docs/contracts.md and docs/incident.md. Replay with
python -B -m src.replay data/current/combined.json; run the supplied checks with
python -B -m unittest discover -s tests -v. Only stdlib and local synthetic data
are needed. Inputs, documents, configs and tests are immutable. You may modify
existing src/**/*.py files, diagnosis.json and STATE.md only. Fix the fewest
source files that address causes, rather than changing expectations or masking
the incident. Keep the replay API and public output contract intact. One main
agent writes final shared source changes; investigators may report findings.

Write diagnosis.json as an object with defects (exactly three objects),
verification (object with commands and observed_results lists) and remaining_limits
(list). Each defect has source_files (list of actual causal paths), evidence_ids
(list of record_id, event_id or trace_id values from immutable records), mechanism
(explain the erroneous operation and correct invariant), impact (causal downstream
consequences), stale_evidence_ids (list of specific excluded historical IDs).
Cite the current triggering records and supporting trace(s), rather than only
test names or vague filenames. Explain why historical diagnoses are inapplicable.
Record actual local commands and observed outcomes in STATE.md, as well as
remaining limits and the next safe step. Do not claim live/production success.
