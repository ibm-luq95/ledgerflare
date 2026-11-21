"""Tests for Staff Briefcase and Staff Notes scoping and authorization."""

from __future__ import annotations

import pytest
from django.core.management import call_command
from django.test import RequestFactory
from django.urls import reverse
from rest_framework.test import APIClient

from beach_wood_user.models import BWUser
from core.choices import BeachWoodUserTypeEnum
from staff_briefcase.models import StaffAccounts, StaffBriefcase, StaffNotes
from staff_briefcase.views.notes.notes import (
    StaffNotesDeleteView,
    StaffNotesListView,
    StaffNotesUpdateView,
)


@pytest.fixture(autouse=True)
def setup_groups(db: None) -> None:
    """Ensure Django auth groups exist before running briefcase tests."""
    call_command("create_groups")


@pytest.mark.django_db
class TestBriefcaseScoping:
    """Verify that staff notes and accounts are properly scoped to user briefcase."""

    def test_user_cannot_view_or_update_other_staff_notes(
        self, rf: RequestFactory
    ) -> None:
        """User B cannot see or modify User A's private staff notes."""
        user_a = BWUser.objects.create_user(
            email="user_a_notes@example.com",
            password="ValidPassword123!",
            user_type=BeachWoodUserTypeEnum.BOOKKEEPER,
        )
        user_b = BWUser.objects.create_user(
            email="user_b_notes@example.com",
            password="ValidPassword123!",
            user_type=BeachWoodUserTypeEnum.BOOKKEEPER,
        )

        briefcase_a, _ = StaffBriefcase.objects.get_or_create(user=user_a)
        note_a = StaffNotes.objects.create(
            title="User A Secret Plan",
            note="Confidential thoughts",
        )
        briefcase_a.notes.add(note_a)

        # User B accessing StaffNotesListView must not see note_a
        view_list = StaffNotesListView()
        req_b = rf.get("/dashboard/briefcase/notes/")
        req_b.user = user_b
        view_list.request = req_b
        qs = view_list.get_queryset()
        assert not qs.filter(pk=note_a.pk).exists()

        # User B accessing StaffNotesUpdateView must not have note_a in queryset
        view_update = StaffNotesUpdateView()
        view_update.request = req_b
        view_update.kwargs = {"pk": note_a.pk}
        update_qs = view_update.get_queryset()
        assert not update_qs.filter(pk=note_a.pk).exists()

    def test_assistant_cannot_view_manager_staff_accounts_via_api(self) -> None:
        """Assistant user querying StaffAccountsViewSet cannot see Manager accounts."""
        manager = BWUser.objects.create_user(
            email="mgr_acc@example.com",
            password="ValidPassword123!",
            user_type=BeachWoodUserTypeEnum.MANAGER,
        )
        assistant = BWUser.objects.create_user(
            email="asst_acc@example.com",
            password="ValidPassword123!",
            user_type=BeachWoodUserTypeEnum.ASSISTANT,
        )

        briefcase_mgr, _ = StaffBriefcase.objects.get_or_create(user=manager)
        mgr_account = StaffAccounts.objects.create(
            name="Manager Portal Account",
            title="Firm Admin Access",
            username_email="admin@vault.com",
            password="VaultPassword123!",
        )
        briefcase_mgr.accounts.add(mgr_account)

        url = reverse(
            "dashboard:briefcase:briefcase_staff_accounts:api:staff-accounts-api-router-list"
        )
        client = APIClient()
        client.force_authenticate(user=assistant)
        response = client.get(url)
        assert response.status_code == 200
        results = response.data.get("results", response.data)
        ids = [item["id"] for item in results]
        assert str(mgr_account.pk) not in ids
