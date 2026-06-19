"""Provider-neutral AI cost telemetry adapter.

Copy this file into a downstream project, usually as `app/ai/telemetry.py`.
Route all LLM/provider calls through a project-owned boundary and call
`write_telemetry_entry` or `call_with_telemetry` from that boundary.

This template avoids provider imports on purpose. It extracts common usage
fields from dict-like or object-like responses returned by OpenAI, Anthropic,
gateway wrappers, or agent runtimes.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class TelemetryContext:
    project: str
    provider: str
    model: str
    agent_role: str
    environment: str
    task: str = ""
    workflow: str = ""
    run_id: str = ""
    user_or_operator: str = ""
    feature: str = ""
    workload_class: str = ""
    routing_maturity_level: str = "n/a"
    router_decision: str = ""
    escalation_reason: str = ""


@dataclass(frozen=True)
class UsageSnapshot:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cached_input_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    reasoning_tokens: int = 0


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def get_value(obj: Any, *names: str) -> Any:
    for name in names:
        if isinstance(obj, dict) and name in obj:
            return obj[name]
        if hasattr(obj, name):
            return getattr(obj, name)
    return None


def get_nested(obj: Any, *path: str) -> Any:
    current = obj
    for name in path:
        current = get_value(current, name)
        if current is None:
            return None
    return current


def as_int(value: Any) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def extract_usage(response: Any) -> UsageSnapshot:
    """Extract common provider usage fields without importing provider SDKs."""

    usage = get_value(response, "usage", "token_usage") or response

    input_tokens = as_int(
        get_value(usage, "input_tokens", "prompt_tokens", "total_input_tokens")
    )
    output_tokens = as_int(
        get_value(usage, "output_tokens", "completion_tokens", "total_output_tokens")
    )
    total_tokens = as_int(get_value(usage, "total_tokens"))

    cache_read_tokens = as_int(
        get_value(
            usage,
            "cache_read_input_tokens",
            "cache_read_tokens",
            "cached_tokens",
        )
        or get_nested(usage, "prompt_tokens_details", "cached_tokens")
    )
    cache_write_tokens = as_int(
        get_value(usage, "cache_creation_input_tokens", "cache_write_tokens")
    )
    cached_input_tokens = as_int(get_value(usage, "cached_input_tokens")) or cache_read_tokens
    reasoning_tokens = as_int(
        get_value(usage, "reasoning_tokens")
        or get_nested(usage, "completion_tokens_details", "reasoning_tokens")
    )

    if total_tokens == 0:
        total_tokens = input_tokens + output_tokens

    return UsageSnapshot(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        cached_input_tokens=cached_input_tokens,
        cache_read_tokens=cache_read_tokens,
        cache_write_tokens=cache_write_tokens,
        reasoning_tokens=reasoning_tokens,
    )


def build_entry(
    context: TelemetryContext,
    usage: UsageSnapshot,
    estimated_cost_usd: float,
    latency_ms: float,
    retry_count: int = 0,
    tool_call_count: int = 0,
    quality_result: str = "n/a",
    notes: str = "",
    source: str = "provider_usage_object",
) -> dict[str, Any]:
    run_id = context.run_id or str(uuid.uuid4())
    entry = {
        **asdict(context),
        "timestamp": utc_now(),
        "run_id": run_id,
        "source": source,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "total_tokens": usage.total_tokens,
        "cached_input_tokens": usage.cached_input_tokens,
        "cache_read_tokens": usage.cache_read_tokens,
        "cache_write_tokens": usage.cache_write_tokens,
        "cache_hit": usage.cache_read_tokens > 0 or usage.cached_input_tokens > 0,
        "reasoning_tokens": usage.reasoning_tokens,
        "estimated_cost_usd": float(estimated_cost_usd),
        "latency_ms": float(latency_ms),
        "retry_count": int(retry_count),
        "tool_call_count": int(tool_call_count),
        "quality_result": quality_result,
        "notes": notes,
    }
    return entry


def append_jsonl(path: Path, entry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def write_telemetry_entry(
    telemetry_path: str | Path,
    context: TelemetryContext,
    response: Any,
    estimated_cost_usd: float,
    latency_ms: float,
    retry_count: int = 0,
    tool_call_count: int = 0,
    quality_result: str = "n/a",
    notes: str = "",
    source: str = "provider_usage_object",
) -> dict[str, Any]:
    usage = extract_usage(response)
    entry = build_entry(
        context=context,
        usage=usage,
        estimated_cost_usd=estimated_cost_usd,
        latency_ms=latency_ms,
        retry_count=retry_count,
        tool_call_count=tool_call_count,
        quality_result=quality_result,
        notes=notes,
        source=source,
    )
    append_jsonl(Path(telemetry_path), entry)
    return entry


def call_with_telemetry(
    call: Callable[[], Any],
    telemetry_path: str | Path,
    context: TelemetryContext,
    estimate_cost: Callable[[UsageSnapshot, TelemetryContext], float],
    retry_count: int = 0,
    tool_call_count: int = 0,
    notes: str = "",
) -> Any:
    started = time.perf_counter()
    response = call()
    latency_ms = (time.perf_counter() - started) * 1000
    usage = extract_usage(response)
    estimated_cost = estimate_cost(usage, context)
    entry = build_entry(
        context=context,
        usage=usage,
        estimated_cost_usd=estimated_cost,
        latency_ms=latency_ms,
        retry_count=retry_count,
        tool_call_count=tool_call_count,
        notes=notes,
    )
    append_jsonl(Path(telemetry_path), entry)
    return response
