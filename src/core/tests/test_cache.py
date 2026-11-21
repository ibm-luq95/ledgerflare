"""Tests for system cache handler operations."""

from __future__ import annotations

import pytest
from django.core.cache import cache


@pytest.mark.unit
def test_cache_handler_set_get_delete() -> None:
    """Verify cache set, get, and delete functionality."""
    cache.set("test_key", "test_value", timeout=60)
    assert cache.get("test_key") == "test_value"
    cache.delete("test_key")
    assert cache.get("test_key") is None
