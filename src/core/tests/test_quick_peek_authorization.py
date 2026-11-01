"""Unit tests for Quick-Peek slide-over object-level authorization."""

from __future__ import annotations

import pytest
from django.core.management import call_command
from django.test import RequestFactory

from beach_wood_user.models import BWUser
from client.models import ClientProxy
from client.views import ClientQuickPeekView
from core.constants.users import CON_BOOKKEEPER, CON_MANAGER
from core.views.mixins.authorization import BWObjectAccessRequiredMixin
from important_contact.models import ImportantContact
from important_contact.views import ImportantContactQuickPeekView
from job.models import JobProxy
from job.views import JobQuickPeekView
from note.models import Note
from note.views import NoteQuickPeekView
from special_assignment.models import SpecialAssignmentProxy
from special_assignment.views import SpecialAssignmentQuickPeekView
from task.models import TaskProxy
from task.views import TaskQuickPeekView


@pytest.fixture(autouse=True)
def setup_groups(db: None) -> None:
    """Ensure Django auth groups exist before running object tests."""
    call_command("create_groups")


@pytest.mark.django_db
class TestQuickPeekAuthorization:
    """Verify that all 6 Quick-Peek slide-overs enforce BWObjectAccessRequiredMixin."""

    def test_quick_peek_views_inherit_mixin(self) -> None:
        """All Quick-Peek views must inherit BWObjectAccessRequiredMixin."""
        assert issubclass(JobQuickPeekView, BWObjectAccessRequiredMixin)
        assert issubclass(ClientQuickPeekView, BWObjectAccessRequiredMixin)
        assert issubclass(TaskQuickPeekView, BWObjectAccessRequiredMixin)
        assert issubclass(NoteQuickPeekView, BWObjectAccessRequiredMixin)
        assert issubclass(ImportantContactQuickPeekView, BWObjectAccessRequiredMixin)
        assert issubclass(SpecialAssignmentQuickPeekView, BWObjectAccessRequiredMixin)

    def test_job_quick_peek_access_control(self, rf: RequestFactory) -> None:
        """Verify unassigned bookkeeper cannot access JobQuickPeekView."""
        manager = BWUser.objects.create_user(
            email="mgr_qp@example.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        bk_assigned = BWUser.objects.create_user(
            email="bk_qp1@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        bk_unassigned = BWUser.objects.create_user(
            email="bk_qp2@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )

        client = ClientProxy.objects.create(name="QP Client Alpha")
        client.bookkeepers.add(bk_assigned.bookkeeper.get_proxy_model())
        job = JobProxy.objects.create(title="QP Job", client=client)

        view = JobQuickPeekView()
        view.kwargs = {"pk": job.pk}
        view.object = job

        req_mgr = rf.get(f"/job/{job.pk}/quick-peek")
        req_mgr.user = manager
        view.request = req_mgr
        assert view.test_func() is True

        req_assigned = rf.get(f"/job/{job.pk}/quick-peek")
        req_assigned.user = bk_assigned
        view.request = req_assigned
        assert view.test_func() is True

        req_unassigned = rf.get(f"/job/{job.pk}/quick-peek")
        req_unassigned.user = bk_unassigned
        view.request = req_unassigned
        assert view.test_func() is False

    def test_client_quick_peek_access_control(self, rf: RequestFactory) -> None:
        """Verify unassigned bookkeeper cannot access ClientQuickPeekView."""
        bk_assigned = BWUser.objects.create_user(
            email="bk_client_qp1@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        bk_unassigned = BWUser.objects.create_user(
            email="bk_client_qp2@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )

        client = ClientProxy.objects.create(name="QP Client Beta")
        client.bookkeepers.add(bk_assigned.bookkeeper.get_proxy_model())

        view = ClientQuickPeekView()
        view.kwargs = {"pk": client.pk}
        view.object = client

        req_assigned = rf.get(f"/client/{client.pk}/quick-peek/")
        req_assigned.user = bk_assigned
        view.request = req_assigned
        assert view.test_func() is True

        req_unassigned = rf.get(f"/client/{client.pk}/quick-peek/")
        req_unassigned.user = bk_unassigned
        view.request = req_unassigned
        assert view.test_func() is False
