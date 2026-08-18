#!/usr/bin/env python3
"""Run or verify a bounded Codex reviewer role through the Playbook harness."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from codex_role_run_lib import (
    ROLE_SPECS,
    RoleRunError,
    execute_role_run,
    validate_role_result,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize a role-scoped prompt, run a fresh read-only codex exec, "
            "and emit tamper-evident evidence."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="execute one guarded reviewer role")
    run_parser.add_argument("--root", type=Path, default=Path("."))
    run_parser.add_argument("--task", required=True)
    run_parser.add_argument("--feature-id")
    run_parser.add_argument("--slice-id")
    run_parser.add_argument("--role", choices=sorted(ROLE_SPECS), required=True)
    run_parser.add_argument("--codex-bin")
    run_parser.add_argument("--model")
    run_parser.add_argument("--timeout-seconds", type=int, default=900)
    run_parser.add_argument("--run-id")
    run_parser.add_argument(
        "--output-report",
        type=Path,
        help=(
            "repository-relative publication path; defaults to "
            ".playbook-artifacts/reports/<feature>/<role>.md"
        ),
    )
    run_parser.add_argument(
        "--no-publish",
        action="store_true",
        help="keep the validated report only inside the immutable run directory",
    )

    verify_parser = subparsers.add_parser("verify", help="revalidate a saved role result")
    verify_parser.add_argument("--root", type=Path, default=Path("."))
    verify_parser.add_argument("--result", type=Path, required=True)
    verify_parser.add_argument(
        "--allow-head-drift",
        action="store_true",
        help="verify artifact integrity without requiring the current Git HEAD",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "run":
            result, result_path = execute_role_run(
                root=args.root,
                task_id=args.task,
                role=args.role,
                feature_id=args.feature_id,
                slice_id=args.slice_id,
                codex_binary=args.codex_bin,
                model=args.model,
                timeout_seconds=args.timeout_seconds,
                run_id=args.run_id,
                output_report=args.output_report,
                publish=not args.no_publish,
            )
            print(
                json.dumps(
                    {
                        "status": result["status"],
                        "verdict": result.get("verdict"),
                        "run_id": result["run_id"],
                        "result": result_path.resolve().as_posix(),
                        "errors": result["postflight"]["errors"],
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0 if result["status"] == "validated" else 1

        payload = validate_role_result(
            root=args.root,
            result_path=args.result,
            require_current_head=not args.allow_head_drift,
        )
        print(
            json.dumps(
                {
                    "status": "valid",
                    "run_id": payload["run_id"],
                    "role": payload["role"],
                    "verdict": payload.get("verdict"),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    except (RoleRunError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
