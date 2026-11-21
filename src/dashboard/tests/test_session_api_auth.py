"""Tests for SessionAuthentication support across DRF API endpoints."""

from __future__ import annotations

import pytest
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient

from beach_wood_user.models import BWUser
from core.choices import BeachWoodUserTypeEnum


@pytest.fixture(autouse=True)
def setup_groups(db: None) -> None:
    call_command("create_groups")


@pytest.mark.django_db
class TestSessionApiAuth:
    """Verify DRF API endpoints accept Django session authentication."""

    def test_session_authenticated_user_can_access_api(self) -> None:
        """A user logged in via session (without Token header) can access API endpoints."""
        user = BWUser.objects.create_user(
            email="session_user@example.com",
            password="ValidPassword123!",
            user_type=BeachWoodUserTypeEnum.MANAGER,
        )

        client = APIClient()
        client.force_login(user=user)

        # Query client-api without Authorization header
        url = reverse("dashboard:client:api:client-api-router-list")
        response = client.get(url)
        assert response.status_code == 200

    def test_token_auth_still_supported(self) -> None:
        """Backward compatibility: Token authentication remains supported."""
        from rest_framework.authtoken.models import Token

        user = BWUser.objects.create_user(
            email="token_user@example.com",
            password="ValidPassword123!",
            user_type=BeachWoodUserTypeEnum.MANAGER,
        )
        token, _ = Token.objects.get_or_create(user=user)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        url = reverse("dashboard:client:api:client-api-router-list")
        response = client.get(url)
        assert response.status_code == 200
