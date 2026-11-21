# -*- coding: utf-8 -*-#
from __future__ import annotations

from typing import Any
import pytest
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.urls import reverse
from model_bakery import baker

from core.constants.site_settings import SITE_SETTINGS_DB_SLUG
from site_settings.models import SiteSettings
from special_assignment.models import SpecialAssignmentProxy


@pytest.fixture(autouse=True)
def setup_test_environment(db: Any) -> None:
    """Ensure Django auth groups, site settings, and sites exist before running tests."""
    call_command("create_groups")
    SiteSettings.objects.get_or_create(
        slug=SITE_SETTINGS_DB_SLUG,
        defaults={"name": "LedgerFlare", "email": "info@ledgerflare.com"},
    )
    Site.objects.get_or_create(domain="testserver", defaults={"name": "testserver"})


@pytest.mark.django_db
def test_special_assignment_quick_peek_endpoint(client, admin_user):
    client.force_login(admin_user)
    sa = baker.make(
        SpecialAssignmentProxy,
        title="Quick Peek Unique Title 99",
        body="Detailed test description content for quick peek view.",
        assigned_to=admin_user,
        is_deleted=False,
    )
    url = reverse("dashboard:special_assignment:quick-peek", kwargs={"pk": sa.pk})
    response = client.get(url)
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Quick Peek Unique Title 99" in content
    assert "Detailed test description content for quick peek view." in content
