"""Tests for dynamic URL reverse resolution API endpoint."""

from __future__ import annotations

from typing import Any

import pytest
from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def setup_groups(db: Any) -> None:
    """Initialize system groups for signal handlers."""
    call_command("create_groups")


@pytest.mark.django_db
def test_fetch_url_get_authenticated(admin_user, auth_api_client) -> None:
    """Verify authenticated user can resolve URL via GET query parameter."""
    client: APIClient = auth_api_client(admin_user)
    fetch_endpoint = reverse("core:api:fetch-url")

    response = client.get(fetch_endpoint, {"urlName": "auth:login"})
    assert response.status_code == status.HTTP_200_OK
    assert response.data["urlPath"] == "/auth/login"


@pytest.mark.django_db
def test_fetch_url_post_authenticated(admin_user, auth_api_client) -> None:
    """Verify authenticated user can resolve URL via POST body."""
    client: APIClient = auth_api_client(admin_user)
    fetch_endpoint = reverse("core:api:fetch-url")

    response = client.post(fetch_endpoint, {"urlName": "auth:login"}, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["urlPath"] == "/auth/login"


@pytest.mark.django_db
def test_fetch_url_anonymous_rejected(anon_api_client) -> None:
    """Verify unauthenticated requests are rejected with 401 Unauthorized."""
    fetch_endpoint = reverse("core:api:fetch-url")

    get_response = anon_api_client.get(fetch_endpoint, {"urlName": "auth:login"})
    assert get_response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )

    post_response = anon_api_client.post(
        fetch_endpoint, {"urlName": "auth:login"}, format="json"
    )
    assert post_response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )


@pytest.mark.django_db
def test_fetch_url_missing_url_name(admin_user, auth_api_client) -> None:
    """Verify missing urlName returns 400 Bad Request."""
    client: APIClient = auth_api_client(admin_user)
    fetch_endpoint = reverse("core:api:fetch-url")

    get_response = client.get(fetch_endpoint)
    assert get_response.status_code == status.HTTP_400_BAD_REQUEST

    post_response = client.post(fetch_endpoint, {}, format="json")
    assert post_response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_fetch_url_invalid_url_name(admin_user, auth_api_client) -> None:
    """Verify non-existent url name returns 400 Bad Request."""
    client: APIClient = auth_api_client(admin_user)
    fetch_endpoint = reverse("core:api:fetch-url")

    response = client.get(
        fetch_endpoint, {"urlName": "nonexistent:invalid:url:pattern"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
