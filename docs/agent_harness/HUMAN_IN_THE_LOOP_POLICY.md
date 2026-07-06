# Human-In-The-Loop Policy

## Purpose

Human-in-the-loop is an authority boundary, not a decorative confirmation step.

## Handoff Triggers

| Trigger | Required action |
|---------|-----------------|
| Missing required context | Ask for the missing input |
| Ambiguous user intent with high error cost | Ask a clarifying question |
| Destructive or irreversible action | Require explicit approval |
| Permission escalation | Route to owner |
| Budget overrun | Request approval or stop |
| Low confidence in high-risk output | Human review |
| Judge/model disagreement | Human review of disagreement slice |
| Compliance or payment action | Human remains final authority |

## Handoff Record

Record each handoff with:

- run ID and task ID
- question or approval request
- risk reason
- options presented
- human decision
- timestamp
- resulting action

## Anti-Pattern

Do not ask humans to rubber-stamp opaque output. The handoff must show the
evidence, risk, and action that needs authority.

