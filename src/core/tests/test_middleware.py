"""Tests for custom middleware behavior."""

from __future__ import annotations

import pytest
from django.core.management import call_command
from django.test import Client

from beach_wood_user.models import BWUser
from core.constants.site_settings import SITE_SETTINGS_DB_SLUG
from core.constants.users import CON_BOOKKEEPER
from site_settings.models import SiteSettings


@pytest.fixture(autouse=True)
def setup_groups(db):
    """Ensure required auth groups exist."""
    call_command("create_groups")


@pytest.mark.security
@pytest.mark.django_db
def test_middleware_check_allowed_login_disallowed_bookkeeper() -> None:
    """Verify CheckAllowedLoginMiddleware blocks login when can_bookkeepers_login is False."""
    SiteSettings.objects.create(
        slug=SITE_SETTINGS_DB_SLUG,
        can_bookkeepers_login=False,
        can_assistants_login=True,
    )
    bk = BWUser.objects.create_user(
        email="bk_blocked@example.com",
        password="Password123!",
        user_type=CON_BOOKKEEPER,
    )
    client = Client()
    client.force_login(bk)
    response = client.get("/dashboard/client/")
    assert response.status_code == 302
