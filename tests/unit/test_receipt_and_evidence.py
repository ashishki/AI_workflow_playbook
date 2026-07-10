from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALID_BUNDLE = ROOT / "tests/fixtures/evidence/valid_bundle"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_hash(bundle: dict[str, object]) -> str:
    cloned = dict(bundle)
    cloned["manifest_hash"] = ""
    payload = json.dumps(cloned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def rewrite_bundle(bundle_path: Path, bundle: dict[str, object]) -> None:
    bundle["manifest_hash"] = manifest_hash(bundle)
    bundle_path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def refresh_receipt_ref(bundle_dir: Path) -> None:
    bundle_path = bundle_dir / "bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    receipt_path = bundle_dir / "receipts/smoke/receipt.json"
    bundle["command_receipts"][0]["sha256"] = sha(receipt_path)
    rewrite_bundle(bundle_path, bundle)


def run_receipt(output_dir: Path, *command: str, timeout: str | None = None) -> subprocess.CompletedProcess[str]:
    args = [
        sys.executable,
        str(ROOT / "tools/receipt_run.py"),
        "--task-id",
        "T01",
        "--output-dir",
        str(output_dir),
    ]
    if timeout is not None:
        args.extend(["--timeout", timeout])
    args.extend(["--", *command])
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_receipt_run_success(tmp_path: Path) -> None:
    output_dir = tmp_path / "receipt"
    result = run_receipt(output_dir, sys.executable, "-c", "print('ok')")

    assert result.returncode == 0
    receipt = json.loads((output_dir / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["exit_code"] == 0
    assert receipt["stdout_artifact_path"] == "stdout.txt"
    assert sha(output_dir / "stdout.txt") == receipt["stdout_sha256"]
    assert "verified" not in receipt


def test_receipt_run_failure_preserves_exit_code(tmp_path: Path) -> None:
    output_dir = tmp_path / "receipt"
    result = run_receipt(output_dir, sys.executable, "-c", "raise SystemExit(7)")

    assert result.returncode == 7
    receipt = json.loads((output_dir / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["exit_code"] == 7


def test_receipt_run_timeout(tmp_path: Path) -> None:
    output_dir = tmp_path / "receipt"
    result = run_receipt(output_dir, sys.executable, "-c", "import time; time.sleep(1)", timeout="0.1")

    assert result.returncode == 124
    receipt = json.loads((output_dir / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["environment_summary"]["timed_out"] is True
    assert receipt["exit_code"] == 124


def test_receipt_run_missing_command(tmp_path: Path) -> None:
    output_dir = tmp_path / "receipt"
    result = run_receipt(output_dir, "definitely-missing-playbook-command")

    assert result.returncode == 127
    receipt = json.loads((output_dir / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["exit_code"] == 127
    assert "command not found" in (output_dir / "stderr.txt").read_text(encoding="utf-8")


def test_valid_bundle_fixture_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/validate_harness_evidence.py"), str(VALID_BUNDLE / "bundle.json")],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_modified_stdout_hash_breaks_validation(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle_dir)
    (bundle_dir / "receipts/smoke/stdout.txt").write_text("tampered\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/validate_harness_evidence.py"), str(bundle_dir / "bundle.json")],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 1
    assert "RECEIPT_ARTIFACT_HASH" in result.stderr


def test_fictional_receipt_output_path_breaks_validation(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle_dir)
    receipt_path = bundle_dir / "receipts/smoke/receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["stdout_artifact_path"] = "missing-output.txt"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    refresh_receipt_ref(bundle_dir)

    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/validate_harness_evidence.py"), str(bundle_dir / "bundle.json")],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 1
    assert "RECEIPT_ARTIFACT_MISSING" in result.stderr


def test_bundle_task_id_mismatch_breaks_validation(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle_dir)
    bundle_path = bundle_dir / "bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle["task_id"] = "other-task"
    rewrite_bundle(bundle_path, bundle)

    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/validate_harness_evidence.py"), str(bundle_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 1
    assert "BUNDLE_TASK_MISMATCH" in result.stderr


def test_bundle_without_environment_digest_breaks_validation(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle_dir)
    bundle_path = bundle_dir / "bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle["environment_digest"] = ""
    rewrite_bundle(bundle_path, bundle)

    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/validate_harness_evidence.py"), str(bundle_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 1
    assert "BUNDLE_ENVIRONMENT_DIGEST" in result.stderr


def test_bundle_path_escape_breaks_validation(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle_dir)
    bundle_path = bundle_dir / "bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle["command_receipts"][0]["path"] = "../../secret.json"
    rewrite_bundle(bundle_path, bundle)

    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/validate_harness_evidence.py"), str(bundle_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 1
    assert "ARTIFACT_PATH_ESCAPE" in result.stderr


def test_manual_verdict_in_bundle_breaks_validation(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle_dir)
    bundle_path = bundle_dir / "bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle["verified"] = True
    rewrite_bundle(bundle_path, bundle)

    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/validate_harness_evidence.py"), str(bundle_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 1
    assert "EVIDENCE_MANUAL_VERDICT" in result.stderr


def test_environment_failure_cannot_be_model_failure(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle_dir)
    bundle_path = bundle_dir / "bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle["failure_records"] = [
        {
            "schema_version": "playbook.failure_record.v1",
            "failure_id": "F1",
            "run_id": "R1",
            "task_id": "smoke",
            "stage": "setup",
            "failure_class": "environment_failure",
            "owner_class": "model",
            "retryable": False,
            "retry_count": 0,
            "terminal": True,
            "message": "fixture missing dependency",
            "evidence_refs": [],
            "score_treatment": "count_as_task_failure",
            "invalid_run": False,
        }
    ]
    rewrite_bundle(bundle_path, bundle)

    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/validate_harness_evidence.py"), str(bundle_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 1
    assert "FAILURE_OWNER_MISCLASSIFIED" in result.stderr
    assert "FAILURE_INVALID_RUN_TREATMENT" in result.stderr


def test_policy_failure_blocks_green_scorer_verdict(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle"
    shutil.copytree(VALID_BUNDLE, bundle_dir)
    bundle_path = bundle_dir / "bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle["failure_records"] = [
        {
            "schema_version": "playbook.failure_record.v1",
            "failure_id": "F2",
            "run_id": "R1",
            "task_id": "smoke",
            "stage": "policy",
            "failure_class": "policy_failure",
            "owner_class": "policy",
            "retryable": False,
            "retry_count": 0,
            "terminal": True,
            "message": "immutable contract changed",
            "evidence_refs": [],
            "score_treatment": "policy_gate_failure",
            "invalid_run": False,
        }
    ]
    rewrite_bundle(bundle_path, bundle)

    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/validate_harness_evidence.py"), str(bundle_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 1
    assert "POLICY_GATE_CONFLICT" in result.stderr
