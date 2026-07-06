# Overdue Claims Agent

## Problem

Finance teams miss overdue invoices or spend time drafting repetitive claim
letters.

## AI Opportunity

Detect overdue invoices and draft claim letters. Sending remains finance/legal
approved.

## Data Required

ERP invoice data, payment status, customer contracts, claim letter templates,
legal escalation rules.

## Risk and HITL

Risk: wrong claim, incorrect debtor, premature escalation, legal exposure.
Finance/legal approves before sending.

## Evaluation Plan

Overdue detection accuracy, wrong-claim rate, legal escalation recall, human
edit distance, and cost per approved letter.

## MVP Scope

Read-only ERP export -> overdue list -> draft letter -> approval queue.

## Production Hardening

ERP integration, contract clause checks, audit logs, customer communication
history, and rollback/correction process.

