from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def run_init(target: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "tools/init_playbook_project.py"), str(target), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def passing_verify_argv() -> str:
    return json.dumps(["{python}", "-c", "raise SystemExit(0)"])


def init_workflow(target: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run_init(
        target, "--operational-pain", "Bootstrap must produce a usable workflow.",
        "--current-workaround", "Repair missing operating instructions manually.",
        "--first-proof-metric", "The generated verifier detects broken workflow wiring.",
        "--verify-argv", passing_verify_argv(), *args,
    )


@pytest.mark.parametrize("mode", ["lean-core", "lean", "standard", "strict"])
def test_mode_entrypoint_is_consistent_with_and_without_force(tmp_path: Path, mode: str) -> None:
    target = tmp_path / mode
    result = init_workflow(target, "--mode", mode)
    assert result.returncode == 0, result.stderr
    agents = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert f"Mode: {'lean-core' if mode == 'lean' else mode}" in agents
    contract = "CONTRACT_LITE" if mode in {"lean", "lean-core"} else "IMPLEMENTATION_CONTRACT"
    assert f"docs/{contract}.md" in agents
    forced = init_workflow(target, "--mode", mode, "--force")
    assert forced.returncode == 0, forced.stderr
    assert (target / "AGENTS.md").read_text(encoding="utf-8") == agents
    assert sum(line.endswith("/AGENTS.md") for line in forced.stdout.splitlines()) == 1


@pytest.mark.parametrize("mode", ["standard", "strict"])
@pytest.mark.parametrize("profile", ["solo_verified", "independent_review"])
def test_generated_operating_contract_is_usable(tmp_path: Path, mode: str, profile: str) -> None:
    target = tmp_path / mode
    args = [] if profile == "solo_verified" else [
        "--delivery-profile", profile, "--agent-model", "example-main-model",
        "--agent-reasoning-effort", "high", "--review-model", "example-review-model",
        "--review-reasoning-effort", "medium",
    ]
    result = init_workflow(target, "--mode", mode, *args)
    assert result.returncode == 0, result.stderr
    assert "scaffold" in result.stdout
    assert (target / "AGENTS.md").is_file()
    assert (target / "docs/REVIEW_POLICY.md").is_file()
    assert (target / "docs/merge_authority.md").is_file()
    assert (target / "docs/codex_exec_subagent_protocol.md").is_file()
    handoff = (target / "docs/CODEX_PROMPT.md").read_text(encoding="utf-8")
    assert len(handoff.splitlines()) < 100
    assert "T01: Complete Project Brief And Mode Selection" in handoff
    assert "IMPLEMENTATION_JOURNAL.md" in handoff
    for heading in (
        "Current State", "Next Task", "Fix Queue", "Open Findings", "Continuity Pointers",
        "Instructions for Codex", "RAG State", "Tool-Use State", "Agentic State",
        "Planning State", "Compliance State", "Evaluation State", "NFR Baseline",
    ):
        assert f"## {heading}\n" in handoff
    assert "Version:" in handoff and "Phase: 1" in handoff and "Baseline:" in handoff
    assert "Eval Source:" in handoff and "Date:" in handoff
    assert "Never delete history from this file" not in handoff
    contract = json.loads((target / ".playbook/delivery_execution_model.json").read_text())
    assert contract["delivery_profile"] == profile
    assert contract["operating_policy_ref"] == "docs/REVIEW_POLICY.md"
    assert contract["completion_authority"]["kind"] == "human"
    if profile == "independent_review":
        assert contract["task_loop_profile"] == "codex_exec_subagents"
        assert contract["orchestrator"]["kind"] == contract["implementer"]["kind"] == "active_codex_session"
        assert contract["orchestrator"]["model"] == "example-main-model"
        assert contract["implementer"]["reasoning_effort"] == "high"
        assert contract["reviewer"]["model"] == "example-review-model"
        assert contract["reviewer"]["reasoning_effort"] == "medium"
        assert contract["reviewer"]["may_write_code"] is False
    else:
        assert contract["task_loop_profile"] == "disabled"
        assert contract["orchestrator"]["kind"] == "human"
        assert "model" not in contract["implementer"]
    verification = subprocess.run(
        [sys.executable, "tools/verify_project.py", "--root", "."], cwd=target,
        capture_output=True, text=True, check=False,
    )
    assert verification.returncode == 0, verification.stdout + verification.stderr


@pytest.mark.parametrize("missing", [
    "AGENTS.md", "docs/REVIEW_POLICY.md", "docs/merge_authority.md",
    "docs/CODEX_PROMPT.md", "tools/run_codex_role.py", "tools/codex_role_run_lib.py",
])
def test_generated_verifier_rejects_broken_operating_contract(tmp_path: Path, missing: str) -> None:
    target = tmp_path / "broken"
    result = init_workflow(target, "--delivery-profile", "independent_review")
    assert result.returncode == 0, result.stderr
    (target / missing).unlink()
    verification = subprocess.run(
        [sys.executable, "tools/verify_project.py", "--root", "."], cwd=target,
        capture_output=True, text=True, check=False,
    )
    assert verification.returncode == 1
    report = json.loads((target / ".playbook-artifacts/project_verification.json").read_text())
    check = next(item for item in report["checks"] if item["id"] == "playbook_contract")
    output = (target / check["stdout_ref"]["path"]).read_text() + (target / check["stderr_ref"]["path"]).read_text()
    assert "DELIVERY_OPERATING_ARTIFACT_MISSING" in output
    assert missing in output


@pytest.mark.parametrize("drift", ["reviewer_writes", "human_orchestrator", "profile_disabled", "reviewer_approves"])
def test_delivery_validation_detects_selected_workflow_drift(tmp_path: Path, drift: str) -> None:
    target = tmp_path / "drift"
    result = init_workflow(target, "--delivery-profile", "independent_review")
    assert result.returncode == 0, result.stderr
    path = target / ".playbook/delivery_execution_model.json"
    contract = json.loads(path.read_text())
    if drift == "reviewer_writes":
        contract["reviewer"]["may_write_code"] = True
    elif drift == "human_orchestrator":
        contract["orchestrator"]["kind"] = "human"
    elif drift == "reviewer_approves":
        contract["completion_authority"]["kind"] = "independent_read_only_agent"
    else:
        contract["task_loop_profile"] = "disabled"
    path.write_text(json.dumps(contract), encoding="utf-8")
    validation = subprocess.run(
        [sys.executable, "tools/playbook_validate.py", "--root", ".", "--check", "delivery"],
        cwd=target, capture_output=True, text=True, check=False,
    )
    assert validation.returncode == 1
    assert "DELIVERY_OPERATING_PROFILE_MISMATCH" in validation.stdout + validation.stderr


def test_lean_rejects_task_loop_profile_before_writing(tmp_path: Path) -> None:
    target = tmp_path / "lean"
    result = init_workflow(target, "--mode", "lean", "--delivery-profile", "independent_review")
    assert result.returncode == 2
    assert "requires --mode standard or strict" in result.stderr
    assert not target.exists()


def test_workflow_retrofit_preserves_owned_files_and_dry_run_writes_nothing(tmp_path: Path) -> None:
    dry_target = tmp_path / "dry"
    dry = init_workflow(dry_target, "--delivery-profile", "independent_review", "--dry-run")
    assert dry.returncode == 0, dry.stderr
    assert not dry_target.exists()
    target = tmp_path / "existing"
    owned = ["AGENTS.md", "docs/REVIEW_POLICY.md", "docs/CODEX_PROMPT.md", "docs/PROJECT_BRIEF.md"]
    for ref in owned:
        path = target / ref
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"Existing project-owned content: {ref}\n", encoding="utf-8")
    result = init_workflow(target, "--retrofit")
    assert result.returncode == 0, result.stderr
    for ref in owned:
        assert (target / ref).read_text(encoding="utf-8") == f"Existing project-owned content: {ref}\n"
        assert f"skip existing: {target / ref}" in result.stdout


def test_lean_core_is_minimal_and_valid(tmp_path: Path) -> None:
    target = tmp_path / "lean-core"
    result = run_init(
        target,
        "--mode",
        "lean-core",
        "--project-name",
        "Lean Smoke",
        "--operational-pain",
        "Agents need a small verified project scaffold.",
        "--current-workaround",
        "Manual copying of playbook files.",
        "--first-proof-metric",
        "Generated project verifier exits zero.",
        "--verify-argv",
        passing_verify_argv(),
    )

    assert result.returncode == 0, result.stderr
    assert (target / "AGENTS.md").exists()
    assert (target / "docs/tasks.md").exists()
    assert (target / "docs/CONTRACT_LITE.md").exists()
    assert (target / "docs/PROBLEM_FIT.md").exists()
    assert (target / "tools/verify_project.py").exists()
    assert (target / "tools/resolve_release_readiness.py").exists()
    assert (target / ".playbook/project_verification.json").exists()
    assert not (target / "PLAYBOOK.md").exists()
    assert not (target / "docs/ARCHITECTURE.md").exists()
    assert not (target / "docs/EVIDENCE_INDEX.md").exists()
    assert not (target / "docs/ai_cost_architecture.md").exists()
    assert not (target / "docs/design/F01.md").exists()

    validation = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/playbook_validate.py"),
            "--root",
            str(target),
            "--check",
            "tasks",
            "--check",
            "placeholders",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert validation.returncode == 0, validation.stderr
    verification = subprocess.run(
        [sys.executable, "tools/verify_project.py", "--root", "."],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert verification.returncode == 0, verification.stderr
    result_path = target / ".playbook-artifacts/project_verification.json"
    assert result_path.exists()
    verification_result = json.loads(result_path.read_text(encoding="utf-8"))
    assert verification_result["required_failures"] == 0
    assert {check["id"] for check in verification_result["checks"]} == {
        "playbook_contract",
        "project_verification",
    }
    release = subprocess.run(
        [sys.executable, "tools/resolve_release_readiness.py", "--root", "."],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert release.returncode == 1
    assert "READINESS_RELEASE_GIT_REQUIRED" in release.stderr


def test_standard_compact_design_creates_draft_and_design_required_state(tmp_path: Path) -> None:
    target = tmp_path / "standard-compact"
    result = run_init(
        target,
        "--mode",
        "standard",
        "--project-name",
        "Standard Compact",
        "--operational-pain",
        "Medium-risk workflow changes need a design checkpoint.",
        "--current-workaround",
        "Reviewers infer file scope from large diffs.",
        "--first-proof-metric",
        "Draft design blocks implementation readiness until approved.",
        "--verify-argv",
        passing_verify_argv(),
        "--planning-depth",
        "compact_design",
    )

    assert result.returncode == 0, result.stderr
    assert "feature_workflow.py --root . plan --task <task-id>" in result.stdout
    assert "select-plan" in result.stdout
    assert (target / "docs/design/F01.md").exists()
    assert (target / "tools/feature_workflow.py").exists()
    assert (target / "tools/approve_feature_design.py").exists()
    assert (target / "tools/feature_review_policy.py").exists()
    assert (target / "tools/receipt_run.py").exists()
    registry = json.loads((target / "docs/design/F01.design.json").read_text(encoding="utf-8"))
    assert registry["status"] == "draft"
    assert registry["planning_depth"] == "compact_design"
    readiness = json.loads((target / ".playbook/readiness_state.json").read_text(encoding="utf-8"))
    assert readiness["state"] == "design_required"
    assert readiness["planning_depth"] == "compact_design"
    assert readiness["required_design_refs"] == ["docs/design/F01.design.json"]

    validation = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/playbook_validate.py"),
            "--root",
            str(target),
            "--check",
            "readiness",
            "--check",
            "design",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert validation.returncode == 0, validation.stderr

    readiness["state"] = "implementation_ready"
    (target / ".playbook/readiness_state.json").write_text(json.dumps(readiness), encoding="utf-8")
    blocked = subprocess.run(
        [sys.executable, str(ROOT / "tools/playbook_validate.py"), "--root", str(target), "--check", "readiness"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert blocked.returncode == 1
    assert "READINESS_DESIGN_APPROVAL_REQUIRED" in blocked.stderr


def test_strict_designed_slices_requires_human_design_approval(tmp_path: Path) -> None:
    target = tmp_path / "strict-designed"
    result = run_init(
        target,
        "--mode",
        "strict",
        "--project-name",
        "Strict Designed",
        "--operational-pain",
        "High-risk multi-layer features need slice-level review.",
        "--current-workaround",
        "Large diffs are reviewed after the architecture is already encoded.",
        "--first-proof-metric",
        "Slice context can be generated from an approved design.",
        "--verify-argv",
        passing_verify_argv(),
        "--planning-depth",
        "designed_slices",
        "--risk-level",
        "high",
    )

    assert result.returncode == 0, result.stderr
    registry = json.loads((target / "docs/design/F01.design.json").read_text(encoding="utf-8"))
    assert registry["approval_policy"] == "human_required"
    readiness = json.loads((target / ".playbook/readiness_state.json").read_text(encoding="utf-8"))
    assert readiness["design_approval_required"] == "human_required"
    assert readiness["state"] == "design_required"


def test_retrofit_preserves_existing_agents_and_writes_inventory_and_plan(tmp_path: Path) -> None:
    target = tmp_path / "retrofit"
    target.mkdir()
    (target / "AGENTS.md").write_text("existing agent rules\n", encoding="utf-8")
    (target / "app.py").write_text("print('app')\n", encoding="utf-8")

    result = run_init(
        target,
        "--retrofit",
        "--mode",
        "standard",
        "--project-name",
        "Retrofit",
        "--operational-pain",
        "Existing repo needs planning checkpoints without rewriting app code.",
        "--current-workaround",
        "Manual architectural review after implementation.",
        "--first-proof-metric",
        "Initializer writes design scaffold and next steps only.",
        "--verify-argv",
        passing_verify_argv(),
        "--planning-depth",
        "recommend",
        "--risk-level",
        "high",
        "--user-visible-feature",
    )

    assert result.returncode == 0, result.stderr
    assert (target / "AGENTS.md").read_text(encoding="utf-8") == "existing agent rules\n"
    assert (target / "app.py").read_text(encoding="utf-8") == "print('app')\n"
    assert (target / ".playbook/repository_inventory.json").exists()
    inventory = json.loads((target / ".playbook/repository_inventory.json").read_text(encoding="utf-8"))
    assert "app.py" in inventory["sample_files"]
    assert (target / "docs/playbook_retrofit_plan.md").exists()
    assert (target / "docs/design/F01.design.json").exists()
    readiness = json.loads((target / ".playbook/readiness_state.json").read_text(encoding="utf-8"))
    assert readiness["planning_depth"] == "designed_slices"
    assert readiness["planning_depth_source"] == "recommended"


def test_standard_with_rag_eval_creates_valid_portable_kit(tmp_path: Path) -> None:
    target = tmp_path / "standard-rag"
    result = run_init(
        target,
        "--mode",
        "standard",
        "--project-name",
        "Standard RAG",
        "--operational-pain",
        "RAG changes need deterministic eval evidence.",
        "--current-workaround",
        "Manual retrieval spot checks.",
        "--first-proof-metric",
        "RAG eval scaffold validates and scores offline.",
        "--verify-argv",
        passing_verify_argv(),
        "--with-rag-eval",
    )

    assert result.returncode == 0, result.stderr
    assert (target / ".playbook/rag_eval_manifest.json").exists()
    assert (target / ".playbook/rag_eval_cases.jsonl").exists()
    assert (target / "tools/rag_eval_score.py").exists()
    assert (target / "schemas/rag_eval_manifest.schema.json").exists()
    assert (target / "docs/rag_data_readiness.md").exists()
    assert (target / "docs/retrieval_eval.md").exists()
    config = json.loads((target / ".playbook/project_verification.json").read_text(encoding="utf-8"))
    assert "rag_eval_contract" in {check["id"] for check in config["checks"]}

    validation = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/playbook_validate.py"),
            "--root",
            str(target),
            "--check",
            "rag",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert validation.returncode == 0, validation.stderr

    baseline = subprocess.run(
        [
            sys.executable,
            "tools/rag_eval_score.py",
            "--root",
            ".",
            "--manifest",
            ".playbook/rag_eval_manifest.json",
            "--observations",
            ".playbook/rag_eval_baseline_observations.jsonl",
            "--condition",
            "lexical_baseline",
            "--json",
            ".playbook-artifacts/rag-eval/baseline.json",
        ],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert baseline.returncode == 0, baseline.stderr

    candidate = subprocess.run(
        [
            sys.executable,
            "tools/rag_eval_score.py",
            "--root",
            ".",
            "--manifest",
            ".playbook/rag_eval_manifest.json",
            "--observations",
            ".playbook/rag_eval_candidate_observations.jsonl",
            "--condition",
            "production_candidate",
            "--json",
            ".playbook-artifacts/rag-eval/candidate.json",
        ],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert candidate.returncode == 0, candidate.stderr

    comparison = subprocess.run(
        [
            sys.executable,
            "tools/rag_eval_compare.py",
            "--root",
            ".",
            "--baseline",
            ".playbook-artifacts/rag-eval/baseline.json",
            "--candidate",
            ".playbook-artifacts/rag-eval/candidate.json",
            "--manifest",
            ".playbook/rag_eval_manifest.json",
            "--json",
            ".playbook-artifacts/rag-eval/comparison.json",
            "--report",
            "reports/rag_eval/comparison.md",
        ],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert comparison.returncode == 0, comparison.stderr
    assert json.loads((target / ".playbook-artifacts/rag-eval/comparison.json").read_text(encoding="utf-8"))["status"] == "pass"


def test_strict_with_rag_eval_verifier_passes(tmp_path: Path) -> None:
    target = tmp_path / "strict-rag"
    result = run_init(
        target,
        "--mode",
        "strict",
        "--project-name",
        "Strict RAG",
        "--operational-pain",
        "Strict RAG projects need machine eval provenance.",
        "--current-workaround",
        "Manual release checklist.",
        "--first-proof-metric",
        "Generated project verifier includes RAG contract.",
        "--verify-argv",
        passing_verify_argv(),
        "--with-rag-eval",
    )

    assert result.returncode == 0, result.stderr
    verification = subprocess.run(
        [sys.executable, "tools/verify_project.py", "--root", "."],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert verification.returncode == 0, verification.stderr
    result_path = target / ".playbook-artifacts/project_verification.json"
    executed = json.loads(result_path.read_text(encoding="utf-8"))
    assert "rag_eval_contract" in {check["id"] for check in executed["checks"]}


def test_lean_core_with_rag_eval_remains_proportional(tmp_path: Path) -> None:
    target = tmp_path / "lean-rag"
    result = run_init(
        target,
        "--mode",
        "lean-core",
        "--project-name",
        "Lean RAG",
        "--operational-pain",
        "Lean project needs only RAG eval smoke artifacts.",
        "--current-workaround",
        "Manual spot checks.",
        "--first-proof-metric",
        "RAG manifest validates offline.",
        "--verify-argv",
        passing_verify_argv(),
        "--with-rag-eval",
    )

    assert result.returncode == 0, result.stderr
    assert not (target / "PLAYBOOK.md").exists()
    assert not (target / "docs/ARCHITECTURE.md").exists()
    assert (target / ".playbook/rag_eval_manifest.json").exists()
    assert (target / "tools/rag_eval_validate.py").exists()


def test_rag_eval_dry_run_does_not_write(tmp_path: Path) -> None:
    target = tmp_path / "dry-run-rag"
    result = run_init(
        target,
        "--mode",
        "standard",
        "--project-name",
        "Dry Run RAG",
        "--operational-pain",
        "Dry-run should show outputs without writing.",
        "--current-workaround",
        "Manual planning.",
        "--first-proof-metric",
        "Target directory remains absent.",
        "--verify-argv",
        passing_verify_argv(),
        "--with-rag-eval",
        "--dry-run",
    )

    assert result.returncode == 0, result.stderr
    assert not target.exists()
    assert ".playbook/rag_eval_manifest.json" in result.stdout


def test_rag_eval_force_overwrites_invalid_manifest(tmp_path: Path) -> None:
    target = tmp_path / "force-rag"
    first = run_init(
        target,
        "--mode",
        "standard",
        "--project-name",
        "Force RAG",
        "--operational-pain",
        "Force should repair stale scaffold files.",
        "--current-workaround",
        "Manual overwrite.",
        "--first-proof-metric",
        "Manifest validates after force.",
        "--verify-argv",
        passing_verify_argv(),
        "--with-rag-eval",
    )
    assert first.returncode == 0, first.stderr
    (target / ".playbook/rag_eval_manifest.json").write_text("{bad json\n", encoding="utf-8")

    second = run_init(
        target,
        "--mode",
        "standard",
        "--project-name",
        "Force RAG",
        "--operational-pain",
        "Force should repair stale scaffold files.",
        "--current-workaround",
        "Manual overwrite.",
        "--first-proof-metric",
        "Manifest validates after force.",
        "--verify-argv",
        passing_verify_argv(),
        "--with-rag-eval",
        "--force",
    )

    assert second.returncode == 0, second.stderr
    validation = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/playbook_validate.py"),
            "--root",
            str(target),
            "--check",
            "rag",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert validation.returncode == 0, validation.stderr


def test_install_claude_hooks_merges_settings(tmp_path: Path) -> None:
    target = tmp_path / "standard"
    settings_path = target / ".claude/settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps({"permissions": {"allow": ["Bash(git status:*)"]}}, indent=2),
        encoding="utf-8",
    )

    result = run_init(
        target,
        "--mode",
        "standard",
        "--project-name",
        "Hook Smoke",
        "--operational-pain",
        "Hook installation must preserve user settings.",
        "--current-workaround",
        "Manual hook copying.",
        "--first-proof-metric",
        "Hook smoke test passes.",
        "--verify-argv",
        passing_verify_argv(),
        "--install-claude-hooks",
    )

    assert result.returncode == 0, result.stderr
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert settings["permissions"]["allow"] == ["Bash(git status:*)"]
    assert "hooks" in settings
    assert (target / "hooks/guard_files.sh").exists()
    assert (target / "hooks/guard_files.sh").stat().st_mode & 0o111
    assert "hook smoke test passed" in result.stdout
    workflow = (target / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "permissions:\n  contents: read" in workflow
    assert "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0" in workflow
    assert "persist-credentials: false" in workflow
    assert "python -m pip install pytest" not in workflow


def test_initializer_rejects_unknown_readiness_values(tmp_path: Path) -> None:
    target = tmp_path / "bad-readiness"
    result = run_init(
        target,
        "--mode",
        "lean-core",
        "--project-name",
        "Bad Readiness",
        "--operational-pain",
        "unknown",
        "--current-workaround",
        "Manual process.",
        "--first-proof-metric",
        "Verifier exits zero.",
        "--verify-argv",
        passing_verify_argv(),
    )

    assert result.returncode == 2
    assert "--operational-pain is required" in result.stderr


def test_initializer_rejects_legacy_shell_verify_command_without_argv(tmp_path: Path) -> None:
    target = tmp_path / "legacy-shell"
    result = run_init(
        target,
        "--mode",
        "lean-core",
        "--project-name",
        "Legacy Shell",
        "--operational-pain",
        "Project verification must be executable without shell parsing.",
        "--current-workaround",
        "Manual command review.",
        "--first-proof-metric",
        "Initializer rejects unsafe verification input.",
        "--verify-command",
        "pytest -q",
    )

    assert result.returncode == 2
    assert "--verify-command is not enforced" in result.stderr


def test_generated_verifier_fails_when_project_verification_fails(tmp_path: Path) -> None:
    target = tmp_path / "failing-project"
    result = run_init(
        target,
        "--mode",
        "lean-core",
        "--project-name",
        "Failing Project",
        "--operational-pain",
        "Project tests must be part of completion evidence.",
        "--current-workaround",
        "Manual pytest inspection.",
        "--first-proof-metric",
        "Generated verifier exits non-zero when pytest fails.",
        "--verify-argv",
        json.dumps([sys.executable, "-m", "pytest", "-q"]),
    )
    assert result.returncode == 0, result.stderr
    tests_dir = target / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_fail.py").write_text("def test_fails():\n    assert False\n", encoding="utf-8")

    verification = subprocess.run(
        [sys.executable, "tools/verify_project.py", "--root", "."],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert verification.returncode == 1
    result_path = target / ".playbook-artifacts/project_verification.json"
    verification_result = json.loads(result_path.read_text(encoding="utf-8"))
    assert verification_result["required_failures"] == 1
    project_check = next(check for check in verification_result["checks"] if check["id"] == "project_verification")
    assert project_check["passed"] is False
    assert project_check["exit_code"] == 1


def test_generated_verifier_rejects_recursive_project_verification(tmp_path: Path) -> None:
    target = tmp_path / "recursive-project"
    result = run_init(
        target,
        "--mode",
        "lean-core",
        "--project-name",
        "Recursive Project",
        "--operational-pain",
        "Self-referential verification must fail closed.",
        "--current-workaround",
        "Manual config inspection.",
        "--first-proof-metric",
        "Generated verifier rejects recursive checks.",
        "--verify-argv",
        json.dumps(["{python}", "tools/verify_project.py", "--root", "."]),
    )
    assert result.returncode == 0, result.stderr

    verification = subprocess.run(
        [sys.executable, "tools/verify_project.py", "--root", "."],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert verification.returncode == 2
    assert "must not call tools/verify_project.py recursively" in verification.stderr


def test_required_platform_skip_fails_project_verification(tmp_path: Path) -> None:
    target = tmp_path / "platform-skip"
    result = run_init(
        target,
        "--mode",
        "lean-core",
        "--project-name",
        "Platform Skip",
        "--operational-pain",
        "Required checks must not disappear on unsupported platforms.",
        "--current-workaround",
        "Manual platform review.",
        "--first-proof-metric",
        "Generated verifier blocks skipped required checks.",
        "--verify-argv",
        passing_verify_argv(),
    )
    assert result.returncode == 0, result.stderr
    config_path = target / ".playbook/project_verification.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["checks"][1]["platforms"] = ["definitely-not-this-platform"]
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    verification = subprocess.run(
        [sys.executable, "tools/verify_project.py", "--root", "."],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert verification.returncode == 1
    result_payload = json.loads((target / ".playbook-artifacts/project_verification.json").read_text(encoding="utf-8"))
    skipped = next(check for check in result_payload["checks"] if check["id"] == "project_verification")
    assert skipped["skipped"] is True
    assert skipped["passed"] is False
    assert result_payload["required_failures"] == 1
