"""Tests for multi-key configuration and backward compatibility."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from beach_wood_financial_proj.settings.config import AppSettings, get_env_file_path


@pytest.mark.security
def test_multi_key_dict_json_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify AppSettings parses JSON string into CONTENT_ENCRYPTION_KEYS dict."""
    keys = {"k1": "a" * 64, "k2": "b" * 64}
    monkeypatch.setenv("CONTENT_ENCRYPTION_KEYS", json.dumps(keys))
    monkeypatch.setenv("ACTIVE_KEY_ID", "k2")

    settings = AppSettings(_env_file=get_env_file_path())
    assert keys == settings.CONTENT_ENCRYPTION_KEYS
    assert settings.ACTIVE_KEY_ID == "k2"


@pytest.mark.security
def test_invalid_key_id_with_colon_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify key ID containing colons is rejected by validator."""
    keys = {"k:1": "a" * 64}
    monkeypatch.setenv("CONTENT_ENCRYPTION_KEYS", json.dumps(keys))

    with pytest.raises(ValidationError):
        AppSettings(_env_file=get_env_file_path())
