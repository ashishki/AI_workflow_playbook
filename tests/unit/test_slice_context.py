from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def write_feature(root: Path) -> None:
    (root / "docs/design").mkdir(parents=True)
    (root / "docs/PROJECT_BRIEF.md").write_text(
        "# Project Brief\n\n- User-visible outcome: smoke flow\n- Expected system impact: API\n",
        encoding="utf-8",
    )
    (root / "docs/ARCHITECTURE.md").write_text("# Architecture\n\nAPI boundary.\n", encoding="utf-8")
    (root / "docs/design/F01.md").write_text(
        "# Feature Design F01\n\nApproved program design.\n",
        encoding="utf-8",
    )
    (root / "docs/design/F01.design.json").write_text(
        json.dumps(
            {
                "schema_version": "playbook.feature_design.v1",
                "feature_id": "F01",
                "status": "approved",
                "planning_depth": "designed_slices",
                "risk_level": "high",
                "brief_ref": "docs/PROJECT_BRIEF.md",
                "architecture_refs": ["docs/ARCHITECTURE.md"],
                "approval_policy": "human_required",
                "approved_by": "human",
                "approved_at": "2026-07-29",
                "slices": [
                    {
                        "slice_id": "S01",
                        "status": "planned",
                        "user_visible_outcome": "User can run smoke flow.",
                        "scope": "API through tests.",
                        "allowed_files": ["app/**", "tests/**"],
                        "forbidden_files": ["docs/secret.md"],
                        "expected_interfaces": ["create_smoke()"],
                        "verification": ["python -m pytest tests/test_smoke.py -q"],
                        "review_checkpoint": "slice_review",
                        "dependencies": [],
                        "change_budget": "files<=4, lines<=200",
                        "rollback": "revert S01 diff",
                    }
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def write_manifest(root: Path) -> None:
    (root / ".playbook").mkdir()
    (root / "docs/secret.md").write_text("SECRET_TOKEN=do-not-load\n", encoding="utf-8")
    (root / "docs/history.md").write_text("old completed tasks\n", encoding="utf-8")
    (root / ".playbook/instruction_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "playbook.instruction_manifest.v1",
                "artifacts": [
                    {
                        "path": "docs/ARCHITECTURE.md",
                        "authority": "normative",
                        "target_roles": ["implementer", "reviewer"],
                        "stability": "stable",
                        "load_policy": "current_feature",
                        "source_authority": "architecture",
                        "executable_consumer": "render_slice_context",
                    },
                    {
                        "path": "docs/secret.md",
                        "authority": "generated",
                        "target_roles": ["implementer"],
                        "stability": "historical",
                        "load_policy": "never_by_default",
                        "source_authority": "secret",
                        "executable_consumer": "none",
                    },
                    {
                        "path": "docs/history.md",
                        "authority": "reference",
                        "target_roles": ["implementer"],
                        "stability": "historical",
                        "load_policy": "never_by_default",
                        "source_authority": "tasks",
                        "executable_consumer": "none",
                    },
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def test_render_slice_context_includes_current_slice_and_excludes_never_by_default(tmp_path: Path) -> None:
    write_feature(tmp_path)
    write_manifest(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/render_slice_context.py"),
            "--root",
            str(tmp_path),
            "--feature-id",
            "F01",
            "--slice-id",
            "S01",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    output = tmp_path / ".playbook-artifacts/context/F01/S01.md"
    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert "User can run smoke flow." in text
    assert "Approved program design." in text
    assert "docs/ARCHITECTURE.md" in text
    assert "SECRET_TOKEN" not in text
    assert "old completed tasks" not in text


def test_render_slice_context_blocks_unapproved_design(tmp_path: Path) -> None:
    write_feature(tmp_path)
    write_manifest(tmp_path)
    registry = json.loads((tmp_path / "docs/design/F01.design.json").read_text(encoding="utf-8"))
    registry["status"] = "draft"
    registry.pop("approved_by")
    registry.pop("approved_at")
    (tmp_path / "docs/design/F01.design.json").write_text(json.dumps(registry), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/render_slice_context.py"),
            "--root",
            str(tmp_path),
            "--feature-id",
            "F01",
            "--slice-id",
            "S01",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 1
    assert "approved feature design" in result.stderr
