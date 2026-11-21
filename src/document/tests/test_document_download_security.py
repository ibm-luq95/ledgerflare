"""Security tests for DocumentDownloadView object-level authorization."""

from __future__ import annotations

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import RequestFactory

from beach_wood_user.models import BWUser
from client.models import ClientProxy
from core.constants.users import CON_BOOKKEEPER, CON_MANAGER
from core.views.mixins.authorization import BWObjectAccessRequiredMixin
from document.models import DocumentProxy
from document.views import DocumentDownloadView


@pytest.fixture(autouse=True)
def setup_groups(db: None) -> None:
    """Ensure Django auth groups exist before running object tests."""
    call_command("create_groups")


@pytest.mark.django_db
class TestDocumentDownloadSecurity:
    """Verify that DocumentDownloadView enforces BWObjectAccessRequiredMixin."""

    def test_view_inherits_object_access_mixin(self) -> None:
        """DocumentDownloadView must inherit BWObjectAccessRequiredMixin."""
        assert issubclass(DocumentDownloadView, BWObjectAccessRequiredMixin)

    def test_unassigned_bookkeeper_denied_download(self, rf: RequestFactory) -> None:
        """Unassigned bookkeeper cannot download document for an unassigned client."""
        bk_assigned = BWUser.objects.create_user(
            email="bk_doc_assigned@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        bk_unassigned = BWUser.objects.create_user(
            email="bk_doc_unassigned@example.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )

        client = ClientProxy.objects.create(name="Secure Client")
        client.bookkeepers.add(bk_assigned.bookkeeper.get_proxy_model())

        doc = DocumentProxy.objects.create(
            title="Confidential Tax Sheet",
            client=client,
            document_file=SimpleUploadedFile(
                "tax.pdf", b"%PDF-1.4 mock", content_type="application/pdf"
            ),
        )

        view = DocumentDownloadView()
        view.kwargs = {"pk": doc.pk}

        # Assigned bookkeeper
        req_assigned = rf.get(f"/document/download/{doc.pk}/")
        req_assigned.user = bk_assigned
        view.request = req_assigned
        assert view.test_func() is True

        # Unassigned bookkeeper
        req_unassigned = rf.get(f"/document/download/{doc.pk}/")
        req_unassigned.user = bk_unassigned
        view.request = req_unassigned
        assert view.test_func() is False
