from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .adapters.command import CommandAdapter
from .adapters.scripted import ScriptedAdapter
from .deepseek_runtime import DSH_EXPECTED_VERSION, DeepSeekRuntimeError, default_profile_path, doctor as deepseek_doctor
from .deepseek_screening import DEFAULT_OUTPUT as DSH_DEFAULT_OUTPUT, DEFAULT_SUITE as DSH_DEFAULT_SUITE, ScreeningConfig, ScreeningError, run_screening
from .audited_execution import build_audited_parser, handle_audited_command
from .changeability import ChangeabilityError, run_changeability_suite
from .comparison import compare
from .evidence import verify_bundle
from .runner import RunError, run_suite
from .suite_loader import SuiteError, load_suite


def nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be nonnegative")
    return parsed


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def missing_identity_flags(values: dict[str, str]) -> list[str]:
    invalid_values = {"unknown", "tbd", "todo", "placeholder", "not_applicable"}
    missing: list[str] = []
    for flag, value in values.items():
        normalized = value.strip().lower()
        if not normalized or normalized in invalid_values or "placeholder" in normalized:
            missing.append(flag)
    return missing


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harness-lab")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate-suite")
    validate.add_argument("suite_path")

    run = sub.add_parser("run")
    run.add_argument("--suite", required=True)
    run.add_argument("--condition", required=True, choices=("baseline", "playbook"))
    run.add_argument("--adapter", required=True, choices=("scripted", "command", "deepseek-harness"))
    run.add_argument("--command-template", default="")
    run.add_argument("--adapter-timeout", type=float, default=None)
    run.add_argument("--trials", type=positive_int, default=1)
    run.add_argument("--trial-start", type=nonnegative_int, default=0)
    run.add_argument("--task-id", action="append", default=None)
    run.add_argument("--append", action="store_true")
    run.add_argument("--output", required=True)
    run.add_argument("--fail-on-invalid-run", action="store_true")
    run.add_argument("--empirical-comparison", action="store_true")
    run.add_argument("--provider", default="")
    run.add_argument("--model-id", default="")
    run.add_argument("--cli-version", default="")
    run.add_argument("--reasoning-profile", default="")
    run.add_argument("--permission-policy", default="")
    run.add_argument("--delivery-profile", default="")
    run.add_argument("--dsh-profile", type=Path, default=default_profile_path())
    run.add_argument("--dsh-max-tokens", type=positive_int, default=32768)
    run.add_argument("--dsh-request-timeout", type=float, default=900.0)
    run.add_argument("--dsh-expected-version", default=DSH_EXPECTED_VERSION)
    run.add_argument("--dsh-input-price-per-million", type=float, default=None)
    run.add_argument("--dsh-output-price-per-million", type=float, default=None)

    verify = sub.add_parser("verify-bundle")
    verify.add_argument("bundle_path")

    cmp_parser = sub.add_parser("compare")
    cmp_parser.add_argument("--baseline", required=True)
    cmp_parser.add_argument("--candidate", required=True)
    cmp_parser.add_argument("--output", required=True)
    cmp_parser.add_argument("--fail-on-invalid-run", action="store_true")
    cmp_parser.add_argument("--fail-on-hard-gate", action="store_true")
    cmp_parser.add_argument("--max-policy-violations", type=int, default=0)
    cmp_parser.add_argument("--max-false-success-rate", type=float, default=0.0)
    cmp_parser.add_argument("--min-trials-per-task", type=positive_int, default=2)
    cmp_parser.add_argument("--require-empirical", action="store_true")

    changeability = sub.add_parser("changeability-run")
    changeability.add_argument("--suite", required=True)
    changeability.add_argument("--output", required=True)
    build_audited_parser(sub)

    dsh_doctor = sub.add_parser("dsh-doctor")
    dsh_doctor.add_argument("--profile", type=Path, default=default_profile_path())
    dsh_doctor.add_argument("--expected-version", default=DSH_EXPECTED_VERSION)
    dsh_doctor.add_argument("--require-credential", action="store_true")

    dsh_screening = sub.add_parser("dsh-screening")
    dsh_screening.add_argument("--suite", type=Path, default=DSH_DEFAULT_SUITE)
    dsh_screening.add_argument("--output", type=Path, default=DSH_DEFAULT_OUTPUT)
    dsh_screening.add_argument("--trials", type=positive_int, default=3)
    dsh_screening.add_argument("--provider", default="deepseek-official")
    dsh_screening.add_argument("--model-id", default="deepseek-v4-flash")
    dsh_screening.add_argument("--profile", type=Path, default=default_profile_path())
    dsh_screening.add_argument("--max-tokens", type=positive_int, default=32768)
    dsh_screening.add_argument("--request-timeout", type=float, default=900.0)
    dsh_screening.add_argument("--reasoning-profile", default="high")
    dsh_screening.add_argument("--expected-version", default=DSH_EXPECTED_VERSION)
    dsh_screening.add_argument("--input-price-per-million", type=float, default=None)
    dsh_screening.add_argument("--output-price-per-million", type=float, default=None)
    dsh_screening.add_argument("--resume", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "validate-suite":
        try:
            suite = load_suite(Path(args.suite_path))
        except SuiteError as exc:
            print(f"validate-suite: failed: {exc}", file=sys.stderr)
            return 1
        print(json.dumps({"suite_id": suite.suite_id, "version": suite.version, "tasks": len(suite.tasks)}, indent=2))
        return 0

    if args.command == "run":
        suite = load_suite(Path(args.suite))
        empirical_required = {
            "--provider": args.provider,
            "--model-id": args.model_id,
            "--cli-version": args.cli_version,
            "--reasoning-profile": args.reasoning_profile,
            "--permission-policy": args.permission_policy,
            "--delivery-profile": args.delivery_profile,
        }
        if args.empirical_comparison:
            if args.adapter == "scripted":
                print("empirical comparison requires the command adapter; scripted adapter is mechanism-only", file=sys.stderr)
                return 2
            missing = missing_identity_flags(empirical_required)
            if missing:
                print(f"empirical comparison requires explicit identity flags: {', '.join(missing)}", file=sys.stderr)
                return 2
        identity_complete = not missing_identity_flags(empirical_required)
        metadata = {
            "model": {
                "provider": args.provider or "unknown",
                "id": args.model_id or "unknown",
                "parameters": args.reasoning_profile or "unknown",
            },
            "cli_version": args.cli_version or "unknown",
            "reasoning_profile": args.reasoning_profile or "unknown",
            "permission_policy_version": args.permission_policy or "adapter_default.v1",
            "delivery_profile": args.delivery_profile or "harness_lab_single_adapter",
            "empirical_comparison": args.empirical_comparison,
            "evaluation_mode": "empirical" if args.empirical_comparison else "mechanism_demonstration",
            "identity_source": "declared" if identity_complete else "unknown",
        }
        if args.adapter == "scripted":
            adapter = ScriptedAdapter(metadata)
        elif args.adapter == "command":
            if not args.command_template:
                print("--command-template is required for command adapter", file=sys.stderr)
                return 2
            adapter = CommandAdapter(args.command_template, timeout=args.adapter_timeout, metadata=metadata)
        else:
            if not args.empirical_comparison:
                print("deepseek-harness adapter requires --empirical-comparison", file=sys.stderr)
                return 2
            from .adapters.deepseek_harness import DeepSeekHarnessAdapter

            adapter = DeepSeekHarnessAdapter(
                provider=args.provider,
                model_id=args.model_id,
                profile_path=args.dsh_profile,
                max_tokens=args.dsh_max_tokens,
                request_timeout_seconds=args.dsh_request_timeout,
                reasoning_profile=args.reasoning_profile,
                permission_policy=args.permission_policy or "workspace-write",
                delivery_profile=args.delivery_profile or "harness_lab_deepseek_single_agent",
                expected_version=args.dsh_expected_version,
                input_price_per_million=args.dsh_input_price_per_million,
                output_price_per_million=args.dsh_output_price_per_million,
            )
        try:
            results = run_suite(
                suite,
                args.condition,
                adapter,
                args.trials,
                Path(args.output),
                trial_start=args.trial_start,
                task_ids=args.task_id,
                append=args.append,
            )
        except (RunError, DeepSeekRuntimeError) as exc:
            print(f"run: failed: {exc}", file=sys.stderr)
            return 1
        invalid = [result for result in results if not result.valid]
        print(
            json.dumps(
                {
                    "bundles": [str(result.bundle_path) for result in results],
                    "trials": len(results),
                    "invalid_runs": len(invalid),
                },
                indent=2,
            )
        )
        if args.fail_on_invalid_run and invalid:
            return 1
        return 0

    if args.command == "verify-bundle":
        errors = verify_bundle(Path(args.bundle_path))
        if errors:
            for error in errors:
                print(f"error: {error}", file=sys.stderr)
            return 1
        print("verify-bundle: ok")
        return 0

    if args.command == "compare":
        report = compare(
            Path(args.baseline),
            Path(args.candidate),
            Path(args.output),
            minimum_trials_per_task=args.min_trials_per_task,
            require_empirical=args.require_empirical,
        )
        print(json.dumps({"output": str(Path(args.output)), "status": report["status"]}, indent=2))
        if report.get("blocking_errors"):
            return 1
        if args.fail_on_invalid_run and (
            report["baseline"]["invalid_runs"] or report["candidate"]["invalid_runs"] or report["compatibility_errors"]
        ):
            return 1
        if args.fail_on_hard_gate:
            gates = report["hard_gates"]
            if gates["candidate_policy_violation_count"] > args.max_policy_violations:
                return 1
            if gates["candidate_false_success_rate"] > args.max_false_success_rate:
                return 1
        return 0

    if args.command == "changeability-run":
        try:
            report = run_changeability_suite(Path(args.suite), Path(args.output))
        except (OSError, json.JSONDecodeError, ChangeabilityError) as exc:
            print(f"changeability-run: failed: {exc}", file=sys.stderr)
            return 1
        print(json.dumps({"output": str(Path(args.output)), "status": report["status"]}, indent=2))
        return 0

    if args.command == "dsh-doctor":
        report = deepseek_doctor(
            profile_path=args.profile,
            require_credential=args.require_credential,
            expected_version=args.expected_version,
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "pass" else 1

    if args.command == "dsh-screening":
        try:
            code, report = run_screening(
                ScreeningConfig(
                    suite_path=args.suite,
                    output_root=args.output,
                    trials=args.trials,
                    provider=args.provider,
                    model_id=args.model_id,
                    profile_path=args.profile,
                    max_tokens=args.max_tokens,
                    request_timeout_seconds=args.request_timeout,
                    reasoning_profile=args.reasoning_profile,
                    expected_version=args.expected_version,
                    input_price_per_million=args.input_price_per_million,
                    output_price_per_million=args.output_price_per_million,
                    resume=args.resume,
                )
            )
        except ScreeningError as exc:
            print(f"dsh-screening: failed: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(report, indent=2, sort_keys=True))
        return code

    if args.command == "audited-run":
        return handle_audited_command(args)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
