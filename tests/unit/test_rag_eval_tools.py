from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from tools import rag_eval_lib


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests/fixtures/rag_eval/valid"


def copy_fixture(tmp_path: Path) -> Path:
    target = tmp_path / "repo"
    shutil.copytree(FIXTURE, target / "tests/fixtures/rag_eval/valid")
    (target / "schemas").mkdir()
    for schema in ROOT.glob("schemas/rag_eval_*.schema.json"):
        shutil.copy2(schema, target / "schemas" / schema.name)
    return target


def load_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def write_manifest(root: Path, data: dict[str, object]) -> Path:
    path = root / "tests/fixtures/rag_eval/valid/manifest-mutated.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def valid_manifest(root: Path) -> dict[str, object]:
    return json.loads((root / "tests/fixtures/rag_eval/valid/manifest.json").read_text(encoding="utf-8"))


def valid_paths(root: Path) -> tuple[Path, Path, Path, Path]:
    base = root / "tests/fixtures/rag_eval/valid"
    return (
        base / "manifest.json",
        base / "cases.jsonl",
        base / "baseline_observations.jsonl",
        base / "candidate_observations.jsonl",
    )


def test_valid_manifest_cases_and_observations_are_accepted(tmp_path: Path) -> None:
    root = copy_fixture(tmp_path)
    manifest, cases, _, candidate = valid_paths(root)

    findings = rag_eval_lib.validate_contract(root, manifest, cases, candidate)

    assert [finding.as_dict() for finding in findings if finding.severity == "error"] == []


def test_unsupported_schema_version_rejected(tmp_path: Path) -> None:
    root = copy_fixture(tmp_path)
    manifest_data = valid_manifest(root)
    manifest_data["schema_version"] = "playbook.rag_eval_manifest.v999"
    manifest = write_manifest(root, manifest_data)

    findings = rag_eval_lib.validate_contract(root, manifest)

    assert any(finding.check_id == "RAG_SCHEMA_INVALID" for finding in findings)
    assert any(finding.check_id == "RAG_SCHEMA_VERSION_UNSUPPORTED" for finding in findings)


def test_unknown_manifest_property_rejected(tmp_path: Path) -> None:
    root = copy_fixture(tmp_path)
    manifest_data = valid_manifest(root)
    manifest_data["unexpected"] = "not allowed"
    manifest = write_manifest(root, manifest_data)

    findings = rag_eval_lib.validate_contract(root, manifest)

    assert any("Additional properties" in finding.message for finding in findings)


def test_path_traversal_rejected(tmp_path: Path) -> None:
    root = copy_fixture(tmp_path)
    manifest_data = valid_manifest(root)
    manifest_data["dataset"]["dataset_path"] = "../cases.jsonl"  # type: ignore[index]
    manifest = write_manifest(root, manifest_data)

    findings = rag_eval_lib.validate_contract(root, manifest)

    assert any(finding.check_id in {"RAG_SCHEMA_INVALID", "RAG_CASES_JSONL_INVALID"} for finding in findings)


def test_artifact_hash_mismatch_rejected(tmp_path: Path) -> None:
    root = copy_fixture(tmp_path)
    manifest_data = valid_manifest(root)
    manifest_data["dataset"]["dataset_sha256"] = "f" * 64  # type: ignore[index]
    manifest = write_manifest(root, manifest_data)

    findings = rag_eval_lib.validate_contract(root, manifest)

    assert any(finding.check_id == "RAG_HASH_MISMATCH" for finding in findings)


def test_duplicate_case_id_rejected(tmp_path: Path) -> None:
    root = copy_fixture(tmp_path)
    manifest, cases, _, _ = valid_paths(root)
    rows = load_jsonl(cases)
    duplicate_path = cases.parent / "duplicate_cases.jsonl"
    write_jsonl(duplicate_path, [rows[0], rows[0]])

    findings = rag_eval_lib.validate_contract(root, manifest, duplicate_path)

    assert any(finding.check_id == "RAG_CASE_ID_DUPLICATE" for finding in findings)


def test_observation_unknown_case_rejected(tmp_path: Path) -> None:
    root = copy_fixture(tmp_path)
    manifest, cases, _, candidate = valid_paths(root)
    rows = load_jsonl(candidate)
    rows[0]["case_id"] = "C-UNKNOWN"
    bad_observations = candidate.parent / "unknown_case_observations.jsonl"
    write_jsonl(bad_observations, rows)

    findings = rag_eval_lib.validate_contract(root, manifest, cases, bad_observations)

    assert any(finding.check_id == "RAG_OBSERVATION_CASE_UNKNOWN" for finding in findings)


def test_empirical_unknown_identity_rejected(tmp_path: Path) -> None:
    root = copy_fixture(tmp_path)
    manifest_data = valid_manifest(root)
    manifest_data["evaluation_mode"] = "empirical"
    manifest_data["identity_source"] = "unknown"
    manifest = write_manifest(root, manifest_data)

    findings = rag_eval_lib.validate_contract(root, manifest)

    assert any(finding.check_id == "RAG_EMPIRICAL_IDENTITY_UNKNOWN" for finding in findings)


def test_blocking_judge_without_calibration_rejected(tmp_path: Path) -> None:
    root = copy_fixture(tmp_path)
    manifest_data = valid_manifest(root)
    manifest_data["judge_policy"]["judge_status"] = "blocking_allowed"  # type: ignore[index]
    manifest = write_manifest(root, manifest_data)

    findings = rag_eval_lib.validate_contract(root, manifest)

    assert any(finding.check_id == "RAG_BLOCKING_JUDGE_UNCALIBRATED" for finding in findings)


def test_protected_holdout_metadata_violation_rejected(tmp_path: Path) -> None:
    root = copy_fixture(tmp_path)
    manifest_data = valid_manifest(root)
    manifest_data["dataset"]["protected_case_count"] = 1  # type: ignore[index]
    manifest_data["dataset"]["protected_holdout"]["status"] = "none"  # type: ignore[index]
    manifest = write_manifest(root, manifest_data)

    findings = rag_eval_lib.validate_contract(root, manifest)

    assert any(finding.check_id == "RAG_PROTECTED_HOLDOUT_METADATA_INVALID" for finding in findings)


def test_metric_correctness_for_hand_computable_fixture(tmp_path: Path) -> None:
    root = copy_fixture(tmp_path)
    manifest, cases, baseline, candidate = valid_paths(root)

    baseline_result, baseline_findings = rag_eval_lib.score_observations(root, manifest, cases, baseline, "lexical_baseline")
    candidate_result, candidate_findings = rag_eval_lib.score_observations(root, manifest, cases, candidate, "production_candidate")

    assert not [finding for finding in baseline_findings if finding.severity == "error"]
    assert not [finding for finding in candidate_findings if finding.severity == "error"]
    assert baseline_result["metrics"]["retrieval.hit_at_3"] == 6 / 7
    assert baseline_result["metrics"]["retrieval.mrr"] == 5.5 / 7
    assert candidate_result["metrics"]["retrieval.hit_at_3"] == 1.0
    assert candidate_result["metrics"]["retrieval.mrr"] == 6 / 7
    assert candidate_result["metrics"]["generation.no_answer_accuracy"] == 1.0
    assert candidate_result["metrics"]["retrieval.acl_leak_rate"] == 0.0
    assert candidate_result["metrics"]["retrieval.stale_doc_rejection"] == 1.0
    assert candidate_result["metrics"]["routing.domain_match_accuracy"] == 1.0
    assert candidate_result["metrics"]["harness.returned_results_consumed_ratio"] == 7 / 11
    assert candidate_result["metrics"]["perturbation.answer_change_sensitivity"] == 0.95


def test_lexical_and_dense_fixture_demonstrates_complementarity(tmp_path: Path) -> None:
    root = copy_fixture(tmp_path)
    _, _, baseline, candidate = valid_paths(root)
    baseline_rows = {row["case_id"]: row for row in load_jsonl(baseline)}
    candidate_rows = {row["case_id"]: row for row in load_jsonl(candidate)}

    assert baseline_rows["C-EXACT"]["retrieved_items"][0]["doc_id"] == "doc-exact"
    assert candidate_rows["C-EXACT"]["retrieved_items"][0]["doc_id"] != "doc-exact"
    assert baseline_rows["C-PARAPHRASE"]["answer_correct"] is False
    assert candidate_rows["C-PARAPHRASE"]["answer_correct"] is True


def test_acl_leak_is_stop_ship(tmp_path: Path) -> None:
    root = copy_fixture(tmp_path)
    manifest, cases, _, candidate = valid_paths(root)
    rows = load_jsonl(candidate)
    for row in rows:
        if row["case_id"] == "C-ACL":
            row["retrieved_items"].insert(
                0,
                {
                    "doc_id": "doc-restricted",
                    "chunk_id": "c4",
                    "span_id": "s1",
                    "source_version": "v2",
                    "rank": 1,
                    "retrieval_score": 0.99,
                    "source_timestamp": "2026-07-01",
                    "fresh": True,
                    "acl_scope": ["restricted"],
                    "acl_result": "denied",
                    "domain": "support",
                    "collection": "restricted",
                    "consumed": True,
                },
            )
            row["failure_stage"] = "acl_leak"
    bad = candidate.parent / "acl_leak_observations.jsonl"
    write_jsonl(bad, rows)

    result, findings = rag_eval_lib.score_observations(root, manifest, cases, bad, "production_candidate")

    assert not [finding for finding in findings if finding.severity == "error"]
    assert result["status"] == "fail"
    assert any(finding["rule_id"] == "ACL_LEAK" for finding in result["stop_ship_findings"])


def test_wrong_route_hides_gold_document(tmp_path: Path) -> None:
    root = copy_fixture(tmp_path)
    manifest, cases, _, candidate = valid_paths(root)
    rows = load_jsonl(candidate)
    for row in rows:
        if row["case_id"] == "C-ROUTE":
            row["route_decision"]["domain"] = "finance"
            row["route_decision"]["collection"] = "payroll"
            row["retrieved_items"] = [
                {
                    "doc_id": "doc-finance",
                    "chunk_id": "c6",
                    "span_id": "s1",
                    "source_version": "v1",
                    "rank": 1,
                    "retrieval_score": 0.9,
                    "source_timestamp": "2026-07-01",
                    "fresh": True,
                    "acl_scope": ["public", "employee"],
                    "acl_result": "allowed",
                    "domain": "finance",
                    "collection": "payroll",
                    "consumed": True,
                }
            ]
            row["answer_correct"] = False
            row["failure_stage"] = "routing"
    wrong = candidate.parent / "wrong_route_observations.jsonl"
    write_jsonl(wrong, rows)

    result, _ = rag_eval_lib.score_observations(root, manifest, cases, wrong, "production_candidate")

    assert result["by_slice"]["routing"]["routing.domain_match_accuracy"] == 0.0
    assert result["failure_taxonomy"]["routing"] == 1


def test_correct_retrieval_but_file_not_opened_is_harness_failure(tmp_path: Path) -> None:
    root = copy_fixture(tmp_path)
    manifest, cases, _, candidate = valid_paths(root)
    rows = load_jsonl(candidate)
    for row in rows:
        if row["case_id"] == "C-EXACT":
            row["harness_events"]["artifacts"] = [{"path": "reports/rag_eval/tool_result.txt", "action": "failed_open", "success": False, "sha256": None}]
            row["harness_events"]["consumed_result_count"] = 0
            row["retrieved_items"][1]["consumed"] = False
            row["answer_correct"] = False
            row["failure_stage"] = "returned_not_opened"
    bad = candidate.parent / "file_not_opened_observations.jsonl"
    write_jsonl(bad, rows)

    result, findings = rag_eval_lib.score_observations(root, manifest, cases, bad, "production_candidate")

    assert not [finding for finding in findings if finding.severity == "error"]
    assert result["failure_taxonomy"]["returned_not_opened"] == 1
    assert result["metrics"]["retrieval.hit_at_3"] == 1.0


def test_comparator_pass_and_regression_gates(tmp_path: Path) -> None:
    root = copy_fixture(tmp_path)
    manifest, cases, baseline_obs, candidate_obs = valid_paths(root)
    baseline_result, _ = rag_eval_lib.score_observations(root, manifest, cases, baseline_obs, "lexical_baseline")
    candidate_result, _ = rag_eval_lib.score_observations(root, manifest, cases, candidate_obs, "production_candidate")
    out = root / ".playbook-artifacts/rag-eval"
    out.mkdir(parents=True)
    baseline_path = out / "baseline.json"
    candidate_path = out / "candidate.json"
    baseline_path.write_text(json.dumps(baseline_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    candidate_path.write_text(json.dumps(candidate_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    comparison = rag_eval_lib.compare_results(root, manifest, baseline_path, candidate_path)

    assert comparison["status"] == "pass"
    assert comparison["compatible"] is True

    candidate_result["metrics"]["retrieval.hit_at_3"] = 0.80
    candidate_path.write_text(json.dumps(candidate_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    comparison = rag_eval_lib.compare_results(root, manifest, baseline_path, candidate_path)
    hit_delta = next(delta for delta in comparison["metric_deltas"] if delta["metric_id"] == "retrieval.hit_at_3")
    assert hit_delta["severity"] == "P1"
    assert comparison["status"] == "fail"

    candidate_result["metrics"]["retrieval.hit_at_3"] = 0.60
    candidate_path.write_text(json.dumps(candidate_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    comparison = rag_eval_lib.compare_results(root, manifest, baseline_path, candidate_path)
    hit_delta = next(delta for delta in comparison["metric_deltas"] if delta["metric_id"] == "retrieval.hit_at_3")
    assert hit_delta["severity"] == "P0"


def test_comparator_lower_is_better_and_baseline_zero(tmp_path: Path) -> None:
    root = copy_fixture(tmp_path)
    manifest, cases, _, candidate_obs = valid_paths(root)
    baseline_result, _ = rag_eval_lib.score_observations(root, manifest, cases, candidate_obs, "production_candidate")
    candidate_result = json.loads(json.dumps(baseline_result))
    candidate_result["metrics"]["retrieval.acl_leak_rate"] = 0.10
    out = root / ".playbook-artifacts/rag-eval"
    out.mkdir(parents=True)
    baseline_path = out / "baseline_zero.json"
    candidate_path = out / "candidate_acl.json"
    baseline_path.write_text(json.dumps(baseline_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    candidate_path.write_text(json.dumps(candidate_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    comparison = rag_eval_lib.compare_results(root, manifest, baseline_path, candidate_path)
    acl_delta = next(delta for delta in comparison["metric_deltas"] if delta["metric_id"] == "retrieval.acl_leak_rate")

    assert acl_delta["baseline"] == 0.0
    assert acl_delta["candidate"] == 0.10
    assert acl_delta["relative_delta"] is None
    assert acl_delta["severity"] == "P1"


def test_comparator_incompatible_dataset_is_invalid(tmp_path: Path) -> None:
    root = copy_fixture(tmp_path)
    manifest, cases, _, candidate_obs = valid_paths(root)
    baseline_result, _ = rag_eval_lib.score_observations(root, manifest, cases, candidate_obs, "production_candidate")
    candidate_result = json.loads(json.dumps(baseline_result))
    candidate_result["dataset_identity"]["dataset_sha256"] = "f" * 64
    out = root / ".playbook-artifacts/rag-eval"
    out.mkdir(parents=True)
    baseline_path = out / "baseline.json"
    candidate_path = out / "candidate_incompatible.json"
    baseline_path.write_text(json.dumps(baseline_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    candidate_path.write_text(json.dumps(candidate_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    comparison = rag_eval_lib.compare_results(root, manifest, baseline_path, candidate_path)

    assert comparison["status"] == "invalid"
    assert comparison["compatible"] is False
    assert "dataset_identity differs" in comparison["compatibility_errors"][0]


def test_cli_validate_score_compare(tmp_path: Path) -> None:
    root = copy_fixture(tmp_path)
    manifest, _, baseline_obs, candidate_obs = valid_paths(root)
    baseline_result = root / ".playbook-artifacts/rag-eval/baseline.json"
    candidate_result = root / ".playbook-artifacts/rag-eval/candidate.json"
    comparison_result = root / ".playbook-artifacts/rag-eval/comparison.json"
    comparison_report = root / "reports/rag_eval/comparison.md"

    validate = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/rag_eval_validate.py"),
            "--root",
            str(root),
            "--manifest",
            str(manifest.relative_to(root)),
            "--observations",
            str(candidate_obs.relative_to(root)),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert validate.returncode == 0, validate.stderr

    for condition, observations, output in (
        ("lexical_baseline", baseline_obs, baseline_result),
        ("production_candidate", candidate_obs, candidate_result),
    ):
        scored = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools/rag_eval_score.py"),
                "--root",
                str(root),
                "--manifest",
                str(manifest.relative_to(root)),
                "--observations",
                str(observations.relative_to(root)),
                "--condition",
                condition,
                "--json",
                str(output.relative_to(root)),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert scored.returncode == 0, scored.stderr

    compared = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/rag_eval_compare.py"),
            "--root",
            str(root),
            "--baseline",
            str(baseline_result.relative_to(root)),
            "--candidate",
            str(candidate_result.relative_to(root)),
            "--manifest",
            str(manifest.relative_to(root)),
            "--json",
            str(comparison_result.relative_to(root)),
            "--report",
            str(comparison_report.relative_to(root)),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert compared.returncode == 0, compared.stderr
    assert json.loads(comparison_result.read_text(encoding="utf-8"))["status"] == "pass"


def test_cli_score_fail_status_exits_nonzero(tmp_path: Path) -> None:
    root = copy_fixture(tmp_path)
    manifest, _, _, candidate_obs = valid_paths(root)
    rows = load_jsonl(candidate_obs)
    for row in rows:
        if row["case_id"] == "C-ACL":
            row["retrieved_items"].insert(
                0,
                {
                    "doc_id": "doc-restricted",
                    "chunk_id": "c4",
                    "span_id": "s1",
                    "source_version": "v2",
                    "rank": 1,
                    "retrieval_score": 0.99,
                    "source_timestamp": "2026-07-01",
                    "fresh": True,
                    "acl_scope": ["restricted"],
                    "acl_result": "denied",
                    "domain": "support",
                    "collection": "restricted",
                    "consumed": True,
                },
            )
            row["failure_stage"] = "acl_leak"
    bad_observations = candidate_obs.parent / "cli_acl_leak_observations.jsonl"
    write_jsonl(bad_observations, rows)
    output = root / ".playbook-artifacts/rag-eval/acl_fail.json"

    scored = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/rag_eval_score.py"),
            "--root",
            str(root),
            "--manifest",
            str(manifest.relative_to(root)),
            "--observations",
            str(bad_observations.relative_to(root)),
            "--condition",
            "production_candidate",
            "--json",
            str(output.relative_to(root)),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert scored.returncode == 1
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "fail"
