"""Tests for Client DRF ViewSet and API endpoints."""

from __future__ import annotations

import pytest
from django.core.management import call_command
from model_bakery import baker
from rest_framework.test import APIClient

from beach_wood_user.models import BWUser
from client.models import ClientProxy
from core.constants.users import CON_BOOKKEEPER, CON_MANAGER


@pytest.fixture(autouse=True)
def setup_groups(db):
    """Ensure required Django auth groups exist before creating users."""
    call_command("create_groups")


@pytest.mark.integration
@pytest.mark.django_db
def test_client_search_endpoint() -> None:
    """Verify ClientViewSet search endpoint filters clients by name."""
    manager = BWUser.objects.create_user(
        email="manager_search@example.com",
        password="Password123!",
        user_type=CON_MANAGER,
    )
    c1 = baker.make(ClientProxy, name="Alpha Finance", is_deleted=False)
    c2 = baker.make(ClientProxy, name="Beta Consulting", is_deleted=False)

    client = APIClient()
    client.force_authenticate(user=manager)

    response = client.get("/dashboard/client/api/client-api/search/?q=Alpha")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["id"] == str(c1.pk)


@pytest.mark.integration
@pytest.mark.django_db
def test_client_dropdown_caching() -> None:
    """Verify ClientDropdownView returns cached list for user."""
    manager = BWUser.objects.create_user(
        email="manager_dropdown@example.com",
        password="Password123!",
        user_type=CON_MANAGER,
    )
    baker.make(ClientProxy, name="Dropdown Client", is_deleted=False)

    client = APIClient()
    client.force_authenticate(user=manager)

    res1 = client.get("/dashboard/client/api/dropdown/")
    assert res1.status_code == 200
    res2 = client.get("/dashboard/client/api/dropdown/")
    assert res2.status_code == 200
    assert res1.json() == res2.json()
