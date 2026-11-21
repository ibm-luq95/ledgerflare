"""Unit tests for advanced access controls, throttling, and safety guards."""
from __future__ import annotations

from typing import Any

import pytest
from django.contrib.admin.sites import AdminSite
from django.core.exceptions import ValidationError
from django.core.management import CommandError, call_command
from django.test import RequestFactory
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from beach_wood_user.models import BWUser
from beach_wood_user.views.api import (
    AssignClientToBookkeeperApiView,
    UpdateStaffPermissionsApiView,
)
from client.models import ClientProxy
from client_account.forms import ClientAccountForm
from client_account.models import ClientAccountProxy
from core.admin.base_mixin import BWBaseAdminModelMixin
from core.constants.users import CON_BOOKKEEPER, CON_MANAGER
from job.forms import JobForm
from job.models import JobProxy


@pytest.fixture(autouse=True)
def setup_groups(db: None) -> None:
    """Ensure Django auth groups exist."""
    call_command("create_groups")


@pytest.mark.django_db
class TestAdvancedAccessControls:
    """Test suite verifying field-level protection, admin safety, and command guards."""

    def test_job_form_field_level_protection_for_non_managers(self) -> None:
        """Verify bookkeepers cannot switch client or managed_by on job updates."""
        manager = BWUser.objects.create_user(
            email="mgr_form@example.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        bk = BWUser.objects.create_user(
            email="bk_form@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        client1 = ClientProxy.objects.create(name="Client 1")
        client2 = ClientProxy.objects.create(name="Client 2")

        job = JobProxy.objects.create(
            title="Tax Filing",
            client=client1,
            managed_by=manager,
        )

        # Bookkeeper attempting to reassign client on update
        form = JobForm(
            data={"title": "Updated", "client": client2.pk, "managed_by": manager.pk},
            instance=job,
            is_updated=True,
            user_type=CON_BOOKKEEPER,
            user=bk,
        )
        assert not form.is_valid()
        assert "client" in form.errors

        # Bookkeeper attempting to change managed_by on update
        form2 = JobForm(
            data={"title": "Updated", "client": client1.pk, "managed_by": bk.pk},
            instance=job,
            is_updated=True,
            user_type=CON_BOOKKEEPER,
            user=bk,
        )
        assert not form2.is_valid()
        assert "managed_by" in form2.errors

    def test_client_account_form_client_locking(self) -> None:
        """Verify client cannot be changed on existing client account update."""
        client1 = ClientProxy.objects.create(name="Client One")
        client2 = ClientProxy.objects.create(name="Client Two")
        account = ClientAccountProxy.objects.create(
            client=client1,
            account_name="AWS Account",
        )

        form = ClientAccountForm(
            data={"client": client2.pk, "account_name": "Renamed"},
            instance=account,
            is_update=True,
        )
        assert not form.is_valid()
        assert "client" in form.errors

    def test_admin_delete_permission_and_soft_delete_action(
        self, rf: RequestFactory
    ) -> None:
        """Verify admin delete permission requires superuser and soft deletes."""
        superuser = BWUser.objects.create_superuser(
            email="admin_su@example.com",
            password="ValidPassword123!",
        )
        staff = BWUser.objects.create_user(
            email="admin_staff@example.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )

        site = AdminSite()
        admin_obj = BWBaseAdminModelMixin(ClientProxy, site)

        req_staff = rf.get("/admin/")
        req_staff.user = staff
        assert admin_obj.has_delete_permission(req_staff) is False

        req_su = rf.get("/admin/")
        req_su.user = superuser
        assert admin_obj.has_delete_permission(req_su) is True

        # Test soft delete action
        client = ClientProxy.objects.create(name="Soft Delete Admin Client")
        admin_obj.soft_delete_selected(req_su, ClientProxy.objects.filter(pk=client.pk))
        client.refresh_from_db()
        assert client.is_deleted is True
        assert client not in ClientProxy.objects.all()
        assert client in ClientProxy.original_objects.all()

    def test_auth_management_api_throttling_configuration(self) -> None:
        """Verify throttling classes are mounted on sensitive auth APIs."""
        assert len(UpdateStaffPermissionsApiView.throttle_classes) > 0
        assert len(AssignClientToBookkeeperApiView.throttle_classes) > 0

    def test_production_guard_command_protection(self, settings: Any) -> None:
        """Verify commands with ProductionGuardCommandMixin refuse unconfirmed runs in production."""
        settings.ENVIRONMENT = "production"
        settings.DEBUG = False

        # Attempting seed command without flag should raise CommandError
        with pytest.raises(CommandError) as exc_info:
            call_command("seed_models", model_name="job", count=1)
        assert "Destructive command requires '--confirm-production'" in str(exc_info.value)



