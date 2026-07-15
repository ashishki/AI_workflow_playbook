from __future__ import annotations

from types import SimpleNamespace

from ai_workflow_harness_lab.comparison import effective_score
from ai_workflow_harness_lab.runner import task_score


def test_required_verification_failure_overrides_later_passing_scorer() -> None:
    failures = [
        {
            "invalid_run": False,
            "score_treatment": "count_as_task_failure",
        }
    ]

    assert effective_score([1.0, 1.0], failures) == 0.0


def test_infrastructure_failure_does_not_create_capability_score() -> None:
    failures = [
        {
            "invalid_run": True,
            "score_treatment": "invalid_run_exclude_from_capability_score",
        }
    ]

    assert effective_score([1.0], failures) == 1.0


def test_run_result_score_counts_required_verification_failure() -> None:
    failures = [
        {
            "invalid_run": False,
            "score_treatment": "count_as_task_failure",
        }
    ]

    assert task_score([SimpleNamespace(score=1.0)], True, failures) == 0.0
