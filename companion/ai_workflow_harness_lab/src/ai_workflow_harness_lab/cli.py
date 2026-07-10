from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .adapters.command import CommandAdapter
from .adapters.scripted import ScriptedAdapter
from .comparison import compare
from .evidence import verify_bundle
from .runner import run_suite
from .suite_loader import SuiteError, load_suite


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harness-lab")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate-suite")
    validate.add_argument("suite_path")

    run = sub.add_parser("run")
    run.add_argument("--suite", required=True)
    run.add_argument("--condition", required=True, choices=("baseline", "playbook"))
    run.add_argument("--adapter", required=True, choices=("scripted", "command"))
    run.add_argument("--command-template", default="")
    run.add_argument("--trials", type=int, default=1)
    run.add_argument("--output", required=True)

    verify = sub.add_parser("verify-bundle")
    verify.add_argument("bundle_path")

    cmp_parser = sub.add_parser("compare")
    cmp_parser.add_argument("--baseline", required=True)
    cmp_parser.add_argument("--candidate", required=True)
    cmp_parser.add_argument("--output", required=True)
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
        if args.adapter == "scripted":
            adapter = ScriptedAdapter()
        else:
            if not args.command_template:
                print("--command-template is required for command adapter", file=sys.stderr)
                return 2
            adapter = CommandAdapter(args.command_template)
        results = run_suite(suite, args.condition, adapter, args.trials, Path(args.output))
        print(json.dumps({"bundles": [str(result.bundle_path) for result in results], "trials": len(results)}, indent=2))
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
        report = compare(Path(args.baseline), Path(args.candidate), Path(args.output))
        print(json.dumps({"output": str(Path(args.output)), "status": report["status"]}, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
