"""Tests for HMAC-SHA256 blind index generation and context isolation."""

from __future__ import annotations

import pytest

from core.crypto.blind_index import compute_blind_index, get_blind_index_key
from core.crypto.service import KeyConfigurationError


@pytest.mark.security
def test_blind_index_empty_and_none() -> None:
    assert compute_blind_index(None) == ""
    assert compute_blind_index("") == ""


@pytest.mark.security
def test_blind_index_deterministic_and_normalized() -> None:
    idx1 = compute_blind_index("SecretPass123", context="user:password")
    idx2 = compute_blind_index("  secretpass123  ", context="user:password")
    assert idx1 == idx2
    assert len(idx1) == 64


@pytest.mark.security
def test_blind_index_context_separation() -> None:
    text = "SharedSecretValue"
    idx_a = compute_blind_index(text, context="client:account_no")
    idx_b = compute_blind_index(text, context="vendor:account_no")
    assert idx_a != idx_b


@pytest.mark.security
def test_blind_index_without_normalization() -> None:
    idx_upper = compute_blind_index("CASE", normalize=False)
    idx_lower = compute_blind_index("case", normalize=False)
    assert idx_upper != idx_lower


@pytest.mark.security
def test_blind_index_missing_keys_raises(settings: pytest.MonkeyPatch) -> None:
    settings.BLIND_INDEX_KEY = None  # type: ignore[attr-defined]
    settings.CONTENT_ENCRYPTION_KEY = None  # type: ignore[attr-defined]
    with pytest.raises(KeyConfigurationError):
        get_blind_index_key()
