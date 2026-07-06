# Workflow Use Case Scoring

## Purpose

Score AI workflow candidates with evidence, not enthusiasm.

## Scorecard

| Dimension | Scale | Evidence |
|-----------|-------|----------|
| Feasibility | 1-5 | Existing workflow clarity, integration complexity |
| Data readiness | 1-5 | Source quality, metadata, ownership |
| Eval readiness | 1-5 | Gold data, clear metrics, failure slices |
| Risk level | low/medium/high/regulated | Error cost, permissions, compliance |
| TCO complexity | low/medium/high | Build, inference, eval, operations |
| ROI proxy | low/medium/high | Time, SLA, error, throughput, service delta |
| Automation fit | deterministic/workflow/bounded agent/routine | Minimum sufficient shape |
| Deployment fit | local/GitHub Action/hosted/self-hosted/cloud function | Runtime and secret needs |

## Guardrail

A score without evidence is a hypothesis. Roadmaps should keep unsupported ROI
claims out of the acceptance criteria.

