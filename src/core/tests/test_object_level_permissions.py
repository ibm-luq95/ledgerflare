"""Unit tests for object-level authorization mixin and CBV scoping."""
from __future__ import annotations

import pytest
from django.core.management import call_command
from django.test import RequestFactory

from beach_wood_user.models import BWUser
from bookkeeper.models import BookkeeperProxy
from cfo.models import CFOProxy
from client.models import ClientProxy
from client.views import ClientDeleteView, ClientUpdateView
from core.constants.users import (
    CON_BOOKKEEPER,
    CON_CFO,
    CON_MANAGER,
)
from important_contact.models import ImportantContact
from important_contact.views import ImportantContactListViewBW
from job.models import JobProxy
from job.views import JobDetailsView, JobUpdateView


@pytest.fixture(autouse=True)
def setup_groups(db: None) -> None:
    """Ensure Django auth groups exist before running object tests."""
    call_command("create_groups")


@pytest.mark.django_db
class TestObjectLevelPermissions:
    """Test suite verifying BWObjectAccessRequiredMixin and CBV scoping."""

    def test_client_update_view_access(self, rf: RequestFactory) -> None:
        """Verify assigned bookkeeper and manager can update client, unassigned cannot."""
        manager = BWUser.objects.create_user(
            email="mgr@example.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        bk_assigned = BWUser.objects.create_user(
            email="bk1@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        bk_unassigned = BWUser.objects.create_user(
            email="bk2@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )

        client = ClientProxy.objects.create(name="Acme Corp")
        client.bookkeepers.add(bk_assigned.bookkeeper.get_proxy_model())

        view = ClientUpdateView()
        view.kwargs = {"pk": client.pk}
        view.object = client

        # Manager check
        req_mgr = rf.get(f"/client/update/{client.pk}/")
        req_mgr.user = manager
        view.request = req_mgr
        assert view.test_func() is True

        # Assigned bookkeeper check
        req_assigned = rf.get(f"/client/update/{client.pk}/")
        req_assigned.user = bk_assigned
        view.request = req_assigned
        assert view.test_func() is True

        # Unassigned bookkeeper check
        req_unassigned = rf.get(f"/client/update/{client.pk}/")
        req_unassigned.user = bk_unassigned
        view.request = req_unassigned
        assert view.test_func() is False

    def test_job_details_and_update_view_access(self, rf: RequestFactory) -> None:
        """Verify job access for assigned bookkeeper, manager, and unassigned bookkeeper."""
        manager = BWUser.objects.create_user(
            email="mgr_job@example.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        bk_assigned = BWUser.objects.create_user(
            email="bk_job1@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        bk_unassigned = BWUser.objects.create_user(
            email="bk_job2@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )

        client = ClientProxy.objects.create(name="Beta Inc")
        client.bookkeepers.add(bk_assigned.bookkeeper.get_proxy_model())
        job = JobProxy.objects.create(
            title="Tax Return 2026",
            client=client,
            managed_by=bk_assigned,
        )

        view_details = JobDetailsView()
        view_details.kwargs = {"pk": job.pk}
        view_details.object = job

        # Manager
        req_mgr = rf.get(f"/job/{job.pk}/")
        req_mgr.user = manager
        view_details.request = req_mgr
        assert view_details.test_func() is True

        # Assigned bookkeeper
        req_assigned = rf.get(f"/job/{job.pk}/")
        req_assigned.user = bk_assigned
        view_details.request = req_assigned
        assert view_details.test_func() is True

        # Unassigned bookkeeper
        req_unassigned = rf.get(f"/job/{job.pk}/")
        req_unassigned.user = bk_unassigned
        view_details.request = req_unassigned
        assert view_details.test_func() is False

        # JobUpdateView
        view_update = JobUpdateView()
        view_update.kwargs = {"pk": job.pk}
        view_update.object = job

        view_update.request = req_assigned
        assert view_update.test_func() is True

        view_update.request = req_unassigned
        assert view_update.test_func() is False

    def test_important_contact_list_cfo_scoping(self, rf: RequestFactory) -> None:
        """Verify ImportantContactListView scopes properly for CFOs without crashing."""
        cfo_user = BWUser.objects.create_user(
            email="cfo_contact@example.com",
            password="ValidPassword123!",
            user_type=CON_CFO,
        )
        cfo_proxy = cfo_user.cfo.get_proxy_model()

        client_assigned = ClientProxy.objects.create(name="Assigned Client")
        client_unassigned = ClientProxy.objects.create(name="Unassigned Client")

        client_assigned.cfos.add(cfo_proxy)

        contact_assigned = ImportantContact.objects.create(
            contact_label="ceo",
            contact_first_name="Alice",
            contact_last_name="Smith",
            contact_email="alice@assigned.com",
            company_name="Assigned Client",
        )
        client_assigned.important_contacts.add(contact_assigned)

        contact_unassigned = ImportantContact.objects.create(
            contact_label="payroll",
            contact_first_name="Bob",
            contact_last_name="Jones",
            contact_email="bob@unassigned.com",
            company_name="Unassigned Client",
        )
        client_unassigned.important_contacts.add(contact_unassigned)

        view = ImportantContactListViewBW()
        req = rf.get("/important_contact/list/")
        req.user = cfo_user
        view.request = req

        qs = view.get_queryset()
        assert contact_assigned in qs
        assert contact_unassigned not in qs

