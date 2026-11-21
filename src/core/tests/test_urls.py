"""Tests for URL reverse resolutions across all app namespaces."""

from __future__ import annotations

import pytest
from django.urls import reverse


@pytest.mark.unit
def test_url_reverse_lookups() -> None:
    """Verify URL reverse resolutions for core routes."""
    assert reverse("auth:login") == "/auth/login"
    assert reverse("dashboard:client:list") == "/dashboard/client/"
