#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS_SRC = ROOT / "companion/ai_workflow_harness_lab/src"
if str(HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(HARNESS_SRC))

from ai_workflow_harness_lab.deepseek_runtime import default_profile_path  # noqa: E402
from ai_workflow_harness_lab.deepseek_screening import (  # noqa: E402
    DEFAULT_OUTPUT,
    DEFAULT_SUITE,
    ScreeningConfig,
    ScreeningError,
    run_screening,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run or resume the DeepSeek Harness empirical screening")
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--provider", default="deepseek-official")
    parser.add_argument("--model-id", default="deepseek-v4-flash")
    parser.add_argument("--profile", type=Path, default=default_profile_path())
    parser.add_argument("--max-tokens", type=int, default=32768)
    parser.add_argument("--request-timeout", type=float, default=900.0)
    parser.add_argument("--reasoning-profile", default="high")
    parser.add_argument("--input-price-per-million", type=float, default=None)
    parser.add_argument("--output-price-per-million", type=float, default=None)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        code, result = run_screening(
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
                input_price_per_million=args.input_price_per_million,
                output_price_per_million=args.output_price_per_million,
                resume=args.resume,
            )
        )
    except ScreeningError as exc:
        print(f"deepseek screening failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
