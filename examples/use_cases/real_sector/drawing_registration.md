# Drawing Registration

## Problem

Engineering drawings and revisions are registered slowly or inconsistently,
creating search and version-control issues.

## AI Opportunity

Draft registry entry from PDF/CAD metadata and visible title block. Engineer or
document controller approves.

## Data Required

Drawings, title blocks, CAD/PDF metadata, revision history, project codes, PLM
or document-control schema.

## Risk and HITL

Risk: wrong revision, duplicate registration, access-control leak. Human
approval before registry write.

## Evaluation Plan

Revision detection accuracy, metadata extraction accuracy, duplicate detection,
human correction rate.

## MVP Scope

PDF drawing upload -> metadata draft -> duplicate warning -> approval.

## Production Hardening

PLM integration, access control, revision audit, CAD parser support, and
rollback of bad registry entries.

