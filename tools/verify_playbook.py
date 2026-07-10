#!/usr/bin/env python3
"""Canonical verification command for AI Workflow Playbook."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class CheckResult:
    check_id: str
    argv: list[str]
    required: bool
    exit_code: int
    stdout_artifact: str
    stderr_artifact: str

    @property
    def passed(self) -> bool:
        return self.exit_code == 0

    def as_dict(self) -> dict[str, object]:
        return {
            "check_id": self.check_id,
            "argv": self.argv,
            "required": self.required,
            "exit_code": self.exit_code,
            "passed": self.passed,
            "stdout_artifact": self.stdout_artifact,
            "stderr_artifact": self.stderr_artifact,
        }


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run_check(
    root: Path,
    output_dir: Path,
    check_id: str,
    argv: list[str],
    *,
    required: bool = True,
    cwd: Path | None = None,
) -> CheckResult:
    stdout_path = output_dir / f"{check_id}.stdout.txt"
    stderr_path = output_dir / f"{check_id}.stderr.txt"
    result = subprocess.run(
        argv,
        cwd=cwd or root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    return CheckResult(
        check_id=check_id,
        argv=argv,
        required=required,
        exit_code=result.returncode,
        stdout_artifact=str(stdout_path),
        stderr_artifact=str(stderr_path),
    )


def generated_project_checks(root: Path, output_dir: Path) -> list[CheckResult]:
    checks: list[CheckResult] = []
    with tempfile.TemporaryDirectory(prefix="playbook-verify-generated-") as tmp:
        tmp_path = Path(tmp)
        for mode in ("lean-core", "standard", "strict"):
            target = tmp_path / mode
            init_cmd = [
                sys.executable,
                "tools/init_playbook_project.py",
                str(target),
                "--mode",
                mode,
                "--project-name",
                f"Verify {mode}",
                "--verify-command",
                f"{sys.executable} tools/verify_project.py --root .",
                "--operational-pain",
                f"Verify {mode} smoke project bootstrap.",
                "--current-workaround",
                "Manual verification of generated artifacts.",
                "--first-proof-metric",
                "Generated project verification exits zero.",
            ]
            if mode == "strict":
                init_cmd.append("--install-claude-hooks")
            checks.append(run_check(root, output_dir, f"initializer_{mode}", init_cmd))
            if checks[-1].exit_code != 0:
                continue
            checks.append(
                run_check(
                    root,
                    output_dir,
                    f"generated_validate_{mode}",
                    [
                        sys.executable,
                        str(root / "tools/playbook_validate.py"),
                        "--root",
                        str(target),
                        "--check",
                        "tasks",
                        "--check",
                        "placeholders",
                    ],
                )
            )
            checks.append(
                run_check(
                    root,
                    output_dir,
                    f"generated_verify_{mode}",
                    [sys.executable, "tools/verify_project.py", "--root", "."],
                    cwd=target,
                )
            )
            if mode == "lean-core":
                unexpected = [
                    "PLAYBOOK.md",
                    "docs/ARCHITECTURE.md",
                    "docs/EVIDENCE_INDEX.md",
                    "docs/ai_cost_architecture.md",
                    "docs/router_eval.md",
                ]
                stdout = ""
                failures = []
                for rel in unexpected:
                    if (target / rel).exists():
                        failures.append(rel)
                stdout = "unexpected_artifacts=" + ",".join(failures) + "\n"
                check_id = "generated_lean_core_artifact_matrix"
                stdout_path = output_dir / f"{check_id}.stdout.txt"
                stderr_path = output_dir / f"{check_id}.stderr.txt"
                stdout_path.write_text(stdout, encoding="utf-8")
                stderr_path.write_text("", encoding="utf-8")
                checks.append(
                    CheckResult(
                        check_id=check_id,
                        argv=["internal", "lean-core-artifact-matrix"],
                        required=True,
                        exit_code=1 if failures else 0,
                        stdout_artifact=str(stdout_path),
                        stderr_artifact=str(stderr_path),
                    )
                )
            if mode == "strict":
                executable = target / "hooks/guard_files.sh"
                stdout_path = output_dir / "generated_strict_hook_install.stdout.txt"
                stderr_path = output_dir / "generated_strict_hook_install.stderr.txt"
                stdout_path.write_text(f"{executable} executable={bool(executable.stat().st_mode & 0o111)}\n", encoding="utf-8")
                stderr_path.write_text("", encoding="utf-8")
                checks.append(
                    CheckResult(
                        check_id="generated_strict_hook_install",
                        argv=["internal", "strict-hook-install"],
                        required=True,
                        exit_code=0 if executable.exists() and executable.stat().st_mode & 0o111 else 1,
                        stdout_artifact=str(stdout_path),
                        stderr_artifact=str(stderr_path),
                    )
                )
    return checks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default=None, help="Verification report path.")
    parser.add_argument("--artifact-dir", default=None, help="Directory for raw verification artifacts.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    artifact_root = Path(args.artifact_dir) if args.artifact_dir else root / ".playbook-artifacts"
    if not artifact_root.is_absolute():
        artifact_root = root / artifact_root
    run_dir = artifact_root / "verification" / utc_stamp()
    run_dir.mkdir(parents=True, exist_ok=True)
    output = Path(args.output) if args.output else artifact_root / "playbook_verification.json"
    if not output.is_absolute():
        output = root / output

    checks: list[CheckResult] = []
    checks.append(
        run_check(
            root,
            run_dir,
            "playbook_validate",
            [
                sys.executable,
                "tools/playbook_validate.py",
                "--root",
                str(root),
                "--json",
                str(artifact_root / "playbook_validation.json"),
            ],
        )
    )
    checks.append(run_check(root, run_dir, "py_compile_tools", [sys.executable, "-m", "py_compile", *[str(path) for path in sorted((root / "tools").glob("*.py"))]]))
    telemetry_adapter = root / "templates/cost_adapters/python/telemetry_adapter.py"
    if telemetry_adapter.exists():
        checks.append(run_check(root, run_dir, "py_compile_templates", [sys.executable, "-m", "py_compile", str(telemetry_adapter)]))
    checks.append(run_check(root, run_dir, "pytest", [sys.executable, "-m", "pytest", "-q"]))
    checks.append(run_check(root, run_dir, "hook_tests", [sys.executable, "-m", "pytest", "tests/hooks", "-q"]))
    checks.extend(generated_project_checks(root, run_dir))
    checks.append(
        run_check(
            root,
            run_dir,
            "evidence_fixture_validation",
            [
                sys.executable,
                "tools/validate_harness_evidence.py",
                "tests/fixtures/evidence/valid_bundle/bundle.json",
                "--json",
                str(artifact_root / "evidence_fixture_validation.json"),
            ],
        )
    )

    required_failures = [check for check in checks if check.required and not check.passed]
    report = {
        "schema_version": "playbook.verify.v1",
        "root": str(root),
        "run_dir": str(run_dir),
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "checks": [check.as_dict() for check in checks],
        "summary": {
            "required": sum(1 for check in checks if check.required),
            "required_failures": len(required_failures),
            "optional_failures": sum(1 for check in checks if not check.required and not check.passed),
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for check in checks:
        status = "PASS" if check.passed else "FAIL"
        requirement = "required" if check.required else "optional"
        print(f"{status}: {check.check_id} ({requirement}) exit={check.exit_code}")
    print(f"verify_playbook: required_failures={len(required_failures)} report={output}")
    return 1 if required_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
