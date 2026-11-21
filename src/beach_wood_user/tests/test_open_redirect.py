"""Tests preventing Open Redirect vulnerabilities in login flow."""

from __future__ import annotations

import pytest
from django.core.cache import cache
from django.core.management import call_command
from django.test import Client
from django.urls import reverse

from beach_wood_user.models import BWUser
from core.choices import BeachWoodUserTypeEnum


@pytest.fixture(autouse=True)
def setup_groups(db: None) -> None:
    cache.clear()
    call_command("create_groups")


@pytest.mark.django_db
class TestOpenRedirectPrevention:
    """Verify that unvalidated external redirect URLs are rejected upon login."""

    def test_external_url_in_next_param_is_rejected(self, client: Client) -> None:
        """Malicious external domain in ?next= must be ignored, falling back to home."""
        BWUser.objects.create_user(
            email="manager_redirect@example.com",
            password="ValidPassword123!",
            user_type=BeachWoodUserTypeEnum.MANAGER,
        )

        login_url = (
            reverse("auth:login")
            + "?next=https://attacker-controlled-site.com/steal-creds"
        )
        response = client.post(
            login_url,
            {
                "email": "manager_redirect@example.com",
                "password": "ValidPassword123!",
                "user_type": "manager",
            },
        )
        assert response.status_code == 302
        assert "attacker-controlled-site.com" not in response.url
        assert response.url == reverse("dashboard:manager:home")

    def test_protocol_relative_url_is_rejected(self, client: Client) -> None:
        """Protocol-relative external URL //evil.com must also be rejected."""
        BWUser.objects.create_user(
            email="manager_redirect2@example.com",
            password="ValidPassword123!",
            user_type=BeachWoodUserTypeEnum.MANAGER,
        )

        login_url = reverse("auth:login") + "?next=//evil.com/phish"
        response = client.post(
            login_url,
            {
                "email": "manager_redirect2@example.com",
                "password": "ValidPassword123!",
                "user_type": "manager",
            },
        )
        assert response.status_code == 302
        assert "evil.com" not in response.url
        assert response.url == reverse("dashboard:manager:home")

    def test_safe_local_redirect_is_allowed(self, client: Client) -> None:
        """Safe local path in ?next= must be honored upon successful login."""
        BWUser.objects.create_user(
            email="manager_redirect3@example.com",
            password="ValidPassword123!",
            user_type=BeachWoodUserTypeEnum.MANAGER,
        )

        login_url = reverse("auth:login") + "?next=/dashboard/client/"
        response = client.post(
            login_url,
            {
                "email": "manager_redirect3@example.com",
                "password": "ValidPassword123!",
                "user_type": "manager",
            },
        )
        assert response.status_code == 302
        assert response.url == "/dashboard/client/"
