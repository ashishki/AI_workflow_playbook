#!/usr/bin/env python3
"""Initialize a downstream repository with a proportional playbook kit."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import planning_depth as planning_depth_rules
except ImportError:  # pragma: no cover
    planning_depth_rules = None  # type: ignore[assignment]


PLAYBOOK_ROOT = Path(__file__).resolve().parents[1]
UNKNOWN_PLACEHOLDER_RE = re.compile(r"(?<!\$)\{\{[^{}\n]+\}\}")
NOT_READY_VALUES = {"", "unknown", "tbd", "todo"}


@dataclass
class CopyResult:
    created: list[Path]
    skipped: list[Path]


def read_template(relative_path: str) -> str:
    return (PLAYBOOK_ROOT / relative_path).read_text(encoding="utf-8")


def render(text: str, replacements: dict[str, str]) -> str:
    rendered = text
    for key, value in replacements.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    rendered = UNKNOWN_PLACEHOLDER_RE.sub(scaffold_placeholder, rendered)
    return rendered


def scaffold_placeholder(match: re.Match[str]) -> str:
    name = match.group(0).strip("{} ")
    return f"not_applicable - scaffold placeholder {name}; replace before treating this section as authoritative"


def parse_verify_argv(raw_values: list[str]) -> tuple[list[list[str]], list[str]]:
    parsed: list[list[str]] = []
    errors: list[str] = []
    for index, raw in enumerate(raw_values, 1):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"--verify-argv #{index} must be a JSON array of strings: {exc}")
            continue
        if not isinstance(value, list) or not value or not all(isinstance(part, str) and part for part in value):
            errors.append(f"--verify-argv #{index} must be a non-empty JSON array of non-empty strings")
            continue
        parsed.append(value)
    return parsed, errors


def display_verify_commands(argvs: list[list[str]]) -> str:
    return "\n".join(" ".join(shlex.quote(part) for part in argv) for argv in argvs)


def project_verification_config(verify_argvs: list[list[str]]) -> str:
    checks: list[dict[str, object]] = [
        {
            "id": "playbook_contract",
            "argv": [
                "{python}",
                "tools/playbook_validate.py",
                "--root",
                ".",
                "--check",
                "tasks",
                "--check",
                "placeholders",
                "--check",
                "readiness",
                "--check",
                "design",
                "--check",
                "instructions",
                "--check",
                "delivery",
            ],
            "required": True,
            "expected_exit_code": 0,
            "timeout_seconds": 60,
        }
    ]
    for index, argv in enumerate(verify_argvs, 1):
        checks.append(
            {
                "id": "project_verification" if index == 1 else f"project_verification_{index}",
                "argv": argv,
                "required": True,
                "expected_exit_code": 0,
                "timeout_seconds": 600,
            }
        )
    payload = {
        "schema_version": "playbook.project_verification.v1",
        "checks": checks,
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def add_rag_eval_project_check(config_text: str) -> str:
    payload = json.loads(config_text)
    payload["checks"].append(
        {
            "id": "rag_eval_contract",
            "argv": [
                "{python}",
                "tools/playbook_validate.py",
                "--root",
                ".",
                "--check",
                "rag",
            ],
            "required": True,
            "expected_exit_code": 0,
            "timeout_seconds": 60,
        }
    )
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def readiness_state_config(mode: str, planning_depth: str, risk_level: str, planning_depth_source: str) -> str:
    design_required = planning_depth in {"compact_design", "designed_slices"}
    approval_required = (
        "human_required"
        if planning_depth == "designed_slices" and risk_level in {"high", "critical"}
        else "human_or_authorized_reviewer"
        if design_required
        else "not_required"
    )
    payload = {
        "schema_version": "playbook.readiness_state.v1",
        "mode": mode,
        "state": "design_required" if design_required else "scaffold",
        "planning_depth": planning_depth,
        "planning_depth_source": planning_depth_source,
        "design_approval_required": approval_required,
        "required_design_refs": ["docs/design/F01.design.json"] if design_required else [],
        "required_decision_policy": "mode_profile_risk_triggered",
        "unresolved_decision_marker": "scaffold placeholder",
        "implementation_ready_requires_no_scaffold_placeholders": True,
        "release_ready_requires_current_verification": True,
        "notes": [
            "Initializer output is a scaffold until project-specific decisions are resolved.",
            "If state is design_required, do not begin implementation until the required feature design is approved.",
            "Do not mark implementation_ready, release_candidate, or release_ready while generated scaffold placeholders remain active.",
            "Release readiness is resolved after tools/verify_project.py by tools/resolve_release_readiness.py.",
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def feature_design_registry_config(planning_depth: str, risk_level: str) -> str:
    approval_policy = (
        "human_required"
        if planning_depth == "designed_slices" and risk_level in {"high", "critical"}
        else "human_or_authorized_reviewer"
    )
    payload = {
        "schema_version": "playbook.feature_design.v1",
        "feature_id": "F01",
        "status": "draft",
        "planning_depth": planning_depth,
        "risk_level": risk_level,
        "brief_ref": "docs/PROJECT_BRIEF.md",
        "architecture_refs": [],
        "approval_policy": approval_policy,
        "slices": [],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def delivery_execution_model_config() -> str:
    payload = {
        "schema_version": "playbook.delivery_execution_model.v1",
        "delivery_profile": "solo_verified",
        "orchestrator": {"kind": "human", "authority": "select_task_and_accept_completion"},
        "implementer": {"kind": "active_codex_session", "may_write_code": True},
        "reviewer": {
            "kind": "human_or_independent_agent_by_risk",
            "required_when": ["medium_or_higher_risk", "auth_secrets_billing", "destructive_or_external_write"],
        },
        "verifier": {
            "kind": "deterministic_project_verifier",
            "binding_id": "project_verifier",
            "argv": ["{python}", "tools/verify_project.py", "--root", "."],
            "command": "python tools/verify_project.py --root .",
        },
        "completion_authority": {"kind": "human", "requires": ["project_verification_passed", "risk_review_satisfied"]},
        "cli_bindings": {
            "codex_direct": "active_session_runs_shell_directly",
            "external_codex_exec": "ci_harness_or_non_codex_orchestrator_only",
        },
        "permission_profile": "repo_local_default",
        "budget": {"model_call_budget": "project_defined", "spend_budget": "project_defined"},
        "independent_review_triggers": [
            "meaningful_implementation_change",
            "security_or_privacy_boundary",
            "production_release_claim",
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json_hash(data: object) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def rag_eval_case_jsonl() -> str:
    rows = [
        {
            "schema_version": "playbook.rag_eval_case.v1",
            "case_id": "RAG-SMOKE-001",
            "query": "What is the documented support code?",
            "slices": ["simple", "clean"],
            "tags": ["lexical_baseline", "mechanism_fixture"],
            "principal": {"principal_id": "public-smoke", "authorization_scope": ["public"]},
            "language": "en",
            "locale": "en-US",
            "expected_route": {
                "domain": "support",
                "collection": "public",
                "ambiguous": False,
                "fallback_allowed": True,
            },
            "expected_evidence": [
                {
                    "doc_id": "rag-smoke-doc",
                    "chunk_id": "c1",
                    "span_id": "s1",
                    "source_version": "scaffold-v1",
                    "domain": "support",
                    "collection": "public",
                }
            ],
            "acceptable_evidence": [],
            "forbidden_evidence": [],
            "distractors": [],
            "no_answer_expected": False,
            "freshness_expectation": {
                "requires_current": False,
                "current_after": None,
                "stale_doc_ids": [],
            },
            "required_modalities": ["text"],
            "expected_answer": "The support code is RAG-SMOKE.",
            "protected_expected_answer_ref": None,
            "rubric_ref": "docs/retrieval_eval.md",
            "pair_group_id": None,
            "noise_scenario": "clean",
            "visibility": "public",
            "provenance": {
                "source": "synthetic_seed",
                "created_by": "init_playbook_project",
                "created_at": "2026-07-26",
                "generator_model": None,
                "generator_prompt_version": None,
            },
            "validation_status": "validated",
        },
        {
            "schema_version": "playbook.rag_eval_case.v1",
            "case_id": "RAG-SMOKE-NA-001",
            "query": "What is the unavailable launch code?",
            "slices": ["no-answer", "clean"],
            "tags": ["insufficient_evidence", "mechanism_fixture"],
            "principal": {"principal_id": "public-smoke", "authorization_scope": ["public"]},
            "language": "en",
            "locale": "en-US",
            "expected_route": {
                "domain": None,
                "collection": None,
                "ambiguous": False,
                "fallback_allowed": True,
            },
            "expected_evidence": [],
            "acceptable_evidence": [],
            "forbidden_evidence": [],
            "distractors": [],
            "no_answer_expected": True,
            "freshness_expectation": {
                "requires_current": False,
                "current_after": None,
                "stale_doc_ids": [],
            },
            "required_modalities": ["text"],
            "expected_answer": None,
            "protected_expected_answer_ref": None,
            "rubric_ref": "docs/retrieval_eval.md",
            "pair_group_id": None,
            "noise_scenario": "clean",
            "visibility": "public",
            "provenance": {
                "source": "synthetic_seed",
                "created_by": "init_playbook_project",
                "created_at": "2026-07-26",
                "generator_model": None,
                "generator_prompt_version": None,
            },
            "validation_status": "validated",
        },
    ]
    return "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n"


def rag_eval_observations_jsonl(condition_id: str, run_id: str) -> str:
    rows = [
        {
            "schema_version": "playbook.rag_eval_observation.v1",
            "run_id": run_id,
            "trial_id": "t1",
            "condition_id": condition_id,
            "case_id": "RAG-SMOKE-001",
            "route_decision": {
                "domain": "support",
                "collection": "public",
                "confidence": 1.0,
                "fallback_used": False,
                "no_route": False,
                "ambiguous": False,
                "latency_ms": 0,
                "cost_usd": 0,
            },
            "retrieved_items": [
                {
                    "doc_id": "rag-smoke-doc",
                    "chunk_id": "c1",
                    "span_id": "s1",
                    "source_version": "scaffold-v1",
                    "rank": 1,
                    "retrieval_score": 1.0,
                    "source_timestamp": "2026-07-26",
                    "fresh": True,
                    "acl_scope": ["public"],
                    "acl_result": "allowed",
                    "domain": "support",
                    "collection": "public",
                    "consumed": True,
                }
            ],
            "assembled_context": {
                "items": [
                    {
                        "doc_id": "rag-smoke-doc",
                        "chunk_id": "c1",
                        "span_id": "s1",
                        "order": 1,
                        "token_count": 8,
                    }
                ],
                "token_count": 8,
                "truncated": False,
            },
            "answer": "The support code is RAG-SMOKE.",
            "answer_correct": True,
            "citations": [
                {
                    "doc_id": "rag-smoke-doc",
                    "chunk_id": "c1",
                    "span_id": "s1",
                    "claim_id": "claim-1",
                    "supports_claim": True,
                }
            ],
            "abstained": False,
            "insufficient_evidence": False,
            "harness_events": {
                "retrieval_calls": 1,
                "search_queries": ["support code"],
                "search_query_refs": [],
                "artifacts": [],
                "returned_result_count": 1,
                "consumed_result_count": 1,
                "retries": 0,
                "termination_reason": "completed",
            },
            "latency_ms": {"retrieval": 1, "reranking": 0, "generation": 1, "e2e": 2},
            "tokens": {"input": 20, "output": 5},
            "cost": {"total_usd": 0},
            "errors": [],
            "failure_stage": None,
        },
        {
            "schema_version": "playbook.rag_eval_observation.v1",
            "run_id": run_id,
            "trial_id": "t1",
            "condition_id": condition_id,
            "case_id": "RAG-SMOKE-NA-001",
            "route_decision": {
                "domain": None,
                "collection": None,
                "confidence": None,
                "fallback_used": True,
                "no_route": True,
                "ambiguous": False,
                "latency_ms": 0,
                "cost_usd": 0,
            },
            "retrieved_items": [],
            "assembled_context": {"items": [], "token_count": 0, "truncated": False},
            "answer": None,
            "answer_correct": True,
            "citations": [],
            "abstained": True,
            "insufficient_evidence": True,
            "harness_events": {
                "retrieval_calls": 1,
                "search_queries": ["unavailable launch code"],
                "search_query_refs": [],
                "artifacts": [],
                "returned_result_count": 0,
                "consumed_result_count": 0,
                "retries": 0,
                "termination_reason": "insufficient_evidence",
            },
            "latency_ms": {"retrieval": 1, "reranking": 0, "generation": 1, "e2e": 2},
            "tokens": {"input": 20, "output": 1},
            "cost": {"total_usd": 0},
            "errors": [],
            "failure_stage": None,
        },
    ]
    return "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n"


def rag_condition(condition_id: str, retrieval_strategy: str, retriever_version: str) -> dict[str, object]:
    condition: dict[str, object] = {
        "condition_id": condition_id,
        "rag_shape": "fixed_pipeline",
        "retrieval_strategy": retrieval_strategy,
        "retriever_version": retriever_version,
        "chunking_version": "scaffold-chunks-v1",
        "embedding": {
            "provider": "not_applicable" if retrieval_strategy == "lexical" else "project_defined",
            "name": "not_applicable" if retrieval_strategy == "lexical" else "project_defined",
            "version": "not_applicable" if retrieval_strategy == "lexical" else "project_defined",
        },
        "index": {"provider": "project_defined", "name": "scaffold-index", "version": "v1"},
        "reranker": {"provider": "not_applicable", "name": "not_applicable", "version": "not_applicable"},
        "top_k": 3,
        "candidate_k": 3,
        "filter_policy_version": "scaffold-filter-v1",
        "router_taxonomy_version": "not_applicable",
        "router_version": "not_applicable",
        "graph_builder_version": "not_applicable",
        "entity_dedup_version": "not_applicable",
        "context_assembly_version": "scaffold-context-v1",
        "generator_model": "project_defined",
        "generator_prompt_version": "scaffold-prompt-v1",
        "citation_contract_version": "scaffold-citations-v1",
        "abstention_policy_version": "scaffold-abstention-v1",
        "harness": {
            "harness_type": "fixed_pipeline",
            "harness_version": "scaffold-harness-v1",
            "tool_registry_version": "not_applicable",
            "delivery_profile": "inline",
            "context_policy_version": "scaffold-context-policy-v1",
            "memory_policy_version": "not_applicable",
            "permission_policy_version": "scaffold-permissions-v1",
            "retry_policy": "no-retry",
            "termination_policy": "single-pass",
            "max_iterations": 1,
            "timeout_seconds": 30,
        },
    }
    condition["compatibility_fingerprint"] = canonical_json_hash(condition)
    return condition


def rag_eval_manifest_config() -> str:
    cases = rag_eval_case_jsonl()
    corpus = (
        "corpus_id=scaffold_rag_eval_corpus\n"
        "corpus_version=scaffold-v1\n"
        "This generated corpus snapshot is a mechanism fixture, not empirical evidence.\n"
    )
    baseline_condition = rag_condition("lexical_baseline", "lexical", "scaffold-lexical-v1")
    candidate_condition = rag_condition("production_candidate", "hybrid", "scaffold-candidate-v1")
    payload = {
        "schema_version": "playbook.rag_eval_manifest.v1",
        "suite_id": "scaffold_rag_eval",
        "suite_version": "scaffold-v1",
        "owner": "project-owner",
        "risk_level": "medium",
        "evaluation_mode": "mechanism_demonstration",
        "identity_source": "declared",
        "repository": "project-local",
        "project_commit": "0" * 40,
        "dirty_state_policy": "record_only",
        "created_at": "2026-07-26T00:00:00Z",
        "dataset": {
            "dataset_id": "scaffold_rag_eval_cases",
            "dataset_version": "scaffold-v1",
            "dataset_source": "synthetic_seed",
            "dataset_path": ".playbook/rag_eval_cases.jsonl",
            "dataset_sha256": sha256_text(cases),
            "case_count": 2,
            "public_case_count": 2,
            "protected_case_count": 0,
            "holdout_policy": "none - public mechanism scaffold",
            "contamination_policy": "visible scaffold cannot support empirical claims",
            "minimum_sample_policy": "diagnostic smoke only; replace before release evidence",
            "protected_holdout": {
                "status": "none",
                "public_boundary": "no protected cases in scaffold",
                "contamination_status": "clean",
            },
        },
        "corpus": {
            "corpus_id": "scaffold_rag_eval_corpus",
            "corpus_version": "scaffold-v1",
            "corpus_snapshot_ref": ".playbook/rag_eval_corpus_snapshot.txt",
            "corpus_sha256": sha256_text(corpus),
            "index_schema_version": "scaffold-index-v1",
            "source_inventory_version": "scaffold-inventory-v1",
            "freshness_cutoff": "2026-01-01",
        },
        "conditions": [baseline_condition, candidate_condition],
        "experiment_design": {
            "question_slices": ["simple", "no-answer"],
            "noise_scenarios": ["clean"],
            "perturbation_scenarios": ["none"],
            "trial_count": 1,
            "controlled_factors": ["dataset", "corpus", "generator_model"],
            "changed_factors": ["retrieval_strategy"],
            "baseline_condition_ref": "lexical_baseline",
            "cost_budget_note": "offline scaffold only",
        },
        "evaluation_policy": {
            "metrics": [
                {
                    "metric_id": "retrieval.hit_at_3",
                    "stage": "candidate_retrieval",
                    "direction": "higher_is_better",
                    "release_significant": True,
                },
                {
                    "metric_id": "retrieval.acl_leak_rate",
                    "stage": "candidate_retrieval",
                    "direction": "lower_is_better",
                    "release_significant": True,
                },
                {
                    "metric_id": "generation.no_answer_accuracy",
                    "stage": "generation_citations_abstention",
                    "direction": "higher_is_better",
                    "release_significant": True,
                },
            ],
            "minimum_thresholds": {"retrieval.acl_leak_rate": 0.0},
            "absolute_regression_thresholds": {"p1": 0.05, "p0": 0.15},
            "relative_regression_thresholds": {"p1": 0.05, "p0": 0.15},
            "slice_thresholds": {},
            "required_stop_ship_rules": [
                "ACL_LEAK",
                "NO_ANSWER_PATH_MISSING",
                "HASH_MISMATCH",
                "INVALID_RUN_AS_PASS",
            ],
            "uncertainty_policy": "report N; scaffold is mechanism-only",
        },
        "judge_policy": {
            "judge_status": "disabled",
            "judge_model": None,
            "judge_prompt_version": None,
            "rubric_version": None,
            "calibration_ref": None,
            "calibration_sha256": None,
            "human_sample_ref": None,
            "eval_cost_budget": "not_applicable",
        },
        "outputs": {
            "result_path": ".playbook-artifacts/rag-eval/result.json",
            "report_path": "reports/rag_eval/result.md",
            "trace_refs": [],
            "evidence_bundle_path": None,
            "harness_eval_unit_ref": None,
        },
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def rag_eval_corpus_snapshot() -> str:
    return (
        "corpus_id=scaffold_rag_eval_corpus\n"
        "corpus_version=scaffold-v1\n"
        "This generated corpus snapshot is a mechanism fixture, not empirical evidence.\n"
    )


def readiness_value(value: str) -> str:
    return value.strip()


def validate_required_readiness(args: argparse.Namespace) -> list[str]:
    required = {
        "operational_pain": "--operational-pain",
        "current_workaround": "--current-workaround",
        "first_proof_metric": "--first-proof-metric",
    }
    errors: list[str] = []
    for attr, flag in required.items():
        value = readiness_value(str(getattr(args, attr, "")))
        if value.lower() in NOT_READY_VALUES:
            errors.append(f"{flag} is required and cannot be unknown/TBD/TODO/empty")
    return errors


def should_skip(path: Path, force: bool) -> bool:
    return path.exists() and not force


def write_text_file(path: Path, content: str, force: bool, dry_run: bool, result: CopyResult) -> None:
    if should_skip(path, force):
        result.skipped.append(path)
        return
    result.created.append(path)
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_file(
    source_relative: str,
    destination: Path,
    replacements: dict[str, str],
    force: bool,
    dry_run: bool,
    result: CopyResult,
) -> None:
    content = render(read_template(source_relative), replacements)
    write_text_file(destination, content, force=force, dry_run=dry_run, result=result)


def copy_binary_or_text_file(source: Path, destination: Path, force: bool, dry_run: bool, result: CopyResult) -> None:
    if should_skip(destination, force):
        result.skipped.append(destination)
        return
    result.created.append(destination)
    if dry_run:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def copy_tree(source_relative: str, destination: Path, force: bool, dry_run: bool, result: CopyResult) -> None:
    source = PLAYBOOK_ROOT / source_relative
    if not source.exists():
        return
    for item in sorted(source.rglob("*")):
        if item.is_dir():
            continue
        if "__pycache__" in item.parts:
            continue
        relative = item.relative_to(source)
        copy_binary_or_text_file(item, destination / relative, force=force, dry_run=dry_run, result=result)


def copy_rendered_tree(
    source_relative: str,
    destination: Path,
    replacements: dict[str, str],
    force: bool,
    dry_run: bool,
    result: CopyResult,
) -> None:
    source = PLAYBOOK_ROOT / source_relative
    if not source.exists():
        return
    for item in sorted(source.rglob("*")):
        if item.is_dir() or "__pycache__" in item.parts:
            continue
        relative = item.relative_to(source)
        if item.suffix.lower() in {".md", ".json", ".yml", ".yaml", ".toml", ".txt"}:
            copy_file(str(item.relative_to(PLAYBOOK_ROOT)), destination / relative, replacements, force, dry_run, result)
        else:
            copy_binary_or_text_file(item, destination / relative, force=force, dry_run=dry_run, result=result)


def copy_prompt_files(
    destination: Path,
    replacements: dict[str, str],
    force: bool,
    dry_run: bool,
    result: CopyResult,
) -> None:
    source = PLAYBOOK_ROOT / "prompts"
    for item in sorted(source.glob("*.md")):
        copy_file(str(item.relative_to(PLAYBOOK_ROOT)), destination / item.name, replacements, force, dry_run, result)


def chmod_executable(path: Path) -> None:
    if not path.exists():
        return
    mode = path.stat().st_mode
    path.chmod(mode | 0o111)


def verify_project_script() -> str:
    return """#!/usr/bin/env python3
\"\"\"Generated project verification entrypoint.\"\"\"

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SHELL_NAMES = {"sh", "bash", "zsh", "fish", "cmd", "cmd.exe", "powershell", "powershell.exe", "pwsh", "pwsh.exe"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else "not-a-git-repository"


def artifact_ref(path: Path, root: Path) -> dict[str, str]:
    return {
        "path": str(path.relative_to(root)),
        "sha256": sha256_file(path),
    }


def safe_relative_path(root: Path, raw: str) -> Path | None:
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        return None
    resolved = (root / path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return resolved


def load_config(root: Path, explicit_path: str | None) -> tuple[dict[str, Any] | None, list[str]]:
    path = Path(explicit_path) if explicit_path else root / ".playbook/project_verification.json"
    if not path.is_absolute():
        path = root / path
    if not path.is_file():
        return None, [f"project verification config missing: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"project verification config is invalid JSON: {exc}"]
    if not isinstance(data, dict):
        return None, ["project verification config must be a JSON object"]
    return data, []


def materialize_argv(argv: list[str], root: Path) -> list[str]:
    replacements = {
        "{python}": sys.executable,
        "{root}": str(root),
    }
    rendered: list[str] = []
    for value in argv:
        for placeholder, replacement in replacements.items():
            value = value.replace(placeholder, replacement)
        rendered.append(value)
    return rendered


def has_self_reference(argv: list[str]) -> bool:
    for value in argv:
        normalized = value.replace("\\\\", "/")
        if normalized == "verify_project.py" or normalized.endswith("/verify_project.py") or "tools/verify_project.py" in normalized:
            return True
    return False


def validate_check(raw: Any, root: Path) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(raw, dict):
        return None, ["check must be an object"]
    check_id = raw.get("id")
    argv = raw.get("argv")
    if not isinstance(check_id, str) or not check_id:
        errors.append("check.id must be a non-empty string")
    elif not all(char.isalnum() or char in "_.-" for char in check_id):
        errors.append(f"check {check_id} id may contain only letters, numbers, underscore, dot, or hyphen")
    if not isinstance(argv, list) or not argv or not all(isinstance(part, str) and part for part in argv):
        errors.append(f"check {check_id or '<unknown>'} argv must be a non-empty array of strings")
        argv = []
    argv = list(argv)
    if has_self_reference(argv):
        errors.append(f"check {check_id or '<unknown>'} must not call tools/verify_project.py recursively")
    shell_name = Path(argv[0]).name.lower() if argv else ""
    if shell_name in SHELL_NAMES and raw.get("allow_shell") is not True:
        errors.append(f"check {check_id or '<unknown>'} uses shell execution without allow_shell=true")
    cwd_raw = raw.get("cwd", ".")
    if not isinstance(cwd_raw, str) or safe_relative_path(root, cwd_raw) is None:
        errors.append(f"check {check_id or '<unknown>'} cwd must be relative and stay inside project root")
    expected_exit = raw.get("expected_exit_code", 0)
    if not isinstance(expected_exit, int):
        errors.append(f"check {check_id or '<unknown>'} expected_exit_code must be an integer")
    required = raw.get("required", True)
    if not isinstance(required, bool):
        errors.append(f"check {check_id or '<unknown>'} required must be boolean")
    timeout = raw.get("timeout_seconds")
    if timeout is not None and (not isinstance(timeout, (int, float)) or timeout <= 0):
        errors.append(f"check {check_id or '<unknown>'} timeout_seconds must be positive")
    env = raw.get("env", {})
    if not isinstance(env, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in env.items()):
        errors.append(f"check {check_id or '<unknown>'} env must map strings to strings")
    platforms = raw.get("platforms")
    if platforms is not None and (not isinstance(platforms, list) or not all(isinstance(item, str) for item in platforms)):
        errors.append(f"check {check_id or '<unknown>'} platforms must be an array of strings")
    if errors:
        return None, errors
    return {
        "id": check_id,
        "argv": argv,
        "cwd": cwd_raw,
        "required": required,
        "expected_exit_code": expected_exit,
        "timeout_seconds": timeout,
        "env": env,
        "platforms": platforms,
    }, []


def validate_config(config: dict[str, Any], root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    if config.get("schema_version") != "playbook.project_verification.v1":
        errors.append("project verification config schema_version must be playbook.project_verification.v1")
    raw_checks = config.get("checks")
    if not isinstance(raw_checks, list) or not raw_checks:
        errors.append("project verification config checks must be a non-empty array")
        return [], errors
    checks: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in raw_checks:
        check, check_errors = validate_check(raw, root)
        errors.extend(check_errors)
        if check is None:
            continue
        if check["id"] in seen:
            errors.append(f"duplicate check id: {check['id']}")
            continue
        seen.add(check["id"])
        checks.append(check)
    return checks, errors


def write_result(root: Path, checks: list[dict[str, Any]], config_errors: list[str], started_at: str) -> Path:
    artifacts_root = root / ".playbook-artifacts"
    artifacts_root.mkdir(parents=True, exist_ok=True)
    required_failures = sum(
        1
        for check in checks
        if check.get("required") and not check.get("passed", False)
    )
    payload = {
        "schema_version": "playbook.project_verification_result.v1",
        "project_commit": git_commit(root),
        "started_at": started_at,
        "finished_at": utc_now(),
        "platform": platform.platform(),
        "python_executable": sys.executable,
        "checks": checks,
        "configuration_errors": config_errors,
        "required_failures": required_failures,
    }
    result_path = artifacts_root / "project_verification.json"
    result_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
    return result_path


def run_check(root: Path, artifacts_root: Path, check: dict[str, Any]) -> dict[str, Any]:
    current_platform = sys.platform
    platforms = check.get("platforms")
    argv = materialize_argv(check["argv"], root)
    check_dir = artifacts_root / "project_verification" / check["id"]
    check_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = check_dir / "stdout.txt"
    stderr_path = check_dir / "stderr.txt"
    if platforms and current_platform not in platforms:
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text(f"skipped on platform {current_platform}\\n", encoding="utf-8")
        passed = not check["required"]
        return {
            "id": check["id"],
            "argv": argv,
            "cwd": check["cwd"],
            "required": check["required"],
            "expected_exit_code": check["expected_exit_code"],
            "exit_code": None,
            "passed": passed,
            "skipped": True,
            "stdout_ref": artifact_ref(stdout_path, root),
            "stderr_ref": artifact_ref(stderr_path, root),
        }
    env = os.environ.copy()
    env.update(check.get("env", {}))
    cwd = safe_relative_path(root, check["cwd"])
    assert cwd is not None
    timed_out = False
    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=check.get("timeout_seconds"),
            check=False,
        )
        exit_code = int(completed.returncode)
        stdout = completed.stdout
        stderr = completed.stderr
    except FileNotFoundError as exc:
        exit_code = 127
        stdout = b""
        stderr = f"verify_project: command not found: {exc.filename}\\n".encode("utf-8")
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = 124
        stdout = exc.stdout or b""
        stderr = (exc.stderr or b"") + f"\\nverify_project: timeout after {check.get('timeout_seconds')} seconds\\n".encode("utf-8")
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    passed = exit_code == check["expected_exit_code"]
    return {
        "id": check["id"],
        "argv": argv,
        "cwd": check["cwd"],
        "required": check["required"],
        "expected_exit_code": check["expected_exit_code"],
        "exit_code": exit_code,
        "passed": passed,
        "skipped": False,
        "timed_out": timed_out,
        "stdout_ref": artifact_ref(stdout_path, root),
        "stderr_ref": artifact_ref(stderr_path, root),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--config", default=None)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    started_at = utc_now()
    config, load_errors = load_config(root, args.config)
    if config is None:
        result_path = write_result(root, [], load_errors, started_at)
        for error in load_errors:
            print(f"verify_project: {error}", file=sys.stderr)
        print(f"verify_project: result={result_path}")
        return 2
    checks, config_errors = validate_config(config, root)
    if config_errors:
        result_path = write_result(root, [], config_errors, started_at)
        for error in config_errors:
            print(f"verify_project: {error}", file=sys.stderr)
        print(f"verify_project: result={result_path}")
        return 2
    artifacts_root = root / ".playbook-artifacts"
    results = [run_check(root, artifacts_root, check) for check in checks]
    result_path = write_result(root, results, [], started_at)
    required_failures = sum(1 for item in results if item["required"] and not item["passed"])
    for item in results:
        status = "SKIP" if item["skipped"] else "PASS" if item["passed"] else "FAIL"
        print(f"{status}: {item['id']} exit={item['exit_code']}")
    print(f"verify_project: required_failures={required_failures} result={result_path}")
    return 1 if required_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def problem_fit_note(replacements: dict[str, str]) -> str:
    return render(
        """# Problem Fit Note

Project: {{PROJECT_NAME}}
Mode: {{MODE}}
Last updated: {{DATE}}

## Operational Pain

{{OPERATIONAL_PAIN}}

## Current Workaround

{{CURRENT_WORKAROUND}}

## First Proof Metric

{{FIRST_PROOF_METRIC}}

## Out-Of-Bounds Claims Before Evidence

- production-ready autonomous system
- replaces accountable human review
- verified success without command evidence

## Verification Command

`{{VERIFY_COMMAND}}`
""",
        replacements,
    )


def add_common_files(args: argparse.Namespace, target: Path, replacements: dict[str, str], result: CopyResult) -> None:
    copy_file("templates/PROJECT_BRIEF.md", target / "docs/PROJECT_BRIEF.md", replacements, args.force, args.dry_run, result)
    copy_file("templates/TASKS.md", target / "docs/tasks.md", replacements, args.force, args.dry_run, result)
    copy_file("templates/FEATURE_DESIGN.md", target / "templates/FEATURE_DESIGN.md", replacements, args.force, args.dry_run, result)
    copy_file("templates/INSTRUCTION_MANIFEST.json", target / "templates/INSTRUCTION_MANIFEST.json", replacements, args.force, args.dry_run, result)
    copy_file("docs/project_fit_guide.md", target / "docs/project_fit_guide.md", replacements, args.force, args.dry_run, result)
    copy_file("docs/adoption_modes.md", target / "docs/adoption_modes.md", replacements, args.force, args.dry_run, result)
    copy_file("docs/cost_budget_guardrails.md", target / "docs/cost_budget_guardrails.md", replacements, args.force, args.dry_run, result)
    copy_file("docs/cost_telemetry_protocol.md", target / "docs/cost_telemetry_protocol.md", replacements, args.force, args.dry_run, result)
    copy_file("docs/cache_context_layout.md", target / "docs/cache_context_layout.md", replacements, args.force, args.dry_run, result)
    copy_file("docs/external_skill_security_policy.md", target / "docs/external_skill_security_policy.md", replacements, args.force, args.dry_run, result)
    copy_file("docs/codex_exec_subagent_protocol.md", target / "docs/codex_exec_subagent_protocol.md", replacements, args.force, args.dry_run, result)
    copy_file("docs/audited_execution_protocol.md", target / "docs/audited_execution_protocol.md", replacements, args.force, args.dry_run, result)
    copy_file("templates/COST_BUDGET.md", target / "docs/COST_BUDGET.md", replacements, args.force, args.dry_run, result)
    copy_file("templates/README_INDEX.md", target / "docs/README.md", replacements, args.force, args.dry_run, result)
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/integrity_check.py",
        target / "tools/integrity_check.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/cost_rollup.py",
        target / "tools/cost_rollup.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/skill_security_gate.py",
        target / "tools/skill_security_gate.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/render_codex_exec_prompt.py",
        target / "tools/render_codex_exec_prompt.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/playbook_validate.py",
        target / "tools/playbook_validate.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/feature_design_lib.py",
        target / "tools/feature_design_lib.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/planning_depth.py",
        target / "tools/planning_depth.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/create_feature_design.py",
        target / "tools/create_feature_design.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/validate_feature_design.py",
        target / "tools/validate_feature_design.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/render_slice_context.py",
        target / "tools/render_slice_context.py",
        args.force,
        args.dry_run,
        result,
    )
    for tool_name in (
        "approve_feature_design.py",
        "feature_review_policy.py",
        "feature_workflow.py",
        "receipt_run.py",
    ):
        copy_binary_or_text_file(
            PLAYBOOK_ROOT / "tools" / tool_name,
            target / "tools" / tool_name,
            args.force,
            args.dry_run,
            result,
        )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/check_maintainability.py",
        target / "tools/check_maintainability.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/resolve_release_readiness.py",
        target / "tools/resolve_release_readiness.py",
        args.force,
        args.dry_run,
        result,
    )
    write_text_file(
        target / "tools/verify_project.py",
        verify_project_script(),
        force=args.force,
        dry_run=args.dry_run,
        result=result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/cost_telemetry_entry.schema.json",
        target / "schemas/cost_telemetry_entry.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/task.schema.json",
        target / "schemas/task.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/feature_design.schema.json",
        target / "schemas/feature_design.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/instruction_manifest.schema.json",
        target / "schemas/instruction_manifest.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/project_verification.schema.json",
        target / "schemas/project_verification.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/project_verification_result.schema.json",
        target / "schemas/project_verification_result.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/readiness_state.schema.json",
        target / "schemas/readiness_state.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    for schema_name in (
        "audited_run_manifest.schema.json",
        "audited_state.schema.json",
        "audited_round_contract.schema.json",
        "audited_executor_report.schema.json",
        "audited_audit_report.schema.json",
        "audited_run_result.schema.json",
    ):
        copy_binary_or_text_file(
            PLAYBOOK_ROOT / "schemas" / schema_name,
            target / "schemas" / schema_name,
            args.force,
            args.dry_run,
            result,
        )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/delivery_execution_model.schema.json",
        target / "schemas/delivery_execution_model.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/release_readiness_result.schema.json",
        target / "schemas/release_readiness_result.schema.json",
        args.force,
        args.dry_run,
        result,
    )


def add_lean_core_files(args: argparse.Namespace, target: Path, replacements: dict[str, str], result: CopyResult) -> None:
    copy_file("templates/TASKS.md", target / "docs/tasks.md", replacements, args.force, args.dry_run, result)
    copy_file("templates/FEATURE_DESIGN.md", target / "templates/FEATURE_DESIGN.md", replacements, args.force, args.dry_run, result)
    copy_file("templates/INSTRUCTION_MANIFEST.json", target / "templates/INSTRUCTION_MANIFEST.json", replacements, args.force, args.dry_run, result)
    copy_file("templates/CONTRACT_LITE.md", target / "docs/CONTRACT_LITE.md", replacements, args.force, args.dry_run, result)
    copy_file("templates/AGENTS.md", target / "AGENTS.md", replacements, args.force, args.dry_run, result)
    write_text_file(
        target / "docs/PROBLEM_FIT.md",
        problem_fit_note(replacements),
        force=args.force,
        dry_run=args.dry_run,
        result=result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/integrity_check.py",
        target / "tools/integrity_check.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/playbook_validate.py",
        target / "tools/playbook_validate.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/feature_design_lib.py",
        target / "tools/feature_design_lib.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/planning_depth.py",
        target / "tools/planning_depth.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/create_feature_design.py",
        target / "tools/create_feature_design.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/validate_feature_design.py",
        target / "tools/validate_feature_design.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/render_slice_context.py",
        target / "tools/render_slice_context.py",
        args.force,
        args.dry_run,
        result,
    )
    for tool_name in (
        "approve_feature_design.py",
        "feature_review_policy.py",
        "feature_workflow.py",
        "receipt_run.py",
    ):
        copy_binary_or_text_file(
            PLAYBOOK_ROOT / "tools" / tool_name,
            target / "tools" / tool_name,
            args.force,
            args.dry_run,
            result,
        )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/check_maintainability.py",
        target / "tools/check_maintainability.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/render_codex_exec_prompt.py",
        target / "tools/render_codex_exec_prompt.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/resolve_release_readiness.py",
        target / "tools/resolve_release_readiness.py",
        args.force,
        args.dry_run,
        result,
    )
    write_text_file(
        target / "tools/verify_project.py",
        verify_project_script(),
        force=args.force,
        dry_run=args.dry_run,
        result=result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/task.schema.json",
        target / "schemas/task.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/feature_design.schema.json",
        target / "schemas/feature_design.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/instruction_manifest.schema.json",
        target / "schemas/instruction_manifest.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/project_verification.schema.json",
        target / "schemas/project_verification.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/project_verification_result.schema.json",
        target / "schemas/project_verification_result.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/readiness_state.schema.json",
        target / "schemas/readiness_state.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/delivery_execution_model.schema.json",
        target / "schemas/delivery_execution_model.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/release_readiness_result.schema.json",
        target / "schemas/release_readiness_result.schema.json",
        args.force,
        args.dry_run,
        result,
    )


def add_lean_files(args: argparse.Namespace, target: Path, replacements: dict[str, str], result: CopyResult) -> None:
    copy_file("templates/CONTRACT_LITE.md", target / "docs/CONTRACT_LITE.md", replacements, args.force, args.dry_run, result)
    copy_file("templates/LEAN_CODEX_PROMPT.md", target / "AGENTS.md", replacements, args.force, args.dry_run, result)
    copy_file("templates/LEAN_REVIEW_CHECKLIST.md", target / "docs/LEAN_REVIEW_CHECKLIST.md", replacements, args.force, args.dry_run, result)


def add_standard_files(args: argparse.Namespace, target: Path, replacements: dict[str, str], result: CopyResult) -> None:
    copy_file("PLAYBOOK.md", target / "PLAYBOOK.md", replacements, args.force, args.dry_run, result)
    copy_file("templates/ARCHITECTURE.md", target / "docs/ARCHITECTURE.md", replacements, args.force, args.dry_run, result)
    copy_file(
        "templates/IMPLEMENTATION_CONTRACT.md",
        target / "docs/IMPLEMENTATION_CONTRACT.md",
        replacements,
        args.force,
        args.dry_run,
        result,
    )
    copy_file("templates/CODEX_PROMPT.md", target / "docs/CODEX_PROMPT.md", replacements, args.force, args.dry_run, result)
    copy_file("templates/DECISION_LOG.md", target / "docs/DECISION_LOG.md", replacements, args.force, args.dry_run, result)
    copy_file(
        "templates/IMPLEMENTATION_JOURNAL.md",
        target / "docs/IMPLEMENTATION_JOURNAL.md",
        replacements,
        args.force,
        args.dry_run,
        result,
    )
    copy_file("templates/EVIDENCE_INDEX.md", target / "docs/EVIDENCE_INDEX.md", replacements, args.force, args.dry_run, result)
    copy_file("ci/ci.yml", target / ".github/workflows/ci.yml", replacements, args.force, args.dry_run, result)
    copy_prompt_files(target / "docs/prompts", replacements, args.force, args.dry_run, result)
    copy_rendered_tree("prompts/audit", target / "docs/audit", replacements, args.force, args.dry_run, result)
    copy_tree("hooks", target / "hooks", args.force, args.dry_run, result)
    if not args.dry_run:
        for hook in (target / "hooks").glob("*.sh"):
            chmod_executable(hook)


def hook_commands(settings: dict[str, object]) -> list[str]:
    commands: list[str] = []
    hooks = settings.get("hooks", {})
    if not isinstance(hooks, dict):
        return commands
    for entries in hooks.values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            for hook in entry.get("hooks", []):
                if isinstance(hook, dict) and isinstance(hook.get("command"), str):
                    commands.append(hook["command"])
    return commands


def merge_settings(existing: dict[str, object], incoming: dict[str, object]) -> dict[str, object]:
    merged = dict(existing)
    existing_hooks = merged.setdefault("hooks", {})
    incoming_hooks = incoming.get("hooks", {})
    if not isinstance(existing_hooks, dict) or not isinstance(incoming_hooks, dict):
        merged["hooks"] = incoming_hooks
        return merged

    for event, incoming_entries in incoming_hooks.items():
        if not isinstance(incoming_entries, list):
            continue
        current_entries = existing_hooks.setdefault(event, [])
        if not isinstance(current_entries, list):
            existing_hooks[event] = incoming_entries
            continue
        seen = {
            json.dumps(entry, sort_keys=True)
            for entry in current_entries
            if isinstance(entry, dict)
        }
        for entry in incoming_entries:
            key = json.dumps(entry, sort_keys=True)
            if key not in seen:
                current_entries.append(entry)
                seen.add(key)
    return merged


def install_claude_hooks(args: argparse.Namespace, target: Path, result: CopyResult) -> tuple[list[str], bool]:
    messages: list[str] = []
    failed = False
    template_path = PLAYBOOK_ROOT / "templates/.claude/settings.json"
    settings = json.loads(template_path.read_text(encoding="utf-8"))
    settings_path = target / ".claude/settings.json"

    if settings_path.exists():
        existing = json.loads(settings_path.read_text(encoding="utf-8"))
        settings = merge_settings(existing, settings)

    write_text_file(
        settings_path,
        json.dumps(settings, indent=2, sort_keys=True) + "\n",
        force=True,
        dry_run=args.dry_run,
        result=result,
    )

    for command in hook_commands(settings):
        if not command.startswith("./hooks/"):
            continue
        hook_name = Path(command).name
        source = PLAYBOOK_ROOT / "hooks" / hook_name
        if source.exists():
            copy_binary_or_text_file(source, target / "hooks" / hook_name, args.force, args.dry_run, result)

    if not args.dry_run:
        for hook in (target / "hooks").glob("*.sh"):
            chmod_executable(hook)
        smoke_hook = target / "hooks" / "guard_files.sh"
        if smoke_hook.exists():
            smoke = subprocess.run(
                [str(smoke_hook)],
                input=json.dumps({"tool_input": {"file_path": "docs/README.md"}}),
                text=True,
                cwd=target,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if smoke.returncode != 0:
                failed = True
                messages.append(
                    "hook smoke test failed: "
                    + (smoke.stderr.strip() or smoke.stdout.strip() or str(smoke.returncode))
                )
            else:
                messages.append("hook smoke test passed")
        else:
            failed = True
            messages.append("hook smoke test skipped: guard_files.sh not installed")
    return messages, failed


def add_optional_files(args: argparse.Namespace, target: Path, replacements: dict[str, str], result: CopyResult) -> None:
    if args.with_cost_architecture:
        copy_file(
            "templates/COST_ARCHITECTURE.md",
            target / "docs/ai_cost_architecture.md",
            replacements,
            args.force,
            args.dry_run,
            result,
        )
    if args.with_router_eval:
        copy_file("templates/ROUTER_EVAL.md", target / "docs/router_eval.md", replacements, args.force, args.dry_run, result)
    if args.with_cost_adapter:
        copy_tree("templates/cost_adapters", target / "templates/cost_adapters", args.force, args.dry_run, result)
        copy_file(
            "templates/COST_TELEMETRY_ADAPTER.md",
            target / "docs/COST_TELEMETRY_ADAPTER.md",
            replacements,
            args.force,
            args.dry_run,
            result,
        )
    for skill_name in args.external_skill:
        slug = skill_name.strip().lower().replace(" ", "-")
        if not slug:
            continue
        skill_replacements = dict(replacements)
        skill_replacements["SKILL_NAME"] = skill_name
        copy_file(
            "templates/EXTERNAL_SKILL_TRUST_RECORD.md",
            target / f"docs/security/skills/{slug}/TRUST_RECORD.md",
            skill_replacements,
            args.force,
            args.dry_run,
            result,
        )


def add_rag_eval_files(args: argparse.Namespace, target: Path, replacements: dict[str, str], result: CopyResult) -> None:
    if not args.with_rag_eval:
        return
    for schema_name in (
        "rag_eval_manifest.schema.json",
        "rag_eval_case.schema.json",
        "rag_eval_observation.schema.json",
        "rag_eval_result.schema.json",
        "rag_eval_comparison.schema.json",
    ):
        copy_binary_or_text_file(
            PLAYBOOK_ROOT / "schemas" / schema_name,
            target / "schemas" / schema_name,
            args.force,
            args.dry_run,
            result,
        )
    for tool_name in (
        "rag_eval_lib.py",
        "rag_eval_validate.py",
        "rag_eval_score.py",
        "rag_eval_compare.py",
    ):
        copy_binary_or_text_file(
            PLAYBOOK_ROOT / "tools" / tool_name,
            target / "tools" / tool_name,
            args.force,
            args.dry_run,
            result,
        )
    copy_file(
        "templates/RAG_DATA_READINESS.md",
        target / "docs/rag_data_readiness.md",
        replacements,
        args.force,
        args.dry_run,
        result,
    )
    copy_file(
        "templates/RETRIEVAL_EVAL.md",
        target / "docs/retrieval_eval.md",
        replacements,
        args.force,
        args.dry_run,
        result,
    )
    write_text_file(
        target / ".playbook/rag_eval_manifest.json",
        rag_eval_manifest_config(),
        force=args.force,
        dry_run=args.dry_run,
        result=result,
    )
    write_text_file(
        target / ".playbook/rag_eval_cases.jsonl",
        rag_eval_case_jsonl(),
        force=args.force,
        dry_run=args.dry_run,
        result=result,
    )
    write_text_file(
        target / ".playbook/rag_eval_corpus_snapshot.txt",
        rag_eval_corpus_snapshot(),
        force=args.force,
        dry_run=args.dry_run,
        result=result,
    )
    write_text_file(
        target / ".playbook/rag_eval_baseline_observations.jsonl",
        rag_eval_observations_jsonl("lexical_baseline", "scaffold-baseline-run"),
        force=args.force,
        dry_run=args.dry_run,
        result=result,
    )
    write_text_file(
        target / ".playbook/rag_eval_candidate_observations.jsonl",
        rag_eval_observations_jsonl("production_candidate", "scaffold-candidate-run"),
        force=args.force,
        dry_run=args.dry_run,
        result=result,
    )
    if not args.dry_run:
        (target / "reports/rag_eval").mkdir(parents=True, exist_ok=True)
        (target / ".playbook-artifacts/rag-eval").mkdir(parents=True, exist_ok=True)


def add_feature_design_scaffold(args: argparse.Namespace, target: Path, replacements: dict[str, str], result: CopyResult) -> None:
    if args.planning_depth == "oneshot":
        return
    design_replacements = dict(replacements)
    design_replacements.update(
        {
            "DATE": replacements["DATE"],
        }
    )
    markdown = render(read_template("templates/FEATURE_DESIGN.md"), design_replacements)
    markdown = (
        markdown.replace("Feature-ID:\n", "Feature-ID: F01\n")
        .replace("Planning-Depth:\n", f"Planning-Depth: {args.planning_depth}\n")
        .replace("Owner:\n", "Owner: human\n")
        .replace("Risk-Level:\n", f"Risk-Level: {args.risk_level}\n")
    )
    write_text_file(
        target / "docs/design/F01.md",
        markdown,
        force=args.force,
        dry_run=args.dry_run,
        result=result,
    )
    write_text_file(
        target / "docs/design/F01.design.json",
        feature_design_registry_config(args.planning_depth, args.risk_level),
        force=args.force,
        dry_run=args.dry_run,
        result=result,
    )


def recommend_or_declared_planning_depth(args: argparse.Namespace) -> tuple[str, str, list[str]]:
    if args.planning_depth != "recommend":
        return args.planning_depth, "declared", []
    if planning_depth_rules is None:
        return "compact_design", "recommended", ["planning_depth.py unavailable; defaulted to compact_design"]
    recommendation = planning_depth_rules.recommend_planning_depth(
        risk_level=args.risk_level,
        estimated_components=args.estimated_components,
        expected_file_count=args.expected_file_count,
        api_change=args.api_change,
        persistence_change=args.persistence_change,
        security_change=args.security_change,
        rag_or_agentic=args.rag_or_agentic,
        migration_required=args.migration_required,
        user_visible_feature=args.user_visible_feature,
    )
    return str(recommendation["recommended_planning_depth"]), "recommended", list(recommendation["reasons"])


def repository_inventory(target: Path) -> str:
    skip = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules", ".playbook-artifacts"}
    files: list[str] = []
    for path in sorted(target.rglob("*")):
        if path.is_dir() or any(part in skip for part in path.relative_to(target).parts):
            continue
        files.append(str(path.relative_to(target)))
    payload = {
        "schema_version": "playbook.repository_inventory.v1",
        "file_count": len(files),
        "sample_files": files[:200],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def retrofit_plan_text(project_name: str, mode: str, planning_depth: str, reasons: list[str]) -> str:
    reason_lines = "\n".join(f"- {reason}" for reason in reasons) if reasons else "- declared by operator"
    return f"""# Playbook Retrofit Plan

Project: {project_name}
Mode: {mode}
Planning-Depth: {planning_depth}

## Recommendation Basis

{reason_lines}

## Migration Strategy

- Existing files are preserved unless `--force` is explicitly used.
- Application code is not generated or rewritten by this initializer.
- The repository inventory is recorded at `.playbook/repository_inventory.json`.
- If Planning Depth requires design, complete and approve `docs/design/F01.md`
  with companion registry `docs/design/F01.design.json` before implementation.
- Run `python3 tools/playbook_validate.py --root .` to see remaining contract
  and readiness findings.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap a project with AI Workflow Playbook artifacts.")
    parser.add_argument("target", help="Target repository directory.")
    parser.add_argument("--mode", choices=("lean-core", "lean", "standard", "strict"), default="standard")
    parser.add_argument("--planning-depth", choices=("oneshot", "compact_design", "designed_slices", "recommend"), default="oneshot")
    parser.add_argument("--risk-level", choices=("low", "medium", "high", "critical"), default="medium")
    parser.add_argument("--expected-file-count", type=int, default=1)
    parser.add_argument("--estimated-components", type=int, default=1)
    parser.add_argument("--api-change", action="store_true")
    parser.add_argument("--persistence-change", action="store_true")
    parser.add_argument("--security-change", action="store_true")
    parser.add_argument("--rag-or-agentic", action="store_true")
    parser.add_argument("--migration-required", action="store_true")
    parser.add_argument("--user-visible-feature", action="store_true")
    parser.add_argument("--project-name", default="")
    parser.add_argument("--retrofit", action="store_true", help="Record repository inventory and retrofit migration plan without overwriting existing files by default.")
    parser.add_argument("--answers-file", help="JSON file with initializer readiness answers.")
    parser.add_argument("--operational-pain", default="")
    parser.add_argument("--current-workaround", default="")
    parser.add_argument("--first-proof-metric", default="")
    parser.add_argument(
        "--verify-argv",
        action="append",
        default=[],
        help='Required project verification check as a JSON argv array, e.g. \'["{python}", "-m", "pytest", "-q"]\'. Repeat for multiple checks.',
    )
    parser.add_argument(
        "--verify-command",
        default="",
        help="Deprecated display-only shell command. Use --verify-argv so generated verification can execute without shell parsing.",
    )
    parser.add_argument("--with-cost-architecture", action="store_true")
    parser.add_argument("--with-router-eval", action="store_true")
    parser.add_argument("--with-rag-eval", action="store_true", help="Add optional portable RAG eval schemas, CLI tools, and mechanism fixture.")
    parser.add_argument("--with-cost-adapter", action="store_true")
    parser.add_argument("--external-skill", action="append", default=[], help="Create trust record for this external skill.")
    parser.add_argument("--install-claude-hooks", action="store_true", help="Merge .claude/settings.json and install hook scripts.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.answers_file:
        answers = json.loads(Path(args.answers_file).read_text(encoding="utf-8"))
        for attr in ("operational_pain", "current_workaround", "first_proof_metric"):
            if not getattr(args, attr) and attr in answers:
                setattr(args, attr, str(answers[attr]))
    verify_argvs, verify_errors = parse_verify_argv(args.verify_argv)
    if args.verify_command and not verify_argvs:
        verify_errors.append("--verify-command is not enforced; provide --verify-argv with a JSON argv array instead")
    if not verify_argvs:
        verify_errors.append("--verify-argv is required so generated verify_project.py can run actual project verification")
    readiness_errors = validate_required_readiness(args)
    if readiness_errors or verify_errors:
        for error in [*readiness_errors, *verify_errors]:
            print(f"init_playbook_project: {error}", file=sys.stderr)
        return 2
    target = Path(args.target).resolve()
    project_name = args.project_name or target.name
    mode = "lean-core" if args.mode == "lean" else args.mode
    resolved_planning_depth, planning_depth_source, planning_reasons = recommend_or_declared_planning_depth(args)
    args.planning_depth = resolved_planning_depth
    today = dt.date.today().isoformat()
    replacements = {
        "PROJECT_NAME": project_name,
        "MODE": mode,
        "DATE": today,
        "VERIFY_COMMAND": display_verify_commands(verify_argvs),
        "OPERATIONAL_PAIN": readiness_value(args.operational_pain),
        "CURRENT_WORKAROUND": readiness_value(args.current_workaround),
        "FIRST_PROOF_METRIC": readiness_value(args.first_proof_metric),
        "PYTHON_VERSION": "3.12",
        "APP_DIR": "app",
        "APP_MODULE": "app.main",
        "ENV_VAR_1": "TEST_ENV",
        "TEST_VALUE_1": "test",
        "ENV_VAR_2": "TEST_MODE",
        "TEST_VALUE_2": "true",
        "MAX_TOTAL_COST_USD": "25",
        "MAX_RUN_COST_USD": "2",
    }

    result = CopyResult(created=[], skipped=[])
    if not args.dry_run:
        target.mkdir(parents=True, exist_ok=True)

    hook_messages: list[str] = []
    hook_failed = False
    if mode == "lean-core":
        add_lean_core_files(args, target, replacements, result)
    else:
        add_common_files(args, target, replacements, result)
    if args.mode == "lean":
        add_lean_files(args, target, replacements, result)
    elif mode != "lean-core":
        add_standard_files(args, target, replacements, result)
        if mode == "strict":
            args.with_cost_architecture = True
    add_optional_files(args, target, replacements, result)
    add_rag_eval_files(args, target, replacements, result)
    add_feature_design_scaffold(args, target, replacements, result)
    project_verification_text = project_verification_config(verify_argvs)
    if args.with_rag_eval:
        project_verification_text = add_rag_eval_project_check(project_verification_text)
    write_text_file(
        target / ".playbook/project_verification.json",
        project_verification_text,
        force=args.force,
        dry_run=args.dry_run,
        result=result,
    )
    write_text_file(
        target / ".playbook/readiness_state.json",
        readiness_state_config(mode, args.planning_depth, args.risk_level, planning_depth_source),
        force=args.force,
        dry_run=args.dry_run,
        result=result,
    )
    write_text_file(
        target / ".playbook/delivery_execution_model.json",
        delivery_execution_model_config(),
        force=args.force,
        dry_run=args.dry_run,
        result=result,
    )
    write_text_file(
        target / ".playbook/instruction_manifest.json",
        render(read_template("templates/INSTRUCTION_MANIFEST.json"), replacements),
        force=args.force,
        dry_run=args.dry_run,
        result=result,
    )
    if args.retrofit:
        write_text_file(
            target / ".playbook/repository_inventory.json",
            repository_inventory(target),
            force=args.force,
            dry_run=args.dry_run,
            result=result,
        )
        write_text_file(
            target / "docs/playbook_retrofit_plan.md",
            retrofit_plan_text(project_name, mode, args.planning_depth, planning_reasons),
            force=args.force,
            dry_run=args.dry_run,
            result=result,
        )
    if args.install_claude_hooks:
        hook_messages, hook_failed = install_claude_hooks(args, target, result)

    print(f"init_playbook_project: target={target}")
    print(f"init_playbook_project: mode={mode}")
    print(f"init_playbook_project: planning_depth={args.planning_depth} source={planning_depth_source}")
    for path in result.created:
        print(f"  create: {path}")
    for path in result.skipped:
        print(f"  skip existing: {path}")
    for message in hook_messages:
        print(f"  hooks: {message}")
    if args.planning_depth in {"compact_design", "designed_slices"}:
        print("init_playbook_project: next=python tools/feature_workflow.py --root . draft --task <task-id> --feature-id F01")
    print(f"init_playbook_project: created={len(result.created)} skipped={len(result.skipped)}")
    return 1 if args.install_claude_hooks and hook_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
