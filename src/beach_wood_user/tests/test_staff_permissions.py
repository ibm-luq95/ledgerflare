"""Unit tests for staff permissions and access control authorization."""
from __future__ import annotations

import pytest
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.test import RequestFactory

from beach_wood_user.models import BWUser
from beach_wood_user.views.staff import (
    StaffMemberDetailsView,
    StaffProfileView,
    StaffUpdatePasswordView,
)
from core.constants.users import (
    ASSISTANT_FULL_MANAGER_PERMISSION_SHORT_NAME,
    CON_ASSISTANT,
    CON_BOOKKEEPER,
    CON_MANAGER,
)


@pytest.fixture(autouse=True)
def setup_groups(db: None) -> None:
    """Ensure Django auth groups exist before user creation."""
    call_command("create_groups")


@pytest.mark.django_db
class TestStaffPermissions:
    """Tests for staff views authorization test_func logic."""

    def test_user_can_access_own_password_update_view(
        self, rf: RequestFactory
    ) -> None:
        user = BWUser.objects.create_user(
            email="bookkeeper@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        request = rf.get(f"/dashboard/staff/update-password/{user.pk}/")
        request.user = user

        view = StaffUpdatePasswordView()
        view.request = request
        view.kwargs = {"pk": user.pk}
        view.object = user

        assert view.test_func() is True

    def test_bookkeeper_cannot_access_other_user_password_update(
        self, rf: RequestFactory
    ) -> None:
        bookkeeper = BWUser.objects.create_user(
            email="bookkeeper@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        manager = BWUser.objects.create_user(
            email="manager@example.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        request = rf.get(f"/dashboard/staff/update-password/{manager.pk}/")
        request.user = bookkeeper

        view = StaffUpdatePasswordView()
        view.request = request
        view.kwargs = {"pk": manager.pk}
        view.object = manager

        assert view.test_func() is False

    def test_manager_can_access_other_user_password_update(
        self, rf: RequestFactory
    ) -> None:
        manager = BWUser.objects.create_user(
            email="manager@example.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        bookkeeper = BWUser.objects.create_user(
            email="bookkeeper@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        request = rf.get(f"/dashboard/staff/update-password/{bookkeeper.pk}/")
        request.user = manager

        view = StaffUpdatePasswordView()
        view.request = request
        view.kwargs = {"pk": bookkeeper.pk}
        view.object = bookkeeper

        assert view.test_func() is True

    def test_user_can_access_own_profile(self, rf: RequestFactory) -> None:
        user = BWUser.objects.create_user(
            email="bookkeeper@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        request = rf.get(f"/dashboard/staff/profile/{user.pk}/")
        request.user = user

        view = StaffProfileView()
        view.request = request
        view.kwargs = {"pk": user.pk}
        view.object = user

        assert view.test_func() is True

    def test_bookkeeper_cannot_access_other_user_profile(
        self, rf: RequestFactory
    ) -> None:
        bookkeeper1 = BWUser.objects.create_user(
            email="bookkeeper1@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        bookkeeper2 = BWUser.objects.create_user(
            email="bookkeeper2@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        request = rf.get(f"/dashboard/staff/profile/{bookkeeper2.pk}/")
        request.user = bookkeeper1

        view = StaffProfileView()
        view.request = request
        view.kwargs = {"pk": bookkeeper2.pk}
        view.object = bookkeeper2

        assert view.test_func() is False

    def test_manager_can_access_other_user_profile(
        self, rf: RequestFactory
    ) -> None:
        manager = BWUser.objects.create_user(
            email="manager@example.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        bookkeeper = BWUser.objects.create_user(
            email="bookkeeper@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        request = rf.get(f"/dashboard/staff/profile/{bookkeeper.pk}/")
        request.user = manager

        view = StaffProfileView()
        view.request = request
        view.kwargs = {"pk": bookkeeper.pk}
        view.object = bookkeeper

        assert view.test_func() is True

    def test_bookkeeper_cannot_access_staff_details(
        self, rf: RequestFactory
    ) -> None:
        bookkeeper = BWUser.objects.create_user(
            email="bookkeeper@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        manager = BWUser.objects.create_user(
            email="manager@example.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        request = rf.get(f"/dashboard/staff/member-details/{manager.pk}/")
        request.user = bookkeeper

        view = StaffMemberDetailsView()
        view.request = request
        view.kwargs = {"pk": manager.pk}
        view.object = manager

        assert view.test_func() is False

    def test_manager_can_access_staff_details(
        self, rf: RequestFactory
    ) -> None:
        manager = BWUser.objects.create_user(
            email="manager@example.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        bookkeeper = BWUser.objects.create_user(
            email="bookkeeper@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        request = rf.get(f"/dashboard/staff/member-details/{bookkeeper.pk}/")
        request.user = manager

        view = StaffMemberDetailsView()
        view.request = request
        view.kwargs = {"pk": bookkeeper.pk}
        view.object = bookkeeper

        assert view.test_func() is True

    def test_assistant_with_full_manager_permissions_can_access_staff_details(
        self, rf: RequestFactory
    ) -> None:
        assistant = BWUser.objects.create_user(
            email="assistant@example.com",
            password="ValidPassword123!",
            user_type=CON_ASSISTANT,
        )
        perm = Permission.objects.get(
            codename=ASSISTANT_FULL_MANAGER_PERMISSION_SHORT_NAME
        )
        assistant.user_permissions.add(perm)

        bookkeeper = BWUser.objects.create_user(
            email="bookkeeper@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        request = rf.get(f"/dashboard/staff/member-details/{bookkeeper.pk}/")
        request.user = assistant

        view = StaffMemberDetailsView()
        view.request = request
        view.kwargs = {"pk": bookkeeper.pk}
        view.object = bookkeeper

        assert view.test_func() is True
