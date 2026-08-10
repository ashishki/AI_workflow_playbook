from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import approve_feature_design
from tools import feature_design_lib
from tools import planning_depth


ROOT = Path(__file__).resolve().parents[2]


def write_design(root: Path, payload: dict[str, object]) -> Path:
    docs = root / "docs/design"
    docs.mkdir(parents=True)
    (root / "docs/PROJECT_BRIEF.md").parent.mkdir(parents=True, exist_ok=True)
    (root / "docs/PROJECT_BRIEF.md").write_text("# Brief\nApproved: human\n", encoding="utf-8")
    markdown = docs / f"{payload['feature_id']}.md"
    registry = docs / f"{payload['feature_id']}.design.json"
    markdown.write_text("# Feature Design\n", encoding="utf-8")
    registry.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return registry


def valid_design(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "playbook.feature_design.v1",
        "feature_id": "F01",
        "status": "review_required",
        "planning_depth": "designed_slices",
        "risk_level": "high",
        "brief_ref": "docs/PROJECT_BRIEF.md",
        "architecture_refs": [],
        "approval_policy": "human_required",
        "slices": [
            {
                "slice_id": "S01",
                "status": "planned",
                "user_visible_outcome": "User can run a bounded smoke path.",
                "scope": "Smoke path through contract and validator.",
                "allowed_files": ["app/**", "tests/**"],
                "forbidden_files": ["secrets/**"],
                "expected_interfaces": ["run_smoke()"],
                "verification": [
                    {
                        "id": "slice_tests",
                        "argv": ["{python}", "-m", "pytest", "tests/test_smoke.py", "-q"],
                        "cwd": ".",
                        "required": True,
                        "expected_exit_code": 0,
                        "timeout_seconds": 600,
                    }
                ],
                "review_checkpoint": "closed",
                "dependencies": [],
                "change_budget": "files<=4, lines<=200",
                "rollback": "revert slice diff",
            }
        ],
    }
    payload.update(overrides)
    return payload


def write_design_review_records(
    root: Path,
    payload: dict[str, object],
    *,
    product_verdict: str = "PASS",
    program_verdict: str = "PASS",
) -> None:
    reports = root / ".playbook-artifacts/reports/F01"
    reports.mkdir(parents=True, exist_ok=True)
    product = reports / "product_design_review.md"
    program = reports / "program_design_review.md"
    product.write_text(f"PRODUCT_DESIGN_REVIEW: {product_verdict}\nReview body.\n", encoding="utf-8")
    program.write_text(f"PROGRAM_DESIGN_REVIEW: {program_verdict}\nReview body.\n", encoding="utf-8")
    approve_feature_design.write_design_review_record(
        root=root,
        feature_id="F01",
        role="product_design_review",
        report_path=".playbook-artifacts/reports/F01/product_design_review.md",
        reviewed_design=payload,
        reviewer_binding="test:product",
    )
    approve_feature_design.write_design_review_record(
        root=root,
        feature_id="F01",
        role="program_design_review",
        report_path=".playbook-artifacts/reports/F01/program_design_review.md",
        reviewed_design=payload,
        reviewer_binding="test:program",
    )


def approve_payload(root: Path, registry: Path) -> dict[str, object]:
    payload = json.loads(registry.read_text(encoding="utf-8"))
    write_design_review_records(root, payload)
    approved = approve_feature_design.approve_registry_payload(
        root=root,
        registry_path=registry,
        payload=payload,
        human_id="human:tester",
        approval_method="test_harness",
        approval_ref="tests/unit/test_feature_design.py",
        approved_at="2026-07-29",
        review_refs=[],
        advisory_acknowledgement="none",
    )
    registry.write_text(json.dumps(approved, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return approved


def test_feature_design_accepts_valid_approved_human_design(tmp_path: Path) -> None:
    registry = write_design(tmp_path, valid_design())
    approve_payload(tmp_path, registry)

    findings, design = feature_design_lib.validate_design_file(tmp_path, registry)

    assert findings == []
    assert design is not None
    assert design["feature_id"] == "F01"
    assert feature_design_lib.design_is_approved(design, tmp_path, registry)


def test_markdown_edit_makes_approval_stale(tmp_path: Path) -> None:
    registry = write_design(tmp_path, valid_design())
    approve_payload(tmp_path, registry)
    (tmp_path / "docs/design/F01.md").write_text("# Feature Design\n\nChanged control flow.\n", encoding="utf-8")

    findings, design = feature_design_lib.validate_design_file(tmp_path, registry)

    assert design is not None
    assert any(f.check_id == "DESIGN_APPROVAL_STALE" for f in findings)
    assert not feature_design_lib.design_is_approved(design, tmp_path, registry)


def test_registry_design_edit_makes_approval_stale(tmp_path: Path) -> None:
    registry = write_design(tmp_path, valid_design())
    payload = approve_payload(tmp_path, registry)
    payload["slices"][0]["allowed_files"].append("extra/**")  # type: ignore[index,union-attr]
    registry.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    findings, design = feature_design_lib.validate_design_file(tmp_path, registry)

    assert design is not None
    assert any(f.check_id == "DESIGN_APPROVAL_STALE" for f in findings)
    assert not feature_design_lib.design_is_approved(design, tmp_path, registry)


def test_slice_status_update_does_not_make_approval_stale(tmp_path: Path) -> None:
    registry = write_design(tmp_path, valid_design())
    payload = approve_payload(tmp_path, registry)
    payload["slices"][0]["status"] = "in_progress"  # type: ignore[index]
    registry.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    findings, design = feature_design_lib.validate_design_file(tmp_path, registry)

    assert findings == []
    assert feature_design_lib.design_is_approved(design, tmp_path, registry)


def test_feature_design_rejects_model_self_approval(tmp_path: Path) -> None:
    registry = write_design(
        tmp_path,
        valid_design(
            status="approved",
            approved_by="codex",
            approved_at="2026-07-29",
            approved_markdown_sha256="0" * 64,
            approved_registry_payload_sha256="0" * 64,
        ),
    )

    findings, _ = feature_design_lib.validate_design_file(tmp_path, registry)

    assert any(f.check_id == "DESIGN_SELF_APPROVAL" for f in findings)


def test_feature_design_rejects_missing_approval_provenance(tmp_path: Path) -> None:
    payload = valid_design(status="approved")
    registry = write_design(tmp_path, payload)

    findings, _ = feature_design_lib.validate_design_file(tmp_path, registry)

    assert any(f.check_id == "DESIGN_APPROVAL_MISSING" for f in findings)


def test_feature_design_rejects_duplicate_slice_ids(tmp_path: Path) -> None:
    payload = valid_design()
    payload["slices"] = [payload["slices"][0], dict(payload["slices"][0])]  # type: ignore[index]
    registry = write_design(tmp_path, payload)

    findings, _ = feature_design_lib.validate_design_file(tmp_path, registry)

    assert any(f.check_id == "DESIGN_SLICE_DUPLICATE" for f in findings)


def test_feature_design_rejects_cyclic_slice_dependencies(tmp_path: Path) -> None:
    payload = valid_design()
    payload["slices"] = [
        {
            **payload["slices"][0],  # type: ignore[index]
            "slice_id": "S01",
            "dependencies": ["S02"],
        },
        {
            **payload["slices"][0],  # type: ignore[index]
            "slice_id": "S02",
            "dependencies": ["S01"],
        },
    ]
    registry = write_design(tmp_path, payload)

    findings, _ = feature_design_lib.validate_design_file(tmp_path, registry)

    assert any(f.check_id == "DESIGN_SLICE_CYCLIC_DEPENDENCY" for f in findings)


def test_feature_design_rejects_repo_escape_ref(tmp_path: Path) -> None:
    registry = write_design(tmp_path, valid_design(brief_ref="../PROJECT_BRIEF.md"))

    findings, _ = feature_design_lib.validate_design_file(tmp_path, registry)

    assert any(f.check_id == "DESIGN_REF_UNSAFE" for f in findings)


def test_legacy_slice_verification_string_is_warning(tmp_path: Path) -> None:
    payload = valid_design()
    payload["slices"][0]["verification"] = ["python -m pytest tests/test_smoke.py -q"]  # type: ignore[index]
    registry = write_design(tmp_path, payload)

    findings, _ = feature_design_lib.validate_design_file(tmp_path, registry)

    assert any(f.check_id == "LEGACY_SLICE_VERIFICATION_STRING" and f.severity == "warning" for f in findings)


def test_noninteractive_approval_cli_fails(tmp_path: Path) -> None:
    registry = write_design(tmp_path, valid_design())

    result = approve_feature_design.main(["--root", str(tmp_path), "--feature-id", "F01"])

    assert result == 2
    assert registry.exists()


def test_stop_ship_review_blocks_approval(tmp_path: Path) -> None:
    registry = write_design(tmp_path, valid_design())
    payload = json.loads(registry.read_text(encoding="utf-8"))
    write_design_review_records(tmp_path, payload, program_verdict="STOP_SHIP")

    with pytest.raises(approve_feature_design.ApprovalError, match="STOP_SHIP"):
        approve_feature_design.approve_registry_payload(
            root=tmp_path,
            registry_path=registry,
            payload=json.loads(registry.read_text(encoding="utf-8")),
            human_id="human:tester",
            approval_method="test_harness",
            approval_ref="tests",
            approved_at="2026-07-29",
            review_refs=[{"role": "program_design_review", "path": ".playbook-artifacts/reports/F01/program_design_review.md"}],
            advisory_acknowledgement="",
        )


def test_missing_required_design_review_records_block_approval(tmp_path: Path) -> None:
    registry = write_design(tmp_path, valid_design())

    with pytest.raises(approve_feature_design.ApprovalError, match="missing required design review record"):
        approve_feature_design.approve_registry_payload(
            root=tmp_path,
            registry_path=registry,
            payload=json.loads(registry.read_text(encoding="utf-8")),
            human_id="human:tester",
            approval_method="test_harness",
            approval_ref="tests",
            approved_at="2026-07-29",
            review_refs=[],
            advisory_acknowledgement="",
        )


def test_deleted_required_reviews_projection_does_not_bypass_approval(tmp_path: Path) -> None:
    registry = write_design(tmp_path, valid_design())
    projection = tmp_path / ".playbook-artifacts/workflows/F01/design/required_reviews.json"
    projection.parent.mkdir(parents=True)
    projection.write_text('{"reviews":[]}\n', encoding="utf-8")
    projection.unlink()

    with pytest.raises(approve_feature_design.ApprovalError, match="missing required design review record"):
        approve_feature_design.approve_registry_payload(
            root=tmp_path,
            registry_path=registry,
            payload=json.loads(registry.read_text(encoding="utf-8")),
            human_id="human:tester",
            approval_method="test_harness",
            approval_ref="tests",
            approved_at="2026-07-29",
            review_refs=[],
            advisory_acknowledgement="",
        )


def test_stale_design_review_record_blocks_approval(tmp_path: Path) -> None:
    registry = write_design(tmp_path, valid_design())
    payload = json.loads(registry.read_text(encoding="utf-8"))
    write_design_review_records(tmp_path, payload)
    (tmp_path / "docs/design/F01.md").write_text("# Feature Design\n\nChanged after review.\n", encoding="utf-8")

    with pytest.raises(approve_feature_design.ApprovalError, match="stale"):
        approve_feature_design.approve_registry_payload(
            root=tmp_path,
            registry_path=registry,
            payload=payload,
            human_id="human:tester",
            approval_method="test_harness",
            approval_ref="tests",
            approved_at="2026-07-29",
            review_refs=[],
            advisory_acknowledgement="",
        )


def test_missing_review_marker_blocks_approval(tmp_path: Path) -> None:
    registry = write_design(tmp_path, valid_design())
    payload = json.loads(registry.read_text(encoding="utf-8"))
    write_design_review_records(tmp_path, payload)
    report = tmp_path / ".playbook-artifacts/reports/F01/program_design_review.md"
    report.write_text("No machine marker here.\n", encoding="utf-8")
    record = json.loads((tmp_path / ".playbook-artifacts/reviews/F01/design/program_design_review.review.json").read_text(encoding="utf-8"))
    record["report_sha256"] = feature_design_lib.sha256_file(report)
    (tmp_path / ".playbook-artifacts/reviews/F01/design/program_design_review.review.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(approve_feature_design.ApprovalError, match="missing required marker"):
        approve_feature_design.approve_registry_payload(
            root=tmp_path,
            registry_path=registry,
            payload=payload,
            human_id="human:tester",
            approval_method="test_harness",
            approval_ref="tests",
            approved_at="2026-07-29",
            review_refs=[],
            advisory_acknowledgement="",
        )


def test_advisory_review_requires_acknowledgement(tmp_path: Path) -> None:
    registry = write_design(tmp_path, valid_design())
    payload = json.loads(registry.read_text(encoding="utf-8"))
    write_design_review_records(tmp_path, payload, program_verdict="ADVISORY")

    kwargs = {
        "root": tmp_path,
        "registry_path": registry,
        "payload": json.loads(registry.read_text(encoding="utf-8")),
        "human_id": "human:tester",
        "approval_method": "test_harness",
        "approval_ref": "tests",
        "approved_at": "2026-07-29",
        "review_refs": [{"role": "program_design_review", "path": ".playbook-artifacts/reports/F01/program_design_review.md"}],
    }
    with pytest.raises(approve_feature_design.ApprovalError, match="ADVISORY"):
        approve_feature_design.approve_registry_payload(**kwargs, advisory_acknowledgement="")

    approved = approve_feature_design.approve_registry_payload(
        **kwargs,
        advisory_acknowledgement="human accepts advisory risk for v1",
    )

    assert approved["approved_review_refs"][0]["verdict"] == "ADVISORY"  # type: ignore[index]
    assert approved["advisory_acknowledgement"]


@pytest.mark.parametrize(
    ("kwargs", "expected_depth"),
    [
        ({"risk_level": "low", "task_tags": ["docs"], "expected_file_count": 1}, "oneshot"),
        ({"risk_level": "medium", "expected_file_count": 4, "new_internal_interface": True}, "compact_design"),
        ({"risk_level": "high", "api_change": True, "persistence_change": True}, "designed_slices"),
        ({"rag_or_agentic": True, "expected_large_diff": True}, "designed_slices"),
    ],
)
def test_planning_depth_recommendation_rules(kwargs: dict[str, object], expected_depth: str) -> None:
    recommendation = planning_depth.recommend_planning_depth(**kwargs)

    assert recommendation["recommended_planning_depth"] == expected_depth
    assert recommendation["override_allowed"] is True
    assert isinstance(recommendation["reasons"], list)
