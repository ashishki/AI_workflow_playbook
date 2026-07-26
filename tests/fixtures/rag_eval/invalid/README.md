# RAG Eval Negative Fixtures

These artifacts are intentionally invalid and are used to document failure
shapes for the provider-neutral RAG Eval v2 validator. Unit tests also create
mutated temporary copies of the valid fixture to verify exact failure
semantics such as hash mismatch, path traversal, unknown observation cases,
uncalibrated blocking judge policy, and contaminated holdout metadata.

