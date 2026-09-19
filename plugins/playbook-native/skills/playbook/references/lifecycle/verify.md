# Verify

Verify the user's observable outcome on the current changed version. Exercise the
main path, important exception and data preservation. A green build, schema or test
count alone is insufficient. For UI follow the frontend browser procedure: right
checkout, actual result, narrow/wide view, fresh screenshots actually inspected.
Disclose unavailable browser and diagnostics rather than crediting another process.

After code changes use the existing [Role Runner](../review.md), including quick
mode. Read status AND verdict, verify currency, fix confirmed findings and rerun
relevant checks. Fresh read-only review is not certainty; incorrect findings need
reasoned disposition. Deep Review covers accumulated architecture/requirements/code
and evidence on material boundaries or when project policy requires it. No mandatory
four reviewers per tiny task, and no silent relaxation of existing project gates.

For AI/RAG separately exercise data readiness, retrieval, answer/citations, no-answer,
conflict/freshness/access and the real end-to-end call. For tools include parameters,
permissions, retry/duplicate and unknown external outcome. Use task examples plus
fresh acceptance cases. Correctness labels need independent evidence or domain
judgment: the implementer's JSON assertion is not ground truth. LLM judges are
advisory unless appropriately calibrated. Reuse available eval tools; do not install
the author's whole lab. Synthetic fixtures are not real-account evidence.

Deliver what passed/failed/not run, actual evidence, open risks and a usable preview.
Do not upgrade blocked review or a mocked integration to completed. Keep private
records local; never weaken permissions to make a check pass.
