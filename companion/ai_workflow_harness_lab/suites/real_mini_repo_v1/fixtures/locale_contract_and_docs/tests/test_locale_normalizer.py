from __future__ import annotations

import pytest

from locales.normalizer import normalize_locale


def test_normalize_region_locales() -> None:
    assert normalize_locale("en-US") == "en"
    assert normalize_locale("ru_RU") == "ru"
    assert normalize_locale("EN") == "en"


def test_unknown_locale_is_rejected() -> None:
    with pytest.raises(ValueError):
        normalize_locale("fr-FR")
