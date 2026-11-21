"""Unit tests for RBAC, default groups, and manager permission classes."""
from __future__ import annotations

import pytest
from django.contrib.auth.models import AnonymousUser, Group
from django.core.management import call_command
from django.test import RequestFactory
from rest_framework.views import APIView

from beach_wood_user.models import BWUser
from core.api.permissions import ManagerApiPermission
from core.constants.users import (
    CON_ASSISTANT,
    CON_BOOKKEEPER,
    CON_CFO,
    CON_MANAGER,
    READONLY_NEW_STAFF_MEMBER_GROUP_NAME,
)
from core.views.mixins.authorization import (
    BWManagerAccessMixin,
    BWManagerAssistantAccessMixin,
)


@pytest.fixture(autouse=True)
def setup_groups(db: None) -> None:
    """Ensure Django auth groups exist before running RBAC tests."""
    call_command("create_groups")


@pytest.mark.django_db
class TestRbacPermissions:
    """Test suite verifying RBAC integrity across groups and mixins."""

    def test_readonly_group_has_no_write_permissions(self) -> None:
        """Verify New Staff Readonly Group has only view/list permissions."""
        group = Group.objects.get(name=READONLY_NEW_STAFF_MEMBER_GROUP_NAME)
        permissions = group.permissions.all()

        assert permissions.exists()
        for perm in permissions:
            codename = perm.codename
            assert not codename.startswith("add_"), f"Unexpected add perm: {codename}"
            assert not codename.startswith("change_"), f"Unexpected change perm: {codename}"
            assert not codename.startswith("delete_"), f"Unexpected delete perm: {codename}"

    def test_manager_api_permission_grants_manager_and_assistant(
        self, rf: RequestFactory
    ) -> None:
        """Verify ManagerApiPermission allows manager and assistant."""
        manager = BWUser.objects.create_user(
            email="manager@example.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        assistant = BWUser.objects.create_user(
            email="assistant@example.com",
            password="ValidPassword123!",
            user_type=CON_ASSISTANT,
        )
        perm = ManagerApiPermission()
        view = APIView()

        request_mgr = rf.get("/api/test/")
        request_mgr.user = manager
        assert perm.has_permission(request_mgr, view) is True

        request_asst = rf.get("/api/test/")
        request_asst.user = assistant
        assert perm.has_permission(request_asst, view) is True

    def test_manager_api_permission_denies_bookkeeper_and_cfo(
        self, rf: RequestFactory
    ) -> None:
        """Verify ManagerApiPermission denies bookkeeper and CFO."""
        bookkeeper = BWUser.objects.create_user(
            email="bookkeeper@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        cfo = BWUser.objects.create_user(
            email="cfo@example.com",
            password="ValidPassword123!",
            user_type=CON_CFO,
        )
        perm = ManagerApiPermission()
        view = APIView()

        request_bk = rf.get("/api/test/")
        request_bk.user = bookkeeper
        assert perm.has_permission(request_bk, view) is False

        request_cfo = rf.get("/api/test/")
        request_cfo.user = cfo
        assert perm.has_permission(request_cfo, view) is False

        request_anon = rf.get("/api/test/")
        request_anon.user = AnonymousUser()
        assert perm.has_permission(request_anon, view) is False

    def test_bw_manager_assistant_access_mixin(
        self, rf: RequestFactory
    ) -> None:
        """Verify BWManagerAssistantAccessMixin test_func logic."""
        manager = BWUser.objects.create_user(
            email="manager@example.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        assistant = BWUser.objects.create_user(
            email="assistant@example.com",
            password="ValidPassword123!",
            user_type=CON_ASSISTANT,
        )
        bookkeeper = BWUser.objects.create_user(
            email="bookkeeper@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        cfo = BWUser.objects.create_user(
            email="cfo@example.com",
            password="ValidPassword123!",
            user_type=CON_CFO,
        )

        mixin = BWManagerAssistantAccessMixin()

        req = rf.get("/dashboard/test/")
        req.user = manager
        mixin.request = req
        assert mixin.test_func() is True

        req.user = assistant
        mixin.request = req
        assert mixin.test_func() is True

        req.user = bookkeeper
        mixin.request = req
        assert mixin.test_func() is False

        req.user = cfo
        mixin.request = req
        assert mixin.test_func() is False
