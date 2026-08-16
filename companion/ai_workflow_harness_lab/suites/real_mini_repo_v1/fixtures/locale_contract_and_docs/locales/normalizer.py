from __future__ import annotations

"""Locale normalization helpers for a mini contract fixture."""

SUPPORTED_LOCALES = {"en", "ru"}


def normalize_locale(value: str) -> str:
    """Normalize user locale inputs to supported locale codes."""
    if not value:
        return value

    normalized = value.lower().replace("_", "-")
    if "-" in normalized:
        normalized = normalized.split("-", 1)[0]

    if normalized in SUPPORTED_LOCALES:
        return normalized

    return normalized
