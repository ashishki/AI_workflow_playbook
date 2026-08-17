from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import json
import os
import re
import sys
from contextlib import contextmanager
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable

from .receipts import sha256_file

DSH_RELEASE_TAG = "dsh-v0.1.0-rc.7"
DSH_UPSTREAM_COMMIT = "99f6f02fecdb7dff40c3fbc9470f5907c29f74ca"
DSH_SDK_DISTRIBUTION = "deepseek-harness-sdk"
DSH_RUNTIME_DISTRIBUTION = "deepseek-harness-runtime-bin"
DSH_EXPECTED_VERSION = "0.1.0rc7"

_RATE_LIMIT_PATTERNS = (
    "rate limit",
    "rate_limit",
    "too many requests",
    "http 429",
    "status 429",
    "quota exceeded",
    "quota_exceeded",
    "insufficient balance",
    "insufficient_balance",
)
_CREDENTIAL_PATTERNS = (
    "missing credential",
    "missing_credential",
    "invalid api key",
    "invalid_api_key",
    "authentication failed",
    "unauthorized",
    "http 401",
    "status 401",
)
_SECRET_NAME = re.compile(r"(?:^|_)(?:KEY|PASSWORD|SECRET|TOKEN|CREDENTIAL|PASSPHRASE)(?:_|$)", re.I)
_SECRET_ALLOWLIST = {
    "DEEPSEEK_API_KEY",
}


class DeepSeekRuntimeError(RuntimeError):
    """Base error for DeepSeek Harness adapter setup or execution."""


class DeepSeekRateLimitError(DeepSeekRuntimeError):
    """The provider rejected the run because a quota or rate limit was reached."""


class DeepSeekCredentialError(DeepSeekRuntimeError):
    """The provider credential is absent or rejected."""


def default_profile_path() -> Path:
    return Path(__file__).resolve().parent / "profiles" / "deepseek_workspace_write.cordis.yml"


def jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {key: jsonable(item) for key, item in asdict(value).items()}
    if hasattr(value, "model_dump"):
        return jsonable(value.model_dump())
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def write_jsonl(path: Path, records: Iterable[Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(jsonable(record), sort_keys=True, ensure_ascii=False) + "\n")
    return path


def sanitize_runtime_environment(
    environment: dict[str, str] | None = None,
    *,
    overrides: dict[str, str] | None = None,
) -> tuple[dict[str, str], list[str]]:
    """Return an environment safe to inherit into the DSH runtime.

    DeepSeek Harness' Python SDK inherits the parent environment. The adapter
    removes credential-shaped variables except the DeepSeek key explicitly
    required for the selected provider. This is a name-based guard, not a full
    secret detector; trial workspaces must still be disposable.
    """

    source = dict(os.environ if environment is None else environment)
    sanitized: dict[str, str] = {}
    removed: list[str] = []
    for key, value in source.items():
        if key in _SECRET_ALLOWLIST:
            sanitized[key] = value
            continue
        if key.startswith("DSH_"):
            removed.append(key)
            continue
        if _SECRET_NAME.search(key):
            removed.append(key)
            continue
        sanitized[key] = value
    if overrides:
        sanitized.update({str(key): str(value) for key, value in overrides.items()})
    return sanitized, sorted(set(removed))



@contextmanager
def isolated_process_environment(environment: dict[str, str]):
    """Temporarily replace os.environ while the SDK spawns its runtime.

    The upstream SDK begins from os.environ and then overlays its explicit env,
    so omission alone does not scrub a secret. Screening is intentionally
    single-threaded; callers must not use this helper in a concurrent process.
    """

    original = dict(os.environ)
    os.environ.clear()
    os.environ.update(environment)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(original)

def validate_restricted_profile(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"profile cannot be read: {exc}"]

    required_fragments = {
        "SDK JSON-RPC entry": "@deepseek-ai/dsh-sdk-jsonrpc-server",
        "DeepSeek adapter": "@deepseek-ai/dsh-llm-deepseek",
        "workspace-write policy": "mode: workspace-write",
        "process sandbox": "@deepseek-ai/dsh-bash-sandbox",
        "filesystem sandbox": "@deepseek-ai/dsh-fs-sandbox",
        "session persistence": "@deepseek-ai/dsh-session-persistence-jsonl",
        "agent spine": "@deepseek-ai/dsh-agent-spine-demo",
    }
    for label, fragment in required_fragments.items():
        if fragment not in text:
            errors.append(f"missing {label}: {fragment}")

    forbidden_fragments = {
        "danger-full-access": "danger-full-access",
        "bare local filesystem": "@deepseek-ai/dsh-fs-local",
        "unconfined persistent bash": "@deepseek-ai/dsh-tool-bash-persistent",
        "web surface": "@deepseek-ai/dsh-web",
    }
    for label, fragment in forbidden_fragments.items():
        if fragment in text:
            errors.append(f"forbidden {label}: {fragment}")

    if "@deepseek-ai/dsh-session-telemetry" in text and "DSH_TELEMETRY_DISABLED" not in text:
        errors.append("telemetry plugin present without an explicit disabled guard")
    return errors


def distribution_identity(name: str) -> dict[str, Any]:
    try:
        version = importlib.metadata.version(name)
        distribution = importlib.metadata.distribution(name)
    except importlib.metadata.PackageNotFoundError:
        return {"name": name, "installed": False, "version": None, "record_sha256": None}

    record = distribution.read_text("RECORD") or ""
    return {
        "name": name,
        "installed": True,
        "version": version,
        "record_sha256": hashlib.sha256(record.encode("utf-8")).hexdigest(),
    }


def load_sdk_module() -> Any:
    try:
        return importlib.import_module("deepseek_harness")
    except ImportError as exc:
        raise DeepSeekRuntimeError(
            "deepseek-harness-sdk is not installed; install requirements-deepseek-harness.txt"
        ) from exc


def doctor(
    *,
    profile_path: Path | None = None,
    require_credential: bool = False,
    expected_version: str = DSH_EXPECTED_VERSION,
) -> dict[str, Any]:
    profile = (profile_path or default_profile_path()).resolve()
    sdk = distribution_identity(DSH_SDK_DISTRIBUTION)
    runtime = distribution_identity(DSH_RUNTIME_DISTRIBUTION)
    checks: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, detail: str) -> None:
        checks.append({"id": check_id, "passed": bool(passed), "detail": detail})

    add("platform", sys.platform != "win32", f"platform={sys.platform}; restricted profile requires POSIX bash")
    profile_errors = validate_restricted_profile(profile)
    add("profile", not profile_errors, "; ".join(profile_errors) if profile_errors else str(profile))
    add("sdk_installed", bool(sdk["installed"]), json.dumps(sdk, sort_keys=True))
    add("runtime_installed", bool(runtime["installed"]), json.dumps(runtime, sort_keys=True))
    add(
        "sdk_version",
        bool(sdk["installed"]) and sdk["version"] == expected_version,
        f"expected={expected_version}; actual={sdk['version']}",
    )
    add(
        "runtime_version",
        bool(runtime["installed"]) and runtime["version"] == expected_version,
        f"expected={expected_version}; actual={runtime['version']}",
    )
    credential_present = bool(os.environ.get("DEEPSEEK_API_KEY"))
    add(
        "credential",
        credential_present or not require_credential,
        "DEEPSEEK_API_KEY present" if credential_present else "DEEPSEEK_API_KEY missing",
    )
    return {
        "schema_version": "harness_lab.deepseek_doctor.v1",
        "status": "pass" if all(item["passed"] for item in checks) else "fail",
        "release_tag": DSH_RELEASE_TAG,
        "upstream_commit": DSH_UPSTREAM_COMMIT,
        "expected_version": expected_version,
        "profile_path": str(profile),
        "profile_sha256": sha256_file(profile) if profile.is_file() else None,
        "sdk": sdk,
        "runtime": runtime,
        "checks": checks,
    }


def is_rate_limit(value: Any) -> bool:
    text = json.dumps(jsonable(value), sort_keys=True, ensure_ascii=False).lower()
    return any(pattern in text for pattern in _RATE_LIMIT_PATTERNS)


def is_credential_failure(value: Any) -> bool:
    text = json.dumps(jsonable(value), sort_keys=True, ensure_ascii=False).lower()
    return any(pattern in text for pattern in _CREDENTIAL_PATTERNS)


def _number(mapping: dict[str, Any], names: tuple[str, ...]) -> int:
    for name in names:
        raw = mapping.get(name)
        if isinstance(raw, bool):
            continue
        if isinstance(raw, (int, float)):
            return int(raw)
    return 0


def _header_from_event(event: dict[str, Any]) -> dict[str, Any] | None:
    if event.get("type") != "request/header":
        return None
    data = event.get("data")
    if not isinstance(data, dict):
        return None
    header = data.get("header")
    return header if isinstance(header, dict) else data


def extract_runtime_metrics(
    events: list[dict[str, Any]],
    notifications: list[Any],
    *,
    input_price_per_million: float | None = None,
    output_price_per_million: float | None = None,
) -> dict[str, Any]:
    input_tokens = 0
    output_tokens = 0
    cache_read_tokens = 0
    cache_write_tokens = 0
    tool_calls = 0
    tool_failures = 0
    steps = 0
    turns = 0
    provider = None
    model = None
    system_prompt = None
    tools: Any = None

    for event in events:
        event_type = event.get("type")
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        if event_type == "step/start":
            steps += 1
        elif event_type == "turn/start":
            turns += 1
        elif event_type == "tool/call":
            tool_calls += 1
        elif event_type == "tool/result" and (data.get("error") or data.get("isError")):
            tool_failures += 1
        elif event_type == "assistant/message":
            usage = data.get("usage")
            if not isinstance(usage, dict):
                message = data.get("message")
                usage = message.get("usage") if isinstance(message, dict) else None
            if isinstance(usage, dict):
                input_tokens += _number(usage, ("inputTokens", "input_tokens", "promptTokens", "prompt_tokens"))
                output_tokens += _number(usage, ("outputTokens", "output_tokens", "completionTokens", "completion_tokens"))
                cache_read_tokens += _number(usage, ("cacheReadInputTokens", "cache_read_input_tokens", "cachedTokens"))
                cache_write_tokens += _number(usage, ("cacheWriteInputTokens", "cache_write_input_tokens"))
        header = _header_from_event(event)
        if header is not None:
            config = header.get("config") if isinstance(header.get("config"), dict) else {}
            provider = config.get("provider") or provider
            model = config.get("model") or model
            system_prompt = header.get("system") if isinstance(header.get("system"), str) else system_prompt
            tools = header.get("tools") if isinstance(header.get("tools"), list) else tools

    cost_usd: float | None = None
    if input_price_per_million is not None and output_price_per_million is not None:
        cost_usd = (
            input_tokens * input_price_per_million / 1_000_000
            + output_tokens * output_price_per_million / 1_000_000
        )
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_tokens": cache_read_tokens,
        "cache_write_tokens": cache_write_tokens,
        "tool_calls": tool_calls,
        "tool_failures": tool_failures,
        "steps": steps,
        "turns": turns,
        "notification_count": len(notifications),
        "provider_observed": provider,
        "model_observed": model,
        "system_prompt_sha256": hashlib.sha256((system_prompt or "").encode("utf-8")).hexdigest(),
        "tool_schema_sha256": hashlib.sha256(
            json.dumps(tools or [], sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "request_header_observed": provider is not None and model is not None,
        "cost_usd": cost_usd,
    }


def find_session_logs(session_root: Path, session_id: str) -> list[Path]:
    if not session_root.exists():
        return []
    candidates = sorted(
        path for path in session_root.rglob("*.jsonl") if path.is_file() and not path.is_symlink()
    )
    matching = [path for path in candidates if session_id in path.name or session_id in path.as_posix()]
    return matching or candidates
