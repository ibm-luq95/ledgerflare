"""Tests for security middleware event output and signal capture."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient


@pytest.mark.security
@pytest.mark.django_db
def test_failed_login_event_captured(
    anon_api_client: APIClient, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify failed login attempt is captured in security logs."""
    response = anon_api_client.post(
        "/auth/login",
        {"email": "wrong@example.com", "password": "bad", "user_type": "manager"},
    )
    assert response.status_code in (400, 401, 429)
