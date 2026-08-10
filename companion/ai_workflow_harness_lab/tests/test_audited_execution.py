from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_workflow_harness_lab import audited_execution as audited


def init_demo(root: Path, *, max_rounds: int = 3) -> None:
    audited.init_run(
        root=root,
        run_id="run-1",
        original_goal_ref=".playbook-artifacts/context/F01/F01-S1.md",
        requirements=[{"id": "REQ-1", "description": "required pytest command passes"}],
        task_id="T14",
        feature_id="F01",
        slice_id="F01-S1",
        max_rounds=max_rounds,
    )


def write_receipt(root: Path, round_number: int, name: str = "tests") -> str:
    receipt = root / ".playbook-artifacts/audited-runs/run-1/rounds" / f"{round_number:04d}" / "receipts" / name / "receipt.json"
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text('{"status":"pass"}\n', encoding="utf-8")
    return str(receipt.relative_to(root / ".playbook-artifacts/audited-runs/run-1"))


def write_audit(root: Path, round_number: int, payload: dict[str, object]) -> None:
    path = root / ".playbook-artifacts/audited-runs/run-1/rounds" / f"{round_number:04d}" / "audit_report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_executor_claim_success_audit_rejects_state_requirements_unchanged(tmp_path: Path) -> None:
    init_demo(tmp_path)
    audited.propose_next_round(root=tmp_path, run_id="run-1")
    receipt_ref = write_receipt(tmp_path, 1)
    receipt_path = tmp_path / ".playbook-artifacts/audited-runs/run-1" / receipt_ref
    write_audit(
        tmp_path,
        1,
        {
            "schema_version": audited.AUDIT_REPORT_SCHEMA,
            "run_id": "run-1",
            "round": 1,
            "read_only": True,
            "verdict": "rejected",
            "receipts": [{"ref": receipt_ref, "sha256": audited.sha256_file(receipt_path)}],
            "findings": [{"id": "AUDIT-1", "message": "executor claim not proven"}],
        },
    )

    state = audited.apply_audit(tmp_path, "run-1", 1)

    assert state["requirements"][0]["status"] == "open"
    assert state["open_requirements"] == ["REQ-1"]


def test_apply_audit_blocks_missing_receipt(tmp_path: Path) -> None:
    init_demo(tmp_path)
    audited.propose_next_round(root=tmp_path, run_id="run-1")
    write_audit(
        tmp_path,
        1,
        {
            "schema_version": audited.AUDIT_REPORT_SCHEMA,
            "run_id": "run-1",
            "round": 1,
            "read_only": True,
            "verdict": "verified",
            "receipts": [{"ref": "rounds/0001/receipts/tests/receipt.json", "sha256": "0" * 64}],
            "requirement_results": [{"id": "REQ-1", "status": "verified"}],
        },
    )

    with pytest.raises(audited.AuditedExecutionError, match="receipt missing"):
        audited.apply_audit(tmp_path, "run-1", 1)


def test_verified_audit_advances_state_and_completes(tmp_path: Path) -> None:
    init_demo(tmp_path)
    audited.propose_next_round(root=tmp_path, run_id="run-1")
    receipt_ref = write_receipt(tmp_path, 1)
    receipt_path = tmp_path / ".playbook-artifacts/audited-runs/run-1" / receipt_ref
    write_audit(
        tmp_path,
        1,
        {
            "schema_version": audited.AUDIT_REPORT_SCHEMA,
            "run_id": "run-1",
            "round": 1,
            "read_only": True,
            "verdict": "verified",
            "receipts": [{"ref": receipt_ref, "sha256": audited.sha256_file(receipt_path)}],
            "requirement_results": [{"id": "REQ-1", "status": "verified", "evidence_refs": ["rounds/0001/audit_report.json"]}],
            "facts": [{"id": "FACT-1", "value": "required pytest command passes", "trust_status": "verified"}],
        },
    )

    state = audited.apply_audit(tmp_path, "run-1", 1)

    assert state["status"] == "complete"
    assert state["open_requirements"] == []
    assert state["facts"][0]["trust_status"] == "verified"


def test_done_without_verified_requirements_is_blocked(tmp_path: Path) -> None:
    init_demo(tmp_path)

    with pytest.raises(audited.AuditedExecutionError, match="done is blocked"):
        audited.propose_next_round(root=tmp_path, run_id="run-1", action="done")


def test_budget_exhausted_stops_run(tmp_path: Path) -> None:
    init_demo(tmp_path, max_rounds=1)
    audited.propose_next_round(root=tmp_path, run_id="run-1")
    receipt_ref = write_receipt(tmp_path, 1)
    receipt_path = tmp_path / ".playbook-artifacts/audited-runs/run-1" / receipt_ref
    write_audit(
        tmp_path,
        1,
        {
            "schema_version": audited.AUDIT_REPORT_SCHEMA,
            "run_id": "run-1",
            "round": 1,
            "read_only": True,
            "verdict": "rejected",
            "receipts": [{"ref": receipt_ref, "sha256": audited.sha256_file(receipt_path)}],
        },
    )

    state = audited.apply_audit(tmp_path, "run-1", 1)

    assert state["status"] == "stopped"
    assert state["stop_reason"] == "budget_exhausted"


def test_fresh_executor_context_excludes_old_executor_history(tmp_path: Path) -> None:
    init_demo(tmp_path)
    audited.propose_next_round(root=tmp_path, run_id="run-1")
    r1 = tmp_path / ".playbook-artifacts/audited-runs/run-1/rounds/0001/executor_report.md"
    r1.parent.mkdir(parents=True, exist_ok=True)
    r1.write_text("old executor conversation should not be copied\n", encoding="utf-8")
    receipt_ref = write_receipt(tmp_path, 1)
    receipt_path = tmp_path / ".playbook-artifacts/audited-runs/run-1" / receipt_ref
    write_audit(
        tmp_path,
        1,
        {
            "schema_version": audited.AUDIT_REPORT_SCHEMA,
            "run_id": "run-1",
            "round": 1,
            "read_only": True,
            "verdict": "rejected",
            "receipts": [{"ref": receipt_ref, "sha256": audited.sha256_file(receipt_path)}],
        },
    )
    audited.apply_audit(tmp_path, "run-1", 1)
    audited.propose_next_round(root=tmp_path, run_id="run-1")

    prompt = audited.executor_prompt(tmp_path, "run-1", 2)

    assert "old executor conversation should not be copied" not in prompt
    assert "Current Audited State" in prompt
