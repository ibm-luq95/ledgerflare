"""Tests for signal handlers across the application."""

from __future__ import annotations

import pytest
from django.core.management import call_command

from beach_wood_user.models import BWUser
from core.constants.users import CON_MANAGER


@pytest.fixture(autouse=True)
def setup_groups(db):
    """Ensure required auth groups exist."""
    call_command("create_groups")


@pytest.mark.unit
@pytest.mark.django_db
def test_signal_assign_group_to_user() -> None:
    """Verify user creation signal assigns user to corresponding group."""
    user = BWUser.objects.create_user(
        email="sig_mgr@example.com",
        password="Password123!",
        user_type=CON_MANAGER,
    )
    assert user.groups.filter(name="Manager Group").exists()
