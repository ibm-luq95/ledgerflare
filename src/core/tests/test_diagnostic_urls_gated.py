"""Tests verifying diagnostic logging routes are gated behind DEBUG, CORS origins are clean, and errors masked."""

from __future__ import annotations

import pytest
from django.test import Client, override_settings
from django.urls import resolve, reverse
from django.urls.exceptions import Resolver404


class TestDiagnosticRoutesGated:
    """Verify diagnostic endpoints are inaccessible in non-DEBUG environments."""

    @pytest.mark.django_db
    def test_diagnostic_routes_not_accessible_when_debug_false(
        self, client: Client
    ) -> None:
        """Accessing test-logging routes in production mode must return 404."""
        response = client.get("/test-logging/")
        assert response.status_code == 404

        response_sec = client.get("/test-security-logging/")
        assert response_sec.status_code == 404

        response_sql = client.get("/test-sql-logging/")
        assert response_sql.status_code == 404

    def test_production_cors_origins_have_no_whitespace(self) -> None:
        """Every entry in CORS_ALLOWED_ORIGINS in production settings must be stripped of whitespace."""
        from beach_wood_financial_proj.settings import production

        for origin in production.CORS_ALLOWED_ORIGINS:
            assert origin == origin.strip(), f"CORS origin has whitespace: '{origin}'"

    def test_update_staff_permissions_masks_internal_error(self, rf: None) -> None:
        """Internal server errors must return a generic detail message, not raw exception string."""
        from unittest.mock import patch

        from rest_framework.test import APIRequestFactory

        from beach_wood_user.models import BWUser
        from beach_wood_user.views.api import UpdateStaffPermissionsApiView
        from core.choices import BeachWoodUserTypeEnum

        factory = APIRequestFactory()
        user = BWUser(
            email="manager_err@example.com",
            user_type=BeachWoodUserTypeEnum.MANAGER,
            is_superuser=True,
        )
        request = factory.post(
            "/fake-url/", {"user": "invalid-uuid", "permissions": []}, format="json"
        )
        request.user = user

        view = UpdateStaffPermissionsApiView.as_view()
        with patch(
            "beach_wood_user.views.api.atomic",
            side_effect=RuntimeError("Secret DB Schema Leak"),
        ):
            response = view(request)
            assert response.status_code == 500
            assert "Secret DB Schema Leak" not in str(response.data)
            assert response.data.get("detail") == "An internal error occurred."
