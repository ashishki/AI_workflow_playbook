# Nomenclature Normalization

## Problem

Messy item names create duplicate catalog entries, poor procurement analytics,
and manual matching work.

## AI Opportunity

Suggest canonical catalog matches with confidence and unknown detection.
Master-data owner approves merges.

## Data Required

Item names, units, attributes, supplier names, historical mappings, canonical
catalog, synonym dictionary.

## Risk and HITL

Risk: bad merge, wrong unit, supplier-specific ambiguity. Approval queue and
rollback are required.

## Evaluation Plan

Top-1/top-3 match accuracy, unknown detection, duplicate merge precision,
human correction rate.

## MVP Scope

Batch suggestions for one category with confidence and evidence.

## Production Hardening

Master-data workflow, rollback for bad merges, drift monitoring, category
ontology, and audit trail.

