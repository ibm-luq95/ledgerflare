"""Tests for UpdateStaffPermissionsApiView privilege escalation hardening."""

from __future__ import annotations

import pytest
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient

from beach_wood_user.models import BWUser
from core.choices import BeachWoodUserTypeEnum


@pytest.fixture(autouse=True)
def setup_groups(db: None) -> None:
    """Ensure Django auth groups exist before running permission tests."""
    call_command("create_groups")


@pytest.mark.django_db
class TestUpdateStaffPermissionsSecurity:
    """Verify UpdateStaffPermissionsApiView enforces strict role gating and whitelist."""

    def test_assistant_cannot_update_staff_permissions(self) -> None:
        """Assistant user must receive HTTP 403 Forbidden."""
        assistant = BWUser.objects.create_user(
            email="asst_perm@example.com",
            password="ValidPassword123!",
            user_type=BeachWoodUserTypeEnum.ASSISTANT,
        )
        target = BWUser.objects.create_user(
            email="target_user@example.com",
            password="ValidPassword123!",
            user_type=BeachWoodUserTypeEnum.BOOKKEEPER,
        )

        perm = Permission.objects.filter(content_type__app_label="client").first()
        assert perm is not None

        url = reverse("dashboard:staff:update-permissions")
        client = APIClient()
        client.force_authenticate(user=assistant)
        response = client.post(
            url,
            data={"user": str(target.pk), "permissions": [perm.pk]},
            format="json",
        )
        assert response.status_code == 403

    def test_cannot_assign_superuser_or_auth_permissions(self) -> None:
        """Manager cannot assign sensitive auth or admin permissions."""
        manager = BWUser.objects.create_user(
            email="mgr_perm@example.com",
            password="ValidPassword123!",
            user_type=BeachWoodUserTypeEnum.MANAGER,
        )
        target = BWUser.objects.create_user(
            email="target_user2@example.com",
            password="ValidPassword123!",
            user_type=BeachWoodUserTypeEnum.BOOKKEEPER,
        )

        auth_perm = Permission.objects.filter(content_type__app_label="auth").first()
        assert auth_perm is not None

        url = reverse("dashboard:staff:update-permissions")
        client = APIClient()
        client.force_authenticate(user=manager)
        response = client.post(
            url,
            data={"user": str(target.pk), "permissions": [auth_perm.pk]},
            format="json",
        )
        assert response.status_code == 403
