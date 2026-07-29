from __future__ import annotations

import json
from pathlib import Path

import pytest

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
        "status": "approved",
        "planning_depth": "designed_slices",
        "risk_level": "high",
        "brief_ref": "docs/PROJECT_BRIEF.md",
        "architecture_refs": [],
        "approval_policy": "human_required",
        "approved_by": "human",
        "approved_at": "2026-07-29",
        "slices": [
            {
                "slice_id": "S01",
                "status": "implemented",
                "user_visible_outcome": "User can run a bounded smoke path.",
                "scope": "Smoke path through contract and validator.",
                "allowed_files": ["app/**", "tests/**"],
                "forbidden_files": ["secrets/**"],
                "expected_interfaces": ["run_smoke()"],
                "verification": ["python -m pytest tests/test_smoke.py -q"],
                "review_checkpoint": "closed",
                "dependencies": [],
                "change_budget": "files<=4, lines<=200",
                "rollback": "revert slice diff",
            }
        ],
    }
    payload.update(overrides)
    return payload


def test_feature_design_accepts_valid_approved_human_design(tmp_path: Path) -> None:
    registry = write_design(tmp_path, valid_design())

    findings, design = feature_design_lib.validate_design_file(tmp_path, registry)

    assert findings == []
    assert design is not None
    assert design["feature_id"] == "F01"


def test_feature_design_rejects_model_self_approval(tmp_path: Path) -> None:
    registry = write_design(tmp_path, valid_design(approved_by="codex"))

    findings, _ = feature_design_lib.validate_design_file(tmp_path, registry)

    assert any(f.check_id == "DESIGN_SELF_APPROVAL" for f in findings)


def test_feature_design_rejects_missing_approval_provenance(tmp_path: Path) -> None:
    payload = valid_design()
    payload.pop("approved_by")
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
