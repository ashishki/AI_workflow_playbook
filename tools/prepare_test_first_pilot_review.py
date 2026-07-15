#!/usr/bin/env python3
"""Prepare condition-blind human review packages for the frozen pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import shlex
import shutil
import stat
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import jsonschema


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from validate_harness_evidence import validate_bundle  # noqa: E402
from build_test_first_pilot_manifest import manifest_bytes as frozen_manifest_bytes  # noqa: E402
from test_first_pilot_run_seal import SealError, verify_seal  # noqa: E402
from ai_workflow_harness_lab.environment import environment_digest  # noqa: E402
from ai_workflow_harness_lab.scorers.base import (  # noqa: E402
    SCORER_VERSION,
    code_hash as current_scorer_code_hash,
)


SUITE_ID = "shishki_bot_ci_v1"
SUITE_VERSION = "1.0.0"
CONDITIONS = ("baseline", "playbook")
TRIALS = range(3)
IDENTITY_FIELDS = (
    "pilot_manifest_sha256",
    "approval_id",
    "pilot_id",
    "attempt_id",
    "model",
    "reasoning_effort",
    "service_tier",
)
SHARED_IDENTITY_FIELDS = tuple(field for field in IDENTITY_FIELDS if field != "attempt_id")
EXPECTED_EXECUTION_ORDER = (
    ("pin_ci_actions", 0, "baseline"),
    ("pin_ci_actions", 0, "playbook"),
    ("reject_unapproved_ci_actions", 0, "playbook"),
    ("reject_unapproved_ci_actions", 0, "baseline"),
    ("pin_ci_actions", 1, "playbook"),
    ("pin_ci_actions", 1, "baseline"),
    ("reject_unapproved_ci_actions", 1, "baseline"),
    ("reject_unapproved_ci_actions", 1, "playbook"),
    ("pin_ci_actions", 2, "baseline"),
    ("pin_ci_actions", 2, "playbook"),
    ("reject_unapproved_ci_actions", 2, "playbook"),
    ("reject_unapproved_ci_actions", 2, "baseline"),
)
FORBIDDEN_REVIEW_KEY_PARTS = ("condition", "path", "prompt", "timestamp", "trace")
CONDITION_LABEL_RE = re.compile(r"\b(?:baseline|playbook)\b", re.IGNORECASE)
SHA256_LINE_RE = re.compile(r"([0-9a-f]{64})  ([^\r\n]+)")
VENV_PYTHON = PROJECT_ROOT / ".venv/bin/python"
BWRAP = Path("/usr/bin/bwrap")
SANDBOX = PROJECT_ROOT / "tools/test_first_pilot_sandbox.py"
ADAPTER = PROJECT_ROOT / "tools/test_first_pilot_codex_adapter.py"
CODEX = Path(
    "/home/ashishki/.nvm/versions/node/v22.22.1/lib/node_modules/@openai/codex/"
    "node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex"
)
HOST_PYCACHE_PREFIX = "/dev/null/test-first-pilot-pycache"
VERIFIER_PYCACHE_PREFIX = "/dev/null/test-first-pilot-verifier"
TRACE_PATHS = (
    "adapter/codex_events.jsonl",
    "adapter/codex_stderr.txt",
    "adapter/final_message.txt",
    "adapter/event_ledger.jsonl",
    "adapter/adapter_summary.json",
    "run_result.json",
)
EXPECTED_SCORER_CODE_HASH = current_scorer_code_hash()


class PreparationError(RuntimeError):
    """The source evidence cannot produce a safe blind review package."""


@dataclass(frozen=True)
class TaskReviewSpec:
    task_id: str
    title: str
    version: str
    fixture: Path
    allowed_file: str
    verification_markers: tuple[str, ...]
    scorer_ids: tuple[str, ...]
    rubric: tuple[str, ...]


SUITE = PROJECT_ROOT / "companion/ai_workflow_harness_lab/suites/shishki_bot_ci_v1"
TASK_SPECS = {
    "pin_ci_actions": TaskReviewSpec(
        task_id="pin_ci_actions",
        title="Pin GitHub Actions to approved immutable revisions",
        version="pin-ci-actions.v1",
        fixture=SUITE / "fixtures/pin_ci_actions",
        allowed_file=".github/workflows/ci.yml",
        verification_markers=("pilot_tests/test_ci_pins.py",),
        scorer_ids=(
            "pin_ci_actions_acceptance",
            "pin_ci_actions_scope",
            "checkout_pin_present",
            "setup_python_pin_present",
        ),
        rubric=(
            "Every action reference uses its approved immutable revision.",
            (
                "The result preserves the canonical workflow, version comments, "
                "read-only permissions, and disabled checkout credentials."
            ),
            "The submitted change is limited to the single allowed artifact.",
        ),
    ),
    "reject_unapproved_ci_actions": TaskReviewSpec(
        task_id="reject_unapproved_ci_actions",
        title="Reject every unapproved GitHub Actions reference",
        version="reject-unapproved-ci-actions.v1",
        fixture=SUITE / "fixtures/reject_unapproved_ci_actions",
        allowed_file="tests/test_ci_supply_chain.py",
        verification_markers=(
            "tests/test_ci_supply_chain.py",
            "pilot_tests/test_unapproved_action.py",
        ),
        scorer_ids=(
            "reject_unapproved_ci_actions_acceptance",
            "reject_unapproved_ci_actions_scope",
        ),
        rubric=(
            "A reusable guard accepts the approved workflow.",
            (
                "The guard rejects third-party actions, wrong immutable revisions, "
                "mutable tags, and missing revisions across every action reference."
            ),
            "The submitted change is limited to the single allowed artifact.",
        ),
    ),
}
TASK_ORDER = tuple(TASK_SPECS)
VERIFIER_COMMANDS = {
    "pin_ci_actions": ("python", "-m", "pytest", "-q", "pilot_tests/test_ci_pins.py"),
    "reject_unapproved_ci_actions": (
        "python",
        "-m",
        "pytest",
        "-q",
        "tests/test_ci_supply_chain.py",
        "pilot_tests/test_unapproved_action.py",
    ),
}


@dataclass(frozen=True)
class ArmEvidence:
    bundle_file: Path
    bundle: dict[str, Any]
    validation: dict[str, Any]
    trial: int


def verify_completed_run_seal(run_root: Path) -> str:
    try:
        return verify_seal(run_root).seal_sha256
    except SealError as exc:
        raise PreparationError(f"completed-run seal verification failed: {exc}") from exc


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreparationError(f"cannot read JSON evidence: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PreparationError(f"JSON evidence must be an object: {path}")
    return value


EVENT_SCHEMA = load_object(PROJECT_ROOT / "schemas/test_first_pilot_event.schema.json")


def resolve_ref(bundle_dir: Path, ref: dict[str, Any]) -> Path:
    raw = Path(str(ref.get("path", "")))
    if raw.is_absolute() or ".." in raw.parts:
        raise PreparationError(f"artifact reference escapes bundle: {raw}")
    resolved = (bundle_dir / raw).resolve()
    try:
        resolved.relative_to(bundle_dir.resolve())
    except ValueError as exc:
        raise PreparationError(f"artifact reference escapes bundle: {raw}") from exc
    if not resolved.is_file():
        raise PreparationError(f"referenced artifact is unavailable: {raw}")
    return resolved


def read_text_file(path: Path, description: str) -> str:
    if path.is_symlink() or not path.is_file():
        raise PreparationError(f"{description} is missing or is not a regular file: {path}")
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise PreparationError(f"cannot read {description}: {path}: {exc}") from exc


def parse_checksum_manifest(path: Path, description: str) -> dict[str, str]:
    text = read_text_file(path, description)
    lines = text.splitlines()
    if not lines:
        raise PreparationError(f"{description} is empty")
    entries: dict[str, str] = {}
    for line_number, line in enumerate(lines, start=1):
        match = SHA256_LINE_RE.fullmatch(line)
        if match is None:
            raise PreparationError(f"invalid {description} line {line_number}")
        digest, raw_name = match.groups()
        name = Path(raw_name)
        if name.is_absolute() or ".." in name.parts or raw_name in entries:
            raise PreparationError(f"unsafe or duplicate {description} path: {raw_name}")
        entries[raw_name] = digest
    return entries


def exact_record_value(text: str, key: str, description: str) -> str:
    prefix = f"{key}: "
    matches = [line[len(prefix) :] for line in text.splitlines() if line.startswith(prefix)]
    if len(matches) != 1 or not matches[0]:
        raise PreparationError(f"{description} must contain exactly one {key} line")
    return matches[0]


def verify_governance(run_root: Path) -> dict[str, str]:
    approval_file = run_root / "approval_record.md"
    asset_manifest_file = run_root / "asset_manifest.sha256"
    critic_file = run_root / "critic_record.md"
    approval = read_text_file(approval_file, "approval record")
    critic = read_text_file(critic_file, "critic record")
    if exact_record_value(critic, "Decision", "critic record") != "ALLOW":
        raise PreparationError("critic record decision must be ALLOW")

    governance_entries = parse_checksum_manifest(
        run_root / "governance_manifest.sha256", "governance manifest"
    )
    expected_governance = {
        "approval_record.md": sha256_file(approval_file),
        "asset_manifest.sha256": sha256_file(asset_manifest_file),
        "critic_record.md": sha256_file(critic_file),
    }
    if governance_entries != expected_governance:
        raise PreparationError("governance manifest does not match the approval and critic records")

    values = {
        "approval_id": exact_record_value(approval, "Approval ID", "approval record"),
        "pilot_id": exact_record_value(approval, "Pilot ID", "approval record"),
        "pilot_manifest_sha256": exact_record_value(
            approval, "Manifest SHA-256", "approval record"
        ),
        "critic_sha256": exact_record_value(
            approval, "Critic report SHA-256", "approval record"
        ),
    }
    if not re.fullmatch(r"[0-9a-f]{64}", values["pilot_manifest_sha256"]):
        raise PreparationError("approval record manifest digest is not a lowercase SHA-256")
    if values["pilot_manifest_sha256"] != expected_governance["asset_manifest.sha256"]:
        raise PreparationError("approval record manifest digest does not match asset_manifest.sha256")
    if values["critic_sha256"] != expected_governance["critic_record.md"]:
        raise PreparationError("approval record critic digest does not match critic_record.md")
    asset_entries = parse_checksum_manifest(asset_manifest_file, "asset manifest")
    expected_manifest = frozen_manifest_bytes()
    if asset_manifest_file.read_bytes() != expected_manifest:
        raise PreparationError("copied asset manifest does not match the current frozen asset closure")
    for relative, expected_digest in asset_entries.items():
        asset = PROJECT_ROOT / relative
        if asset.is_symlink() or not asset.is_file() or sha256_file(asset) != expected_digest:
            raise PreparationError(f"frozen asset content does not match its manifest: {relative}")
    for required_line in ("Codex executions: 12", "Retries: 0"):
        if approval.splitlines().count(required_line) != 1:
            raise PreparationError(f"approval record must contain exact line: {required_line}")
    if exact_record_value(approval, "Decision", "approval record") != "approved":
        raise PreparationError("approval record decision must be approved")
    return values


def verify_bundle_manifest(run_root: Path, arms: dict[tuple[str, int, str], ArmEvidence]) -> None:
    entries = parse_checksum_manifest(run_root / "bundle_manifest.sha256", "bundle manifest")
    expected = {
        str(arm.bundle_file.relative_to(run_root)): sha256_file(arm.bundle_file)
        for arm in arms.values()
    }
    if entries != expected:
        raise PreparationError(
            "bundle manifest does not exactly match the frozen 12-arm bundle set"
        )


def trial_from_bundle_file(bundle_file: Path) -> int:
    match = re.fullmatch(r"trial-([0-9]+)", bundle_file.parent.name)
    if match is None:
        raise PreparationError(f"bundle is not in a trial directory: {bundle_file}")
    return int(match.group(1))


def collect_arms(run_root: Path) -> dict[tuple[str, int, str], ArmEvidence]:
    run_root = run_root.resolve()
    if not run_root.is_dir():
        raise PreparationError(f"run root is not a directory: {run_root}")
    bundle_files = sorted(run_root.rglob("bundle.json"))
    if len(bundle_files) != 12:
        raise PreparationError(f"completed pilot must contain exactly 12 bundles; found {len(bundle_files)}")

    arms: dict[tuple[str, int, str], ArmEvidence] = {}
    task_environments: dict[str, set[str]] = {task_id: set() for task_id in TASK_ORDER}
    for bundle_file in bundle_files:
        resolved = bundle_file.resolve()
        try:
            relative = resolved.relative_to(run_root)
        except ValueError as exc:
            raise PreparationError(f"bundle resolves outside run root: {bundle_file}") from exc
        validation = validate_bundle(resolved)
        errors = int(validation.get("summary", {}).get("errors", 0))
        if errors:
            raise PreparationError(f"bundle validation failed with {errors} error(s): {relative}")

        bundle = load_object(resolved)
        task_id = str(bundle.get("task_id", ""))
        if task_id not in TASK_SPECS:
            raise PreparationError(f"unexpected task in completed run: {task_id}")
        spec = TASK_SPECS[task_id]
        trial = trial_from_bundle_file(resolved)
        condition = str(bundle.get("condition", ""))
        if condition not in CONDITIONS or trial not in TRIALS:
            raise PreparationError(f"unexpected arm identity in bundle: {relative}")
        expected_tail = (condition, task_id, f"trial-{trial}", "bundle.json")
        if tuple(relative.parts[-4:]) != expected_tail:
            raise PreparationError(f"bundle layout disagrees with its identity: {relative}")
        if bundle.get("repository") != SUITE_ID or bundle.get("task_spec_version") != spec.version:
            raise PreparationError(f"bundle is incompatible with frozen task {task_id}: {relative}")
        if bundle.get("adapter_version") != "command.v1":
            raise PreparationError(f"bundle adapter is not frozen command.v1: {relative}")
        expected_environment = environment_digest(spec.fixture)
        if bundle.get("environment_digest") != expected_environment:
            raise PreparationError(
                f"bundle environment digest does not match frozen fixture {task_id}: {relative}"
            )
        key = (task_id, trial, condition)
        if key in arms:
            raise PreparationError(f"duplicate pilot arm: {key}")
        arms[key] = ArmEvidence(resolved, bundle, validation, trial)
        task_environments[task_id].add(str(bundle.get("environment_digest", "")))

    expected = {
        (task_id, trial, condition)
        for task_id in TASK_ORDER
        for trial in TRIALS
        for condition in CONDITIONS
    }
    if set(arms) != expected:
        missing = sorted(expected - set(arms))
        extra = sorted(set(arms) - expected)
        raise PreparationError(f"pilot arm set mismatch; missing={missing} extra={extra}")
    for task_id, digests in task_environments.items():
        if len(digests) != 1 or not next(iter(digests)):
            raise PreparationError(f"fixture environment drift across arms for {task_id}")
    return arms


def exact_ref_paths(
    arm: ArmEvidence,
    field: str,
    expected_paths: tuple[str, ...],
    expected_kind: str,
) -> list[Path]:
    refs = arm.bundle.get(field)
    if not isinstance(refs, list) or len(refs) != len(expected_paths):
        raise PreparationError(f"{field} must contain exactly {len(expected_paths)} references")
    actual_paths: list[str] = []
    resolved: list[Path] = []
    for ref in refs:
        if not isinstance(ref, dict) or ref.get("kind") != expected_kind:
            raise PreparationError(f"{field} contains an invalid artifact reference")
        actual_paths.append(str(ref.get("path", "")))
        resolved.append(resolve_ref(arm.bundle_file.parent, ref))
    if tuple(actual_paths) != expected_paths:
        raise PreparationError(f"{field} paths disagree with the frozen evidence layout")
    return resolved


def verify_prompt_evidence(arm: ArmEvidence, spec: TaskReviewSpec) -> tuple[Path, bytes]:
    ref = arm.bundle.get("prompt_ref")
    if (
        not isinstance(ref, dict)
        or ref.get("path") != "prompt.md"
        or ref.get("kind") != "prompt"
    ):
        raise PreparationError("prompt_ref must identify the copied prompt.md artifact")
    prompt_file = resolve_ref(arm.bundle_file.parent, ref)
    prompt_bytes = prompt_file.read_bytes()
    expected = SUITE / "prompts" / f"{spec.task_id}.{arm.bundle['condition']}.md"
    if prompt_bytes != expected.read_bytes():
        raise PreparationError("copied prompt does not match the frozen condition prompt")
    return prompt_file, prompt_bytes


def expected_adapter_tokens(
    arm: ArmEvidence,
    governance: dict[str, str],
    prompt_file: Path,
) -> list[str]:
    task_id = str(arm.bundle["task_id"])
    condition = str(arm.bundle["condition"])
    attempt_id = f"{task_id}-{condition}-{arm.trial}"
    workspace = (arm.bundle_file.parent / "workspace").resolve()
    output = (arm.bundle_file.parent / "adapter").resolve()
    return [
        str(BWRAP),
        "--die-with-parent",
        "--new-session",
        "--unshare-pid",
        "--bind",
        "/",
        "/",
        "--proc",
        "/proc",
        "--dev-bind",
        "/dev",
        "/dev",
        "--",
        str(VENV_PYTHON),
        "-I",
        "-B",
        "-X",
        f"pycache_prefix={HOST_PYCACHE_PREFIX}",
        str(ADAPTER),
        "--workspace",
        str(workspace),
        "--prompt",
        str(prompt_file.resolve()),
        "--output",
        str(output),
        "--pilot-id",
        governance["pilot_id"],
        "--attempt-id",
        attempt_id,
        "--task",
        task_id,
        "--condition",
        condition,
        "--trial",
        str(arm.trial),
        "--manifest-digest",
        governance["pilot_manifest_sha256"],
        "--approval-id",
        governance["approval_id"],
        "--codex-bin",
        str(CODEX),
        "--timeout",
        "1200",
    ]


def expected_verifier_argv(arm: ArmEvidence, spec: TaskReviewSpec) -> list[str]:
    workspace = (arm.bundle_file.parent / "workspace").resolve()
    return [
        str(VENV_PYTHON),
        str(SANDBOX),
        "--workspace",
        str(workspace),
        "--",
        str(VENV_PYTHON),
        "-I",
        "-X",
        f"pycache_prefix={VERIFIER_PYCACHE_PREFIX}",
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        *spec.verification_markers,
    ]


def verify_receipt_common(
    receipt: dict[str, Any],
    receipt_file: Path,
    arm: ArmEvidence,
    *,
    expected_argv: list[str],
    expected_timeout: float,
) -> tuple[int, int]:
    workspace = (arm.bundle_file.parent / "workspace").resolve()
    expected = {
        "schema_version": "playbook.command_receipt.v1",
        "task_id": arm.bundle["task_id"],
        "producer": "ai_workflow_harness_lab.receipts",
        "command_argv": expected_argv,
        "working_directory": str(workspace),
        "stdout_artifact_path": "stdout.txt",
        "stderr_artifact_path": "stderr.txt",
        "diff_stat_artifact_path": "diff_stat.txt",
        "repo_commit_before": "not_inspected",
        "repo_commit_after": "not_inspected",
        "dirty_state_before": ["not_inspected"],
        "dirty_state_after": ["not_inspected"],
        "parent_receipt_id": None,
        "redaction_status": "not_requested",
    }
    if any(receipt.get(key) != value for key, value in expected.items()):
        raise PreparationError(f"receipt disagrees with frozen command contract: {receipt_file}")
    environment = receipt.get("environment_summary")
    if (
        not isinstance(environment, dict)
        or environment.get("git_inspection") is not False
        or environment.get("timed_out") is not False
        or float(environment.get("timeout", -1)) != expected_timeout
    ):
        raise PreparationError(f"receipt environment disagrees with frozen contract: {receipt_file}")
    start = parse_event_time(receipt.get("start_timestamp"))
    end = parse_event_time(receipt.get("end_timestamp"))
    if end < start:
        raise PreparationError(f"receipt duration is negative: {receipt_file}")
    start_ns = environment.get("start_monotonic_ns")
    end_ns = environment.get("end_monotonic_ns")
    if (
        not isinstance(start_ns, int)
        or isinstance(start_ns, bool)
        or not isinstance(end_ns, int)
        or isinstance(end_ns, bool)
        or start_ns < 0
        or end_ns < start_ns
    ):
        raise PreparationError(f"receipt monotonic bounds are invalid: {receipt_file}")
    return start_ns, end_ns


def exact_receipts(
    arm: ArmEvidence,
    spec: TaskReviewSpec,
    governance: dict[str, str],
    prompt_file: Path,
) -> tuple[dict[str, Any], dict[str, Any], tuple[int, int]]:
    files = exact_ref_paths(
        arm,
        "command_receipts",
        (
            "adapter/receipts/command/receipt.json",
            "verification/receipts/required-verification/receipt.json",
        ),
        "command_receipt",
    )
    outer = load_object(files[0])
    verifier = load_object(files[1])
    outer_argv = outer.get("command_argv")
    if not isinstance(outer_argv, list) or outer_argv[:2] != ["/bin/sh", "-c"] or len(outer_argv) != 3:
        raise PreparationError("outer adapter receipt must use exact /bin/sh -c argv")
    try:
        rendered = shlex.split(str(outer_argv[2]))
    except ValueError as exc:
        raise PreparationError("outer adapter command is not valid shell argv") from exc
    expected_outer = ["/bin/sh", "-c", str(outer_argv[2])]
    if rendered != expected_adapter_tokens(arm, governance, prompt_file):
        raise PreparationError("outer adapter command does not match the frozen bwrap/adapter argv")
    outer_times = verify_receipt_common(
        outer,
        files[0],
        arm,
        expected_argv=expected_outer,
        expected_timeout=1260.0,
    )
    verify_receipt_common(
        verifier,
        files[1],
        arm,
        expected_argv=expected_verifier_argv(arm, spec),
        expected_timeout=60.0,
    )
    return outer, verifier, outer_times


def read_failure_records(arm: ArmEvidence) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in arm.bundle.get("failure_records", []):
        if not isinstance(item, dict):
            raise PreparationError("failure record must be an object")
        if "failure_class" in item:
            records.append(item)
        elif "path" in item:
            records.append(load_object(resolve_ref(arm.bundle_file.parent, item)))
        else:
            raise PreparationError("failure record has no class or artifact reference")
    return records


def normalized_verification(arm: ArmEvidence, spec: TaskReviewSpec) -> dict[str, Any]:
    refs = arm.bundle.get("command_receipts", [])
    if not isinstance(refs, list) or len(refs) != 2 or not isinstance(refs[1], dict):
        raise PreparationError(f"required-verifier receipt is missing for {spec.task_id}")
    receipt_file = resolve_ref(arm.bundle_file.parent, refs[1])
    receipt = load_object(receipt_file)
    exit_code = int(receipt.get("exit_code", -1))
    environment = receipt.get("environment_summary", {})
    timed_out = environment.get("timed_out", "unknown") if isinstance(environment, dict) else "unknown"
    stdout_name = Path(str(receipt.get("stdout_artifact_path", "")))
    if stdout_name.is_absolute() or ".." in stdout_name.parts:
        raise PreparationError("verifier stdout reference escapes its receipt")
    stdout_file = (receipt_file.parent / stdout_name).resolve()
    try:
        stdout_file.relative_to(receipt_file.parent.resolve())
    except ValueError as exc:
        raise PreparationError("verifier stdout reference escapes its receipt") from exc
    stdout = stdout_file.read_text(encoding="utf-8", errors="replace")
    counts: dict[str, int] = {}
    for result_name in ("passed", "failed", "errors", "skipped", "xfailed", "xpassed"):
        match = re.search(rf"\b([0-9]+)\s+{result_name}\b", stdout)
        if match:
            counts[result_name] = int(match.group(1))
    return {
        "status": "passed" if exit_code == 0 else "failed",
        "exit_code": exit_code,
        "timed_out": timed_out,
        "test_counts": counts,
    }


def load_scorer_evidence(arm: ArmEvidence, spec: TaskReviewSpec) -> list[dict[str, Any]]:
    files = exact_ref_paths(
        arm,
        "scorer_outputs",
        tuple(f"scorers/{scorer_id}.json" for scorer_id in spec.scorer_ids),
        "scorer_output",
    )
    scorers: list[dict[str, Any]] = []
    for expected_id, scorer_file in zip(spec.scorer_ids, files):
        scorer = load_object(scorer_file)
        expected = {
            "schema_version": "playbook.scorer_output.v1",
            "scorer_id": expected_id,
            "scorer_version": SCORER_VERSION,
            "scorer_code_hash": EXPECTED_SCORER_CODE_HASH,
            "task_id": spec.task_id,
        }
        if any(scorer.get(key) != value for key, value in expected.items()):
            raise PreparationError(f"scorer output disagrees with frozen identity: {scorer_file}")
        failures = scorer.get("failure_records")
        if not isinstance(failures, list) or not all(isinstance(item, str) for item in failures):
            raise PreparationError(f"scorer failure IDs are invalid: {scorer_file}")
        scorers.append(scorer)
    return scorers


def normalized_scorers(arm: ArmEvidence, spec: TaskReviewSpec) -> list[dict[str, Any]]:
    scorers: list[dict[str, Any]] = []
    for scorer in load_scorer_evidence(arm, spec):
        failures = scorer["failure_records"]
        scorers.append(
            {
                "id": str(scorer["scorer_id"]),
                "version": str(scorer.get("scorer_version", "unknown")),
                "verdict": str(scorer.get("verdict", "unknown")),
                "score": scorer.get("score", "unknown"),
                "failure_count": len(failures),
            }
        )
    return scorers


def parse_event_time(raw: object) -> datetime:
    if not isinstance(raw, str):
        raise PreparationError("pilot event time must be an ISO-8601 string")
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PreparationError("pilot event time is not valid ISO-8601") from exc
    if value.tzinfo is None or value.utcoffset() is None:
        raise PreparationError("pilot event time must include an offset")
    return value


def command_text(item: dict[str, Any]) -> str:
    command = item.get("command", "")
    if isinstance(command, list):
        return " ".join(str(part) for part in command)
    return str(command)


def is_verifier(task_id: str, command: str) -> bool:
    expected = VERIFIER_COMMANDS.get(task_id)
    if expected is None:
        return False
    try:
        tokens = shlex.split(command)
        if (
            len(tokens) == 3
            and Path(tokens[0]).name in {"bash", "sh"}
            and tokens[1] in {"-c", "-lc"}
        ):
            tokens = shlex.split(tokens[2])
    except ValueError:
        return False
    return tuple(tokens) == expected


def command_result(item: dict[str, Any]) -> tuple[int | None, str]:
    raw_exit = item.get("exit_code")
    exit_code = raw_exit if isinstance(raw_exit, int) else None
    if exit_code == 0:
        return exit_code, "passed"
    if exit_code is not None:
        return exit_code, "failed"
    return None, "unknown"


def relative_change_paths(item: dict[str, Any], workspace: Path) -> list[str]:
    raw_paths: list[str] = []
    changes = item.get("changes")
    if isinstance(changes, list):
        for change in changes:
            if isinstance(change, dict) and isinstance(change.get("path"), str):
                raw_paths.append(change["path"])
    if isinstance(item.get("path"), str):
        raw_paths.append(item["path"])

    paths: list[str] = []
    for raw in raw_paths:
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = workspace / candidate
        try:
            paths.append(str(candidate.resolve().relative_to(workspace)))
        except ValueError:
            paths.append("<outside-workspace>")
    return sorted(set(paths))


def named_trace(arm: ArmEvidence, filename: str, description: str) -> Path:
    candidates: list[Path] = []
    refs = arm.bundle.get("trace_refs", [])
    if not isinstance(refs, list):
        raise PreparationError("trace_refs must be a list")
    for ref in refs:
        if not isinstance(ref, dict):
            raise PreparationError("trace reference must be an object")
        if Path(str(ref.get("path", ""))).name == filename:
            candidates.append(resolve_ref(arm.bundle_file.parent, ref))
    if len(candidates) != 1:
        raise PreparationError(f"pilot arm must contain exactly one {description}")
    return candidates[0]


def raw_codex_events(arm: ArmEvidence) -> list[dict[str, Any]]:
    trace = named_trace(arm, "codex_events.jsonl", "raw Codex trace")
    try:
        lines = trace.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise PreparationError(f"cannot read raw Codex trace: {exc}") from exc
    if not lines or len(lines) > 10_000:
        raise PreparationError("raw Codex trace has an invalid event count")

    events: list[dict[str, Any]] = []
    for index, line in enumerate(lines, start=1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PreparationError(f"invalid raw Codex event at line {index}: {exc}") from exc
        if not isinstance(event, dict):
            raise PreparationError(f"raw Codex event at line {index} must be an object")
        events.append(event)
    return events


def event_ledger(arm: ArmEvidence) -> list[dict[str, Any]]:
    ledger = named_trace(arm, "event_ledger.jsonl", "event ledger")

    events: list[dict[str, Any]] = []
    try:
        lines = ledger.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise PreparationError(f"cannot read pilot event ledger: {exc}") from exc
    if not lines or len(lines) > 10_000:
        raise PreparationError("pilot event ledger has an invalid event count")
    for index, line in enumerate(lines, start=1):
        try:
            event = json.loads(line)
            jsonschema.validate(event, EVENT_SCHEMA)
        except (json.JSONDecodeError, jsonschema.ValidationError) as exc:
            raise PreparationError(f"invalid pilot event at line {index}: {exc}") from exc
        if not isinstance(event, dict):
            raise PreparationError(f"pilot event at line {index} must be an object")
        if (
            event.get("task_id") != arm.bundle.get("task_id")
            or event.get("condition") != arm.bundle.get("condition")
            or event.get("trial") != arm.trial
        ):
            raise PreparationError("pilot event identity disagrees with its bundle")
        events.append(event)

    if any(len({event[field] for event in events}) != 1 for field in IDENTITY_FIELDS):
        raise PreparationError("pilot event identity drifts within an arm")
    event_times = [parse_event_time(event["timestamp"]) for event in events]
    if event_times != sorted(event_times):
        raise PreparationError("pilot event order is not chronological")
    monotonic_values = [event["monotonic_ns"] for event in events]
    if monotonic_values != sorted(monotonic_values) or len(set(monotonic_values)) != len(
        monotonic_values
    ):
        raise PreparationError("pilot event monotonic order is not strict")
    return events


def expected_derived_events(
    arm: ArmEvidence, raw_events: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    task_id = str(arm.bundle.get("task_id"))
    workspace = (arm.bundle_file.parent / "workspace").resolve()
    expected: list[dict[str, Any]] = []
    verifier_attempts = 0
    verifier_by_item: dict[str, int] = {}
    last_verifier_result = "unknown"
    last_verifier_attempt: int | None = None
    first_green_observed = False
    file_change_count = 0

    for payload in raw_events:
        event_type = payload.get("type")
        item = payload.get("item")
        if event_type not in {"item.started", "item.completed"} or not isinstance(item, dict):
            continue
        item_type = item.get("type")
        item_id = str(item.get("id", "unknown"))
        if item_type == "command_execution":
            command = command_text(item)
            command_event: dict[str, Any] = {
                "event": "command_start" if event_type == "item.started" else "command_end",
                "source_event_type": str(event_type),
                "source_item_id": item_id,
                "command": command,
            }
            if event_type == "item.completed":
                exit_code, result = command_result(item)
                command_event["result"] = result
                if exit_code is not None:
                    command_event["exit_code"] = exit_code
            expected.append(command_event)
            if not is_verifier(task_id, command):
                continue
            if event_type == "item.started":
                verifier_attempts += 1
                verifier_by_item[item_id] = verifier_attempts
                expected.append(
                    {
                        "event": "verifier_start",
                        "source_event_type": str(event_type),
                        "source_item_id": item_id,
                        "command": command,
                        "verifier_attempt": verifier_attempts,
                    }
                )
                continue

            attempt = verifier_by_item.get(item_id)
            if attempt is None:
                verifier_attempts += 1
                attempt = verifier_attempts
            exit_code, result = command_result(item)
            verifier_end: dict[str, Any] = {
                "event": "verifier_end",
                "source_event_type": str(event_type),
                "source_item_id": item_id,
                "command": command,
                "verifier_attempt": attempt,
                "result": result,
            }
            if exit_code is not None:
                verifier_end["exit_code"] = exit_code
            expected.append(verifier_end)
            last_verifier_attempt = attempt
            last_verifier_result = result
            if result == "passed" and not first_green_observed:
                first_green_observed = True
                expected.append(
                    {
                        "event": "first_green",
                        "source_item_id": item_id,
                        "verifier_attempt": attempt,
                        "result": result,
                    }
                )
            elif result == "failed" and file_change_count > 0:
                expected.append(
                    {
                        "event": "repair_candidate",
                        "source_item_id": item_id,
                        "verifier_attempt": attempt,
                        "result": result,
                        "reason": "verifier failed after an observed file change",
                    }
                )
        elif event_type == "item.completed" and item_type == "file_change":
            file_change_count += 1
            expected.append(
                {
                    "event": "file_change",
                    "source_event_type": str(event_type),
                    "source_item_id": item_id,
                    "file_paths": relative_change_paths(item, workspace),
                    "change_count": file_change_count,
                }
            )

    final_gate: dict[str, Any] = {
        "event": "final_model_gate",
        "result": last_verifier_result,
    }
    if last_verifier_attempt is None:
        final_gate["reason"] = "no declared verifier command observed in Codex JSONL"
    else:
        final_gate["verifier_attempt"] = last_verifier_attempt
    expected.append(final_gate)
    return expected


def verify_ledger_derivation(arm: ArmEvidence, events: list[dict[str, Any]]) -> None:
    derived_names = {
        "command_start",
        "command_end",
        "file_change",
        "verifier_start",
        "verifier_end",
        "first_green",
        "repair_candidate",
        "final_model_gate",
    }
    ignored_fields = set(IDENTITY_FIELDS) | {
        "schema_version",
        "task_id",
        "condition",
        "trial",
        "timestamp",
        "monotonic_ns",
    }
    actual = [
        {key: value for key, value in event.items() if key not in ignored_fields}
        for event in events
        if event.get("event") in derived_names
    ]
    expected = expected_derived_events(arm, raw_codex_events(arm))
    if actual != expected:
        raise PreparationError(
            "event ledger does not match events derived from the raw Codex trace"
        )


def single_event(events: list[dict[str, Any]], name: str) -> dict[str, Any]:
    matches = [event for event in events if event.get("event") == name]
    if len(matches) != 1:
        raise PreparationError(f"pilot event ledger must contain exactly one {name}")
    return matches[0]


def elapsed_seconds(start: dict[str, Any], end: dict[str, Any] | None) -> float | str:
    if end is None:
        return "unknown"
    elapsed = (parse_event_time(end["timestamp"]) - parse_event_time(start["timestamp"])).total_seconds()
    if elapsed < 0:
        raise PreparationError("pilot event duration is negative")
    return round(elapsed, 6)


def verify_adapter_summary(
    arm: ArmEvidence,
    prompt_bytes: bytes,
    outer: dict[str, Any],
    events: list[dict[str, Any]],
    outer_times: tuple[int, int],
) -> None:
    trace_files = exact_ref_paths(arm, "trace_refs", TRACE_PATHS, "trace")
    summary = load_object(trace_files[4])
    start = single_event(events, "adapter_start")
    end = single_event(events, "adapter_end")
    if events[0] is not start or events[-1] is not end:
        raise PreparationError("adapter_start and adapter_end must bound the event ledger")
    identity = {field: start[field] for field in IDENTITY_FIELDS}
    expected_summary = {
        **identity,
        "schema_version": "test_first_pilot.adapter_summary.v1",
        "codex_cli": "codex-cli 0.144.4",
        "codex_exit_code": end.get("codex_exit_code"),
        "wrapper_exit_code": end.get("wrapper_exit_code"),
        "terminal_class": end.get("terminal_class"),
        "timed_out": end.get("timed_out"),
        "network_access": False,
        "web_search": "disabled",
        "permission_profile": "test_first_pilot",
        "prompt_sha256": sha256_bytes(prompt_bytes),
        "prompt_size_bytes": len(prompt_bytes),
        "trace_path": "codex_events.jsonl",
        "stderr_path": "codex_stderr.txt",
        "final_message_path": "final_message.txt",
        "ledger_path": "event_ledger.jsonl",
    }
    if any(summary.get(key) != value for key, value in expected_summary.items()):
        raise PreparationError("adapter summary disagrees with prompt, identity, or terminal ledger")
    if outer.get("exit_code") != summary.get("wrapper_exit_code"):
        raise PreparationError("outer receipt exit code disagrees with adapter summary")
    stdout_path = (arm.bundle_file.parent / "adapter/receipts/command/stdout.txt").resolve()
    try:
        stdout = json.loads(stdout_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreparationError("outer adapter stdout is not the terminal JSON record") from exc
    terminal = {
        key: summary[key]
        for key in ("codex_exit_code", "wrapper_exit_code", "terminal_class", "timed_out")
    }
    if stdout != terminal:
        raise PreparationError("outer adapter stdout disagrees with adapter summary")
    ledger_start = int(start["monotonic_ns"])
    ledger_end = int(end["monotonic_ns"])
    if not (outer_times[0] <= ledger_start <= ledger_end <= outer_times[1]):
        raise PreparationError("event ledger is not contained by the outer command receipt")


def verify_outcome_correlation(
    arm: ArmEvidence,
    spec: TaskReviewSpec,
    outer: dict[str, Any],
    verifier: dict[str, Any],
    events: list[dict[str, Any]],
) -> None:
    run_id = f"{spec.task_id}-{arm.bundle['condition']}-{arm.trial}"
    failures = read_failure_records(arm)
    failure_ids = [str(record.get("failure_id", "")) for record in failures]
    if (
        any(not failure_id for failure_id in failure_ids)
        or len(set(failure_ids)) != len(failure_ids)
        or any(
            record.get("schema_version") != "playbook.failure_record.v1"
            or record.get("run_id") != run_id
            or record.get("task_id") != spec.task_id
            for record in failures
        )
    ):
        raise PreparationError("bundle failure records have inconsistent identity")

    scorers = load_scorer_evidence(arm, spec)
    scorer_failure_ids = [
        failure_id
        for scorer in scorers
        for failure_id in scorer["failure_records"]
    ]
    expected_failure_ids = list(scorer_failure_ids)
    outer_exit = int(outer.get("exit_code", -1))
    if outer_exit != 0:
        environment = outer.get("environment_summary", {})
        suffix = "adapter-timeout" if environment.get("timed_out") else f"adapter-exit-{outer_exit}"
        expected_failure_ids.insert(0, f"{run_id}-{suffix}")
    verifier_exit = int(verifier.get("exit_code", -1))
    if verifier_exit != 0:
        expected_failure_ids.insert(0, f"{run_id}-verification-exit-{verifier_exit}")
    if sorted(expected_failure_ids) != sorted(failure_ids):
        raise PreparationError("bundle, verifier, and scorer failure IDs do not correlate")
    scoring_failures = sorted(
        str(record["failure_id"]) for record in failures if record.get("stage") == "scoring"
    )
    if scoring_failures != sorted(scorer_failure_ids):
        raise PreparationError("scorer failure IDs do not match scoring failure records")
    if verifier_exit != 0 and not any(
        record.get("failure_id") == f"{run_id}-verification-exit-{verifier_exit}"
        and record.get("stage") == "verification"
        for record in failures
    ):
        raise PreparationError("required-verifier failure record has the wrong stage")

    run_result = load_object(
        exact_ref_paths(arm, "trace_refs", TRACE_PATHS, "trace")[5]
    )
    invalid = any(record.get("invalid_run") is True for record in failures)
    policy_fail = any(
        record.get("failure_class") == "policy_failure" and record.get("terminal")
        for record in failures
    )
    task_fail = any(
        not record.get("invalid_run")
        and record.get("score_treatment") == "count_as_task_failure"
        for record in failures
    )
    task_gate = any(
        not record.get("invalid_run")
        and record.get("score_treatment")
        in {"count_as_task_failure", "policy_gate_failure"}
        for record in failures
    )
    scores = [float(scorer.get("score", 0.0)) for scorer in scorers]
    score = 0.0 if invalid or task_gate else sum(scores) / len(scores)
    if invalid:
        verdict, status, score_value = "invalid_run", "not_scored", None
    elif policy_fail or task_fail or score < 1.0:
        verdict, status, score_value = "failed", "fail", score
    else:
        verdict, status, score_value = "passed", "pass", score
    expected_result = {
        "schema_version": "playbook.run_result.v1",
        "run_id": run_id,
        "task_id": spec.task_id,
        "failure_records": failure_ids,
        "final_verdict": verdict,
        "policy_status": "fail" if policy_fail else "pass",
        "evidence_status": (
            "invalid"
            if any(record.get("failure_class") == "invalid_evidence" for record in failures)
            else "complete"
        ),
    }
    if any(run_result.get(key) != value for key, value in expected_result.items()):
        raise PreparationError("run_result identity, failures, or verdict do not correlate")
    task_score = run_result.get("task_score")
    validity = run_result.get("run_validity")
    intervention = single_event(events, "human_intervention")
    if (
        not isinstance(task_score, dict)
        or task_score.get("status") != status
        or task_score.get("score") != score_value
        or not isinstance(validity, dict)
        or validity.get("valid") is not (not invalid)
        or run_result.get("human_intervention")
        != {"required": False, "status": "not_requested"}
        or intervention.get("occurred") is not False
    ):
        raise PreparationError("run_result score, validity, or intervention does not correlate")


def validate_completed_run(
    run_root: Path, arms: dict[tuple[str, int, str], ArmEvidence]
) -> None:
    governance = verify_governance(run_root)
    verify_bundle_manifest(run_root, arms)

    arm_records: list[tuple[int, int, tuple[str, int, str], dict[str, Any]]] = []
    attempts: set[str] = set()
    shared_identities: list[dict[str, Any]] = []
    for key, arm in arms.items():
        invalid = [
            record
            for record in read_failure_records(arm)
            if record.get("invalid_run") is True
        ]
        if invalid:
            raise PreparationError(f"invalid_run arm cannot enter outcome review: {key}")

        spec = TASK_SPECS[key[0]]
        prompt_file, prompt_bytes = verify_prompt_evidence(arm, spec)
        events = event_ledger(arm)
        verify_ledger_derivation(arm, events)
        outer, verifier, outer_times = exact_receipts(
            arm, spec, governance, prompt_file
        )
        verify_adapter_summary(arm, prompt_bytes, outer, events, outer_times)
        verify_outcome_correlation(arm, spec, outer, verifier, events)
        start = single_event(events, "adapter_start")
        end = single_event(events, "adapter_end")
        identity = {field: start[field] for field in IDENTITY_FIELDS}
        if any(event[field] != identity[field] for event in events for field in IDENTITY_FIELDS):
            raise PreparationError(f"pilot event identity drifts within arm {key}")
        expected_attempt = f"{key[0]}-{key[2]}-{key[1]}"
        if identity["attempt_id"] != expected_attempt:
            raise PreparationError(f"attempt ID disagrees with the frozen schedule for arm {key}")
        if identity["attempt_id"] in attempts:
            raise PreparationError(f"duplicate attempt ID: {identity['attempt_id']}")
        attempts.add(str(identity["attempt_id"]))
        shared_identities.append({field: identity[field] for field in SHARED_IDENTITY_FIELDS})
        arm_records.append(
            (
                outer_times[0],
                outer_times[1],
                key,
                identity,
            )
        )

    if len(attempts) != 12:
        raise PreparationError("completed pilot must contain 12 unique attempt IDs")
    if any(identity != shared_identities[0] for identity in shared_identities[1:]):
        raise PreparationError(
            "pilot, approval, manifest, model, reasoning, or service identity drifts across arms"
        )

    identity = shared_identities[0]
    if run_root.name != identity["pilot_id"]:
        raise PreparationError("run-root directory name disagrees with the pilot ID")
    for field in ("approval_id", "pilot_id", "pilot_manifest_sha256"):
        if governance[field] != identity[field]:
            raise PreparationError(f"approval record {field} disagrees with pilot events")

    chronological = sorted(arm_records, key=lambda item: item[0])
    if len({record[0] for record in chronological}) != len(chronological):
        raise PreparationError(
            "pilot schedule cannot be reconstructed from duplicate outer monotonic starts"
        )
    if tuple(record[2] for record in chronological) != EXPECTED_EXECUTION_ORDER:
        raise PreparationError("outer receipt monotonic order disagrees with the frozen schedule")
    if any(current[0] < previous[1] for previous, current in zip(chronological, chronological[1:])):
        raise PreparationError("pilot arms overlap despite the frozen sequential schedule")


def normalized_process(arm: ArmEvidence) -> dict[str, Any]:
    events = event_ledger(arm)
    verify_ledger_derivation(arm, events)
    adapter_start = single_event(events, "adapter_start")
    adapter_end = single_event(events, "adapter_end")
    intervention = single_event(events, "human_intervention")
    final_gate = single_event(events, "final_model_gate")
    first_green_events = [event for event in events if event.get("event") == "first_green"]
    if len(first_green_events) > 1:
        raise PreparationError("pilot event ledger contains multiple first-green events")
    verifier_ends = [event for event in events if event.get("event") == "verifier_end"]
    repair_candidates = [event for event in events if event.get("event") == "repair_candidate"]
    first_green = first_green_events[0] if first_green_events else None
    return {
        "verifier_attempts": len(verifier_ends),
        "verifier_failures": sum(event.get("result") == "failed" for event in verifier_ends),
        "repair_candidates": len(repair_candidates),
        "prompt_correction_limit": 1,
        "correction_limit_enforcement": "not_enforced",
        "first_green_observed": first_green is not None,
        "seconds_to_first_green": elapsed_seconds(adapter_start, first_green),
        "seconds_to_final_model_gate": elapsed_seconds(adapter_start, final_gate),
        "final_model_gate": final_gate.get("result", "unknown"),
        "human_intervention": bool(intervention.get("occurred")),
        "terminal_class": adapter_end.get("terminal_class", "unknown"),
        "timed_out": bool(adapter_end.get("timed_out")),
    }


def allowed_change(arm: ArmEvidence, spec: TaskReviewSpec) -> dict[str, Any]:
    manifest_ref = arm.bundle.get("post_state_manifest")
    if not isinstance(manifest_ref, dict):
        raise PreparationError("post-state manifest reference is missing")
    manifest = load_object(resolve_ref(arm.bundle_file.parent, manifest_ref))
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise PreparationError("post-state manifest has no file digest map")

    workspace = (arm.bundle_file.parent / "workspace").resolve()
    candidate = (workspace / spec.allowed_file).resolve()
    try:
        candidate.relative_to(workspace)
    except ValueError as exc:
        raise PreparationError("allowed artifact resolves outside workspace") from exc
    expected_digest = files.get(spec.allowed_file)
    if not candidate.exists():
        if expected_digest is not None:
            raise PreparationError("post-state manifest records a missing allowed artifact")
        return {"state": "deleted", "sha256": None, "content": None}
    if candidate.is_symlink() or not candidate.is_file():
        raise PreparationError("allowed artifact is not a regular file")
    content_bytes = candidate.read_bytes()
    actual_digest = sha256_bytes(content_bytes)
    if expected_digest != actual_digest:
        raise PreparationError("allowed artifact disagrees with post-state manifest")
    try:
        content = content_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PreparationError("allowed artifact is not UTF-8 text") from exc
    if CONDITION_LABEL_RE.search(content):
        raise PreparationError("allowed artifact contains an arm label and cannot be blinded")
    base_bytes = (spec.fixture / spec.allowed_file).read_bytes()
    state = "unchanged" if content_bytes == base_bytes else "modified"
    return {"state": state, "sha256": actual_digest, "content": content}


def candidate_payload(arm: ArmEvidence, spec: TaskReviewSpec) -> dict[str, Any]:
    failures = read_failure_records(arm)
    failure_classes = Counter(str(record.get("failure_class", "unknown")) for record in failures)
    invalid_count = sum(1 for record in failures if record.get("invalid_run") is True)
    return {
        "run_valid": invalid_count == 0,
        "evidence_validation": {
            "errors": 0,
            "warnings": int(arm.validation.get("summary", {}).get("warnings", 0)),
        },
        "allowed_change": allowed_change(arm, spec),
        "verification": normalized_verification(arm, spec),
        "scorers": normalized_scorers(arm, spec),
        "failure_counts": dict(sorted(failure_classes.items())),
        "invalid_failure_count": invalid_count,
    }


def assert_blind_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if any(part in lowered for part in FORBIDDEN_REVIEW_KEY_PARTS):
                raise PreparationError(f"review payload contains forbidden key: {key}")
            assert_blind_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_blind_payload(item)
        return
    if isinstance(value, str) and CONDITION_LABEL_RE.search(value):
        raise PreparationError("review payload exposes an arm label")


def is_within(candidate: Path, parent: Path) -> bool:
    try:
        candidate.relative_to(parent)
    except ValueError:
        return False
    return True


def validate_output_boundaries(run_root: Path, review_output: Path, mapping_output: Path) -> tuple[Path, Path, Path]:
    run_root = run_root.resolve()
    review_output = review_output.resolve()
    mapping_output = mapping_output.resolve()
    if (
        review_output == mapping_output
        or is_within(review_output, mapping_output)
        or is_within(mapping_output, review_output)
    ):
        raise PreparationError("review and protected mapping outputs must not overlap")
    if is_within(review_output, run_root) or is_within(mapping_output, run_root):
        raise PreparationError("review outputs must not modify the completed run root")
    if review_output.exists() or mapping_output.exists():
        raise PreparationError("refusing to overwrite an existing review or mapping output")
    return run_root, review_output, mapping_output


def prepare(run_root: Path, review_output: Path, mapping_output: Path) -> dict[str, Any]:
    run_root, review_output, mapping_output = validate_output_boundaries(run_root, review_output, mapping_output)
    initial_seal_sha256 = verify_completed_run_seal(run_root)
    arms = collect_arms(run_root)
    validate_completed_run(run_root, arms)
    assignments = [False] * 3 + [True] * 3
    secrets.SystemRandom().shuffle(assignments)

    packages: list[tuple[str, bytes]] = []
    mappings: list[dict[str, Any]] = []
    pair_index = 0
    for task_id in TASK_ORDER:
        spec = TASK_SPECS[task_id]
        for trial in TRIALS:
            pair_index += 1
            pair_id = f"pair-{pair_index:03d}"
            swapped = assignments[pair_index - 1]
            labels = {
                "A": CONDITIONS[1] if swapped else CONDITIONS[0],
                "B": CONDITIONS[0] if swapped else CONDITIONS[1],
            }
            package = {
                "schema_version": "test_first_pilot.blind_review_pair.v1",
                "pair_id": pair_id,
                "task": {
                    "id": spec.task_id,
                    "title": spec.title,
                    "version": spec.version,
                    "trial": trial,
                    "rubric": list(spec.rubric),
                },
                "candidates": {
                    label: candidate_payload(arms[(task_id, trial, source)], spec)
                    for label, source in labels.items()
                },
            }
            assert_blind_payload(package)
            package_bytes = json_bytes(package)
            packages.append((pair_id, package_bytes))
            mappings.append(
                {
                    "pair_id": pair_id,
                    "task_id": task_id,
                    "trial": trial,
                    "package_sha256": sha256_bytes(package_bytes),
                    "labels": {
                        label: {
                            "condition": source,
                            "source_bundle": str(arms[(task_id, trial, source)].bundle_file.relative_to(run_root)),
                            "bundle_sha256": sha256_file(arms[(task_id, trial, source)].bundle_file),
                            "execution_process": normalized_process(arms[(task_id, trial, source)]),
                        }
                        for label, source in labels.items()
                    },
                }
            )

    mapping = {
        "schema_version": "test_first_pilot.protected_review_mapping.v1",
        "suite_id": SUITE_ID,
        "suite_version": SUITE_VERSION,
        "completed_run_seal_sha256": initial_seal_sha256,
        "pair_count": len(mappings),
        "mappings": mappings,
    }
    mapping_bytes = json_bytes(mapping)
    review_manifest = {
        "schema_version": "test_first_pilot.blind_review_manifest.v1",
        "suite_id": SUITE_ID,
        "suite_version": SUITE_VERSION,
        "pair_count": len(packages),
        "protected_mapping_sha256": sha256_bytes(mapping_bytes),
        "package_digests": {pair_id: sha256_bytes(payload) for pair_id, payload in packages},
    }
    assert_blind_payload(review_manifest)
    final_seal_sha256 = verify_completed_run_seal(run_root)
    if final_seal_sha256 != initial_seal_sha256:
        raise PreparationError("completed-run seal changed while preparing review packages")

    created: list[Path] = []
    try:
        review_output.parent.mkdir(parents=True, exist_ok=True)
        mapping_output.parent.mkdir(parents=True, exist_ok=True)
        review_output.mkdir(mode=0o750)
        created.append(review_output)
        mapping_output.mkdir(mode=0o700)
        created.append(mapping_output)
        os.chmod(review_output, 0o750)
        os.chmod(mapping_output, 0o700)
        for pair_id, payload in packages:
            target = review_output / f"{pair_id}.json"
            target.write_bytes(payload)
            os.chmod(target, 0o640)
        manifest_file = review_output / "manifest.json"
        manifest_file.write_bytes(json_bytes(review_manifest))
        os.chmod(manifest_file, 0o640)
        mapping_file = mapping_output / "mapping.json"
        mapping_file.write_bytes(mapping_bytes)
        os.chmod(mapping_file, 0o600)
    except Exception:
        for created_path in reversed(created):
            if created_path.exists() and stat.S_ISDIR(created_path.stat().st_mode):
                shutil.rmtree(created_path)
        raise

    return {
        "status": "prepared",
        "pair_count": len(packages),
        "review_output": str(review_output),
        "mapping_output": str(mapping_output),
        "mapping_sha256": sha256_bytes(mapping_bytes),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--review-output", required=True, type=Path)
    parser.add_argument("--mapping-output", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = prepare(args.run_root, args.review_output, args.mapping_output)
    except PreparationError as exc:
        print(f"prepare_test_first_pilot_review: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
