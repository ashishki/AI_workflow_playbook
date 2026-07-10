from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SCORER_VERSION = "1.0.0"


def write_scorer_output(
    output_dir: Path,
    scorer_id: str,
    task_id: str,
    verdict: str,
    score: float,
    metrics: dict[str, Any],
    failure_records: list[dict[str, Any]],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "playbook.scorer_output.v1",
        "scorer_id": scorer_id,
        "scorer_version": SCORER_VERSION,
        "scorer_code_hash": code_hash(),
        "task_id": task_id,
        "verdict": verdict,
        "score": score,
        "metrics": metrics,
        "failure_records": [record["failure_id"] for record in failure_records],
    }
    path = output_dir / f"{scorer_id}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def code_hash() -> str:
    digest = hashlib.sha256()
    for path in sorted(Path(__file__).resolve().parents[1].glob("scorers/*.py")):
        digest.update(path.read_bytes())
    return digest.hexdigest()


def failure(
    task_id: str,
    run_id: str,
    failure_id: str,
    failure_class: str,
    message: str,
    *,
    owner_class: str = "model",
    stage: str = "scoring",
    retryable: bool = False,
    retry_count: int = 0,
    terminal: bool = True,
    score_treatment: str = "count_as_task_failure",
    invalid_run: bool = False,
) -> dict[str, Any]:
    return {
        "schema_version": "playbook.failure_record.v1",
        "failure_id": failure_id,
        "run_id": run_id,
        "task_id": task_id,
        "stage": stage,
        "failure_class": failure_class,
        "owner_class": owner_class,
        "retryable": retryable,
        "retry_count": retry_count,
        "terminal": terminal,
        "message": message,
        "evidence_refs": [],
        "score_treatment": score_treatment,
        "invalid_run": invalid_run,
    }
