# Generation Eval Plan

## Purpose

Generation eval measures the answer produced from retrieved evidence. It must be
separate from retrieval eval so failures can be localized.

## Inputs

Each case should record:

- question
- retrieved context
- generated answer
- expected answer or rubric
- citation requirements
- no-answer expectation
- risk slice

Do not give a faithfulness judge hidden ground truth when the metric is meant to
check whether the answer is supported by retrieved context.

## Metrics

| Metric | What it measures |
|--------|------------------|
| Faithfulness | Claims are supported by retrieved context |
| Completeness | Answer covers the question within available evidence |
| Relevance | Answer stays on task |
| Citation correctness | Citations support the exact claims made |
| No-answer correctness | Model refuses or returns insufficient evidence when context is weak |
| Unsafe answer rate | Output violates policy or regulated-data constraints |
| Human correction rate | Operator had to fix or reject the answer |

## Judge Use

LLM judges may score faithfulness, completeness, and relevance after calibration
against human labels. Before calibration, judge scores are advisory and should
not be the only release gate.

## Failure Slices

Track at least these slices when relevant:

- stale context
- conflicting context
- partial evidence
- long context
- multilingual or transliterated terms
- tables/forms
- scanned documents/OCR
- restricted data
- unsupported user request

