"""Unit tests for staff briefcase isolation and API role scoping."""
from __future__ import annotations

import pytest
from django.core.management import call_command
from django.test import RequestFactory
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from beach_wood_user.models import BWUser
from bookkeeper.models import BookkeeperProxy
from cfo.models import CFOProxy
from client.models import ClientProxy
from client.views.api import ClientDropdownView, ClientViewSet
from core.constants.users import (
    CON_BOOKKEEPER,
    CON_CFO,
    CON_MANAGER,
)
from staff_briefcase.models import StaffBriefcase, StaffDocuments, StaffNotes
from staff_briefcase.views.briefcase import (
    StaffBriefcaseDetailView,
    StaffBriefcaseListView,
)
from staff_briefcase.views.documents.api import StaffDocumentsViewSet
from staff_briefcase.views.notes.api import StaffNotesViewSet


@pytest.fixture(autouse=True)
def setup_groups(db: None) -> None:
    """Ensure Django auth groups exist."""
    call_command("create_groups")


@pytest.mark.django_db
class TestStaffBriefcasePermissions:
    """Test suite verifying briefcase isolation and API role boundaries."""

    def test_briefcase_list_and_details_isolation(self, rf: RequestFactory) -> None:
        """Verify staff members can only access their own briefcase."""
        manager = BWUser.objects.create_user(
            email="mgr_bc@example.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        staff1 = BWUser.objects.create_user(
            email="staff1@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        staff2 = BWUser.objects.create_user(
            email="staff2@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )

        bc1 = StaffBriefcase.objects.get(user=staff1)
        bc2 = StaffBriefcase.objects.get(user=staff2)

        # ListView scoping
        list_view = StaffBriefcaseListView()
        req1 = rf.get("/briefcase/")
        req1.user = staff1
        list_view.request = req1
        staff1_qs = list_view.get_queryset()
        assert bc1 in staff1_qs
        assert bc2 not in staff1_qs

        # DetailView object permission
        detail_view = StaffBriefcaseDetailView()
        detail_view.kwargs = {"pk": bc2.pk}
        detail_view.object = bc2

        # Staff 1 trying to access Staff 2 briefcase
        detail_view.request = req1
        assert detail_view.test_func() is False

        # Staff 2 accessing own briefcase
        req2 = rf.get(f"/briefcase/{bc2.pk}/")
        req2.user = staff2
        detail_view.request = req2
        assert detail_view.test_func() is True

        # Manager accessing Staff 2 briefcase
        req_mgr = rf.get(f"/briefcase/{bc2.pk}/")
        req_mgr.user = manager
        detail_view.request = req_mgr
        assert detail_view.test_func() is True

    def test_staff_documents_and_notes_api_scoping(self) -> None:
        """Verify API ViewSets scope documents and notes per briefcase owner."""
        staff1 = BWUser.objects.create_user(
            email="staff_api1@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        staff2 = BWUser.objects.create_user(
            email="staff_api2@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )

        bc1 = StaffBriefcase.objects.get(user=staff1)
        bc2 = StaffBriefcase.objects.get(user=staff2)

        doc1 = StaffDocuments.objects.create(
            title="Doc Staff 1",
            document_file="staff_documents/test1.pdf",
        )
        bc1.documents.add(doc1)

        doc2 = StaffDocuments.objects.create(
            title="Doc Staff 2",
            document_file="staff_documents/test2.pdf",
        )
        bc2.documents.add(doc2)

        note1 = StaffNotes.objects.create(
            title="Note Staff 1",
            note="Confidential note 1",
        )
        bc1.notes.add(note1)

        note2 = StaffNotes.objects.create(
            title="Note Staff 2",
            note="Confidential note 2",
        )
        bc2.notes.add(note2)

        api_rf = APIRequestFactory()

        # Documents ViewSet for Staff 1
        doc_view = StaffDocumentsViewSet.as_view({"get": "list"})
        req_doc = api_rf.get("/staff_briefcase/api/documents-api/")
        force_authenticate(req_doc, user=staff1)
        res_doc = doc_view(req_doc)
        assert (
            res_doc.status_code == status.HTTP_200_OK
        ), f"Doc error: {res_doc.data if hasattr(res_doc, 'data') else res_doc.content}"
        doc_titles = [d["title"] for d in res_doc.data["results"]]
        assert "Doc Staff 1" in doc_titles
        assert "Doc Staff 2" not in doc_titles

        # Notes ViewSet for Staff 1
        note_view = StaffNotesViewSet.as_view({"get": "list"})
        req_note = api_rf.get("/staff_briefcase/api/notes-api/")
        force_authenticate(req_note, user=staff1)
        res_note = note_view(req_note)
        assert res_note.status_code == status.HTTP_200_OK
        note_titles = [n["title"] for n in res_note.data["results"]]
        assert "Note Staff 1" in note_titles
        assert "Note Staff 2" not in note_titles

    def test_client_api_assign_staff_permission(self) -> None:
        """Verify non-managers cannot assign staff to clients via API."""
        manager = BWUser.objects.create_user(
            email="mgr_assign@example.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        bk = BWUser.objects.create_user(
            email="bk_assign@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        client = ClientProxy.objects.create(name="Assign Test Client")

        api_rf = APIRequestFactory()
        assign_view = ClientViewSet.as_view({"post": "assign_bookkeeper"})

        # Bookkeeper attempting assignment -> 403 Forbidden
        req_bk = api_rf.post(
            "/client/api/client-api/assign_bookkeeper/",
            {"client": str(client.pk), "bookkeepers": [str(bk.bookkeeper.pk)]},
            format="json",
        )
        force_authenticate(req_bk, user=bk)
        res_bk = assign_view(req_bk)
        assert res_bk.status_code == status.HTTP_403_FORBIDDEN

        # Manager attempting assignment -> 200 OK
        req_mgr = api_rf.post(
            "/client/api/client-api/assign_bookkeeper/",
            {"client": str(client.pk), "bookkeepers": [str(bk.bookkeeper.pk)]},
            format="json",
        )
        force_authenticate(req_mgr, user=manager)
        res_mgr = assign_view(req_mgr)
        assert res_mgr.status_code == status.HTTP_200_OK, f"Error: {res_mgr.data}"
        client.refresh_from_db()
        assert bk.bookkeeper.get_proxy_model() in client.bookkeepers.all()

    def test_briefcase_detail_view_renders_cleanly(self, client) -> None:
        """Verify StaffBriefcaseDetailView renders all sections, tabs, and modals."""
        from django.urls import reverse

        manager = BWUser.objects.create_user(
            email="mgr_render@example.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        bc = StaffBriefcase.objects.get(user=manager)
        client.force_login(manager)
        url = reverse("dashboard:briefcase:details", kwargs={"pk": bc.pk})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Personal Working Notes" in content
        assert "Briefcase Documents &amp; Attachments" in content or "Briefcase Documents & Attachments" in content
        assert "Encrypted Credential Vault" in content
        assert "createBriefcaseNoteModal" in content
        assert "createBriefcaseDocumentModal" in content
        assert "createBriefcaseAccountModal" in content

    def test_staff_accounts_api_create(self, client) -> None:
        from django.urls import reverse
        from rest_framework.authtoken.models import Token

        manager = BWUser.objects.create_user(
            email="mgr_acc_api@example.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        token, _ = Token.objects.get_or_create(user=manager)
        bc = StaffBriefcase.objects.get(user=manager)
        url = reverse("dashboard:briefcase:briefcase_staff_accounts:api:staff-accounts-api-router-list")
        
        # Test with a valid ServiceNameEnum choice:
        payload = {
            "title": "QuickBooks Online Login",
            "name": "quickbooks_online",
            "url": "https://qbo.intuit.com",
            "username_email": "admin@quickbooks.com",
            "password": "SecretPassword123!",
            "briefcase": str(bc.pk),
        }
        response = client.post(
            url,
            payload,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "QuickBooks Online Login"

        # Test with optional/empty name:
        payload_empty_name = {
            "title": "Custom Portal",
            "name": "",
            "url": "https://custom.portal.com",
            "username_email": "user@portal.com",
            "password": "SecretPassword456!",
            "briefcase": str(bc.pk),
        }
        response2 = client.post(
            url,
            payload_empty_name,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )
        assert response2.status_code == 201

