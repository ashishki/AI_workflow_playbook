# Monitoring and Fallback Checklist

## Runtime Signals

| Signal | Why it matters |
|--------|----------------|
| success rate | Routine reliability |
| retry rate | Hidden instability |
| timeout rate | SLA or dependency issue |
| dead-letter rate | Unhandled failures |
| cost per completed job | Budget health |
| p95 queue delay | Backpressure |
| p95 runtime | Latency/SLA |
| human handoff rate | Automation fit |
| unsafe-action blocks | Permission pressure |

## Fallback Requirements

Every routine needs:

- fallback action
- owner notification path
- rollback or compensation path when possible
- dead-letter review process
- budget-overrun behavior
- disable switch

