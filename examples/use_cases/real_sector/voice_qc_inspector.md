# Voice QC Inspector

## Problem

Factory inspectors record defects slowly or after the fact, causing incomplete
defect data and delayed quality feedback.

## AI Opportunity

Voice note -> structured defect draft -> inspector approval. The system should
not submit final quality records without human confirmation.

## Data Required

Audio samples, defect taxonomy, product/line metadata, accepted defect reports,
and noisy-environment samples.

## Risk and HITL

Risk: wrong defect code, missed severity, noisy audio, worker privacy.
Inspector approves every draft in MVP.

## Evaluation Plan

WER, field extraction accuracy, defect taxonomy accuracy, human correction rate,
p95 draft latency, and cost per approved report.

## MVP Scope

Mobile voice note upload, transcription, structured draft, taxonomy suggestion,
and approval queue.

## Production Hardening

Offline mode, noisy factory audio tests, audit trail, language/local accent
coverage, and privacy policy.

