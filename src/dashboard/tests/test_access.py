from __future__ import annotations

import re

import pytest
from bs4 import BeautifulSoup
from django.core import management
from django.test import Client
from django.urls import reverse_lazy

from beach_wood_user.forms import BWLoginForm
from beach_wood_user.models import BWUser


from axes.utils import reset
from django.core.cache import cache


@pytest.fixture(autouse=True)
def setup_groups(db: None) -> None:
    """Ensure auth groups exist for user signals and reset rate limiter."""
    management.call_command("create_groups")
    cache.clear()
    reset()


@pytest.mark.django_db
class TestAccessDashboard:
    """Test suite for dashboard access and authentication flows."""

    def test_login_form(self) -> None:
        form_data = {
            "email": "admin@admin.com",
            "password": "test123456",
            "user_type": "manager",
        }
        form = BWLoginForm(data=form_data)
        assert form.is_valid()

    def test_successfully_login(self, client: Client) -> None:
        credentials = {
            "email": "admin_success@admin.com",
            "password": "test123456",
            "user_type": "manager",
        }
        BWUser.objects.create_user(**credentials)
        response = client.post(reverse_lazy("auth:login"), credentials)
        assert response.status_code == 302
        assert response.url == str(reverse_lazy("dashboard:manager:home"))

    def test_dashboard_bootstrap_scripts_match_csp_nonce(
        self, client: Client
    ) -> None:
        credentials = {
            "email": "admin_csp@admin.com",
            "password": "test123456",
            "user_type": "manager",
        }
        BWUser.objects.create_user(**credentials)
        login_response = client.post(
            reverse_lazy("auth:login"),
            credentials,
        )
        assert login_response.status_code == 302
        assert login_response.url == str(reverse_lazy("dashboard:manager:home"))

        response = client.get(reverse_lazy("dashboard:manager:home"))
        assert response.status_code == 200

        csp_header = response.headers.get("Content-Security-Policy", "")
        assert "default-src" in csp_header or "script-src" in csp_header

        soup = BeautifulSoup(response.content, "html.parser")
        auth_script = soup.find(
            "script",
            string=lambda text: text and "window.AUTH_TOKEN" in text,
        )
        csrf_script = soup.find(
            "script",
            string=lambda text: text and "window.csrfToken" in text,
        )
        # Verify window.AUTH_TOKEN is no longer leaked into DOM
        assert auth_script is None
        assert csrf_script is not None
        assert "window.AUTH_TOKEN" not in response.content.decode()

    def test_invalid_login(self, client: Client) -> None:
        credentials = {
            "email": "admin_invalid@admin.com",
            "password": "test123456",
            "user_type": "bookkeeper",
        }
        BWUser.objects.create_user(**credentials)
        credentials["password"] = "WrongPassword"
        response = client.post(reverse_lazy("auth:login"), credentials)
        assert response.status_code in (200, 400, 429)

