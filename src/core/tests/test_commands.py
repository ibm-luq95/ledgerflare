"""Tests for Django CLI management commands."""

from __future__ import annotations

import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command


@pytest.mark.integration
@pytest.mark.django_db
def test_create_groups_management_command() -> None:
    """Verify create_groups management command creates required Django auth groups."""
    call_command("create_groups")
    assert Group.objects.filter(name="Manager Group").exists()
    assert Group.objects.filter(name="Bookkeeper Group").exists()
    assert Group.objects.filter(name="Assistant Group").exists()
