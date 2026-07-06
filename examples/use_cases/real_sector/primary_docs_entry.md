# Primary Documents Entry

## Problem

Accountants manually enter invoice, act, and waybill fields, causing delays and
duplicate or incorrect records.

## AI Opportunity

Document upload -> extracted fields -> accountant review. Deterministic
validation and duplicate checks should own final acceptance.

## Data Required

Invoices, acts, waybills, vendor master data, field schemas, accounting system
rules, OCR samples.

## Risk and HITL

Risk: wrong amount, VAT, counterparty, duplicate document, PII leakage.
Accountant reviews in MVP.

## Evaluation Plan

Field-level accuracy, rejection rate, duplicate detection precision/recall, OCR
quality, human correction rate.

## MVP Scope

Upload common invoice formats, extract required fields, validate totals, queue
for approval.

## Production Hardening

Vendor-specific parsers, OCR monitoring, access controls, retention policy,
and integration with accounting software.

