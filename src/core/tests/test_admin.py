"""Tests for Django Admin ModelAdmin registration integrity."""

from __future__ import annotations

import pytest
from django.contrib import admin

from client.models import Client, ClientProxy


@pytest.mark.unit
def test_client_models_registered_in_admin() -> None:
    """Verify Client or ClientProxy model is registered in Django admin."""
    assert admin.site.is_registered(Client) or admin.site.is_registered(ClientProxy)
