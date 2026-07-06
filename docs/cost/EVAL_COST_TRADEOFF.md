# Eval Cost Tradeoff

## Purpose

Eval depth should match risk. Too little eval creates false confidence. Too much
eval makes teams skip the gate.

## Eval Depth Matrix

| Risk | Minimum eval | Typical cadence |
|------|--------------|-----------------|
| Low | deterministic tests and small manual sample | per PR or task |
| Medium | seeded regression, capability eval, cost/latency check | per PR and release |
| High | human labels, calibrated judge, stop-ship slices, trace review | release and risky PRs |
| Regulated | control evidence, audit trace, human authority, calibration | release gate |

## Tradeoff Questions

- Which failures are cheap enough for manual review?
- Which failures must be deterministic blockers?
- Which eval slices can run async without blocking developer flow?
- What is the cost per successful task after failed attempts and judge cost?
- What evidence justifies reducing the eval set?

