from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import build_test_first_pilot_manifest


SUITE = ROOT / "companion/ai_workflow_harness_lab/suites/shishki_bot_ci_v1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def task_facts(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return text.split("## Task Facts\n", 1)[1].split("\n## Condition Workflow", 1)[0]


def test_frozen_prompts_have_identical_task_facts_without_gold_refs() -> None:
    accepted_commits = {
        "5f9adb4f7421c7cc03e74c8dd30c127f3ecfd31d",
        "798bb0ed68f7dacdf7e6f697381b7a3222949d74",
    }
    for task in ("pin_ci_actions", "reject_unapproved_ci_actions"):
        baseline = SUITE / f"prompts/{task}.baseline.md"
        playbook = SUITE / f"prompts/{task}.playbook.md"
        assert task_facts(baseline) == task_facts(playbook)
        for path in (baseline, playbook):
            text = path.read_text(encoding="utf-8")
            assert "github.com" not in text.lower()
            assert not accepted_commits.intersection(text.split())


def test_sparse_fixtures_match_frozen_source_files_and_path_boundary() -> None:
    expected_hashes = {
        "fixtures/pin_ci_actions/.github/workflows/ci.yml":
            "2812ae94c9ccd2e73900baa62610fba54b6269122d40925e071d902da8cc1bc4",
        "fixtures/reject_unapproved_ci_actions/.github/workflows/ci.yml":
            "5a0e83cc77c460093ea59e51979cef2e042e87fe938f2056bb194d6e1df11aba",
        "fixtures/reject_unapproved_ci_actions/tests/test_ci_supply_chain.py":
            "d7fc19e73e58422ad069ad56cb42bfc3263da6b4de36e076f2771e981af9a654",
    }
    allowed = {
        "fixtures/pin_ci_actions/.gitignore",
        "fixtures/pin_ci_actions/.github/workflows/ci.yml",
        "fixtures/pin_ci_actions/pilot_tests/test_ci_pins.py",
        "fixtures/reject_unapproved_ci_actions/.gitignore",
        "fixtures/reject_unapproved_ci_actions/.github/workflows/ci.yml",
        "fixtures/reject_unapproved_ci_actions/tests/test_ci_supply_chain.py",
        "fixtures/reject_unapproved_ci_actions/pilot_tests/test_unapproved_action.py",
    }
    observed = {
        str(path.relative_to(SUITE))
        for fixture in (SUITE / "fixtures").iterdir()
        for path in fixture.rglob("*")
        if path.is_file() and not any(part in {"__pycache__", ".pytest_cache"} for part in path.parts)
    }
    assert observed == allowed
    for relative, expected in expected_hashes.items():
        assert sha256(SUITE / relative) == expected


def test_each_staged_fixture_starts_with_the_declared_red_result() -> None:
    commands = {
        "pin_ci_actions": ["pilot_tests/test_ci_pins.py"],
        "reject_unapproved_ci_actions": [
            "tests/test_ci_supply_chain.py",
            "pilot_tests/test_unapproved_action.py",
        ],
    }
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    for task, tests in commands.items():
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *tests],
            cwd=SUITE / "fixtures" / task,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        assert result.returncode == 1, result.stdout
        assert "1 failed" in result.stdout


def test_counterbalanced_schedule_has_twelve_calls_and_balanced_first_arms() -> None:
    runner = (ROOT / "tools/run_test_first_pilot.sh").read_text(encoding="utf-8")
    calls = re.findall(
        r"^run_one (pin_ci_actions|reject_unapproved_ci_actions) ([0-2]) (baseline|playbook)$",
        runner,
        re.MULTILINE,
    )
    assert len(calls) == 12
    assert len(set(calls)) == 12
    for task in ("pin_ci_actions", "reject_unapproved_ci_actions"):
        for trial in ("0", "1", "2"):
            assert {arm for candidate, index, arm in calls if (candidate, index) == (task, trial)} == {
                "baseline",
                "playbook",
            }
    first_arms = [calls[index][2] for index in range(0, len(calls), 2)]
    assert first_arms.count("baseline") == first_arms.count("playbook") == 3
    assert 'RUN_SEAL="$ROOT/tools/test_first_pilot_run_seal.py"' in runner
    assert '"$PYTHON" "${PYTHON_FLAGS[@]}" "$RUN_SEAL" write "$RUN_ROOT"' in runner
    assert '"$ROOT/tests/unit/test_test_first_pilot_run_seal.py" \\' in runner


def test_event_schema_accepts_adapter_events() -> None:
    schema = json.loads(
        (ROOT / "schemas/test_first_pilot_event.schema.json").read_text(encoding="utf-8")
    )
    base = {
        "schema_version": "test_first_pilot.event.v1",
        "pilot_manifest_sha256": "a" * 64,
        "approval_id": "approval-1",
        "pilot_id": "pilot-1",
        "attempt_id": "pilot-1.pin-ci.baseline.0",
        "task_id": "pin_ci_actions",
        "condition": "baseline",
        "trial": 0,
        "model": "gpt-5.6-sol",
        "reasoning_effort": "medium",
        "service_tier": "default",
        "timestamp": "2026-07-14T00:00:00Z",
        "monotonic_ns": 0,
    }
    jsonschema.validate({**base, "event": "adapter_start"}, schema)
    jsonschema.validate(
        {
            **base,
            "event": "adapter_end",
            "codex_exit_code": 0,
            "wrapper_exit_code": 0,
            "terminal_class": "completed",
            "timed_out": False,
        },
        schema,
    )
    without_monotonic = {**base, "event": "adapter_start"}
    without_monotonic.pop("monotonic_ns")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(without_monotonic, schema)


def test_frozen_asset_manifest_matches_full_execution_closure() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/build_test_first_pilot_manifest.py"), "--check"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_asset_manifest_rejects_symlinks_in_execution_trees(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tree = tmp_path / "tree"
    tree.mkdir()
    target = tmp_path / "outside.py"
    target.write_text("raise RuntimeError('must not execute')\n", encoding="utf-8")
    (tree / "conftest.py").symlink_to(target)

    monkeypatch.setattr(build_test_first_pilot_manifest, "ROOT", tmp_path)
    monkeypatch.setattr(build_test_first_pilot_manifest, "EXACT_PATHS", set())
    monkeypatch.setattr(build_test_first_pilot_manifest, "TREE_ROOTS", ("tree",))

    with pytest.raises(RuntimeError, match="symbolic link is not allowed"):
        build_test_first_pilot_manifest.asset_paths()


def test_asset_manifest_rejects_symlinked_exact_path_ancestor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = tmp_path / "real"
    real.mkdir()
    (real / "asset.txt").write_text("frozen\n", encoding="utf-8")
    (tmp_path / "linked").symlink_to(real, target_is_directory=True)
    tree = tmp_path / "tree"
    tree.mkdir()

    monkeypatch.setattr(build_test_first_pilot_manifest, "ROOT", tmp_path)
    monkeypatch.setattr(
        build_test_first_pilot_manifest, "EXACT_PATHS", {"linked/asset.txt"}
    )
    monkeypatch.setattr(build_test_first_pilot_manifest, "TREE_ROOTS", ("tree",))

    with pytest.raises(RuntimeError, match="symbolic link is not allowed"):
        build_test_first_pilot_manifest.asset_paths()
