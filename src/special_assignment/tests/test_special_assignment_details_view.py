from __future__ import annotations

from typing import Any

import pytest
from django.contrib.sites.models import Site
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.urls import reverse
from model_bakery import baker

from beach_wood_user.models import BWUser
from client.models import ClientProxy
from core.constants.users import CON_BOOKKEEPER, CON_MANAGER
from job.models import JobProxy
from special_assignment.models import SpecialAssignmentProxy


@pytest.fixture(autouse=True)
def setup_test_environment(db: Any) -> None:
    """Ensure Django auth groups and sites exist before running tests."""
    call_command("create_groups")
    Site.objects.get_or_create(domain="testserver", defaults={"name": "testserver"})


@pytest.mark.django_db
class TestSpecialAssignmentDetailsView:
    """Test suite for SpecialAssignmentDetailsView."""

    def test_manager_can_access_details_view_with_full_metadata(self, client):
        manager = BWUser.objects.create_user(
            email="manager@ledgerflare.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        bookkeeper = BWUser.objects.create_user(
            email="bookkeeper@ledgerflare.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        test_client = baker.make(ClientProxy, name="Acme Corporation")
        test_job = baker.make(JobProxy, title="Year-End Audit 2026", client=test_client)
        attachment = SimpleUploadedFile(
            "sample_statement.pdf",
            b"%PDF-1.4 sample content",
            content_type="application/pdf",
        )

        assignment = baker.make(
            SpecialAssignmentProxy,
            title="Q3 Tax Preparation",
            body="<p>Full assignment description content</p>",
            notes="Critical note: review reconciliation report.",
            status="in_progress",
            assigned_by=manager,
            assigned_to=bookkeeper,
            client=test_client,
            job=test_job,
            attachment=attachment,
            is_seen=True,
        )

        client.force_login(manager)
        url = reverse(
            "dashboard:special_assignment:details", kwargs={"pk": assignment.pk}
        )
        response = client.get(url)

        assert response.status_code == 200
        assert "special_assignment/details.html" in [t.name for t in response.templates]
        assert response.context["object"] == assignment
        assert "SA - Q3 Tax Preparation" in response.context["title"]

        content = response.content.decode("utf-8")
        assert "Q3 Tax Preparation" in content
        assert "Full assignment description content" in content
        assert "Critical note: review reconciliation report." in content
        assert "Acme Corporation" in content
        assert "Year-End Audit 2026" in content
        assert "sample_statement" in content
        assert "Assignment Lifecycle" in content
        assert (
            "Team Discussion &amp; Activity" in content
            or "Team Discussion & Activity" in content
        )

    def test_unauthenticated_user_redirected(self, client):
        manager = BWUser.objects.create_user(
            email="manager2@ledgerflare.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        bookkeeper = BWUser.objects.create_user(
            email="bookkeeper2@ledgerflare.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        assignment = baker.make(
            SpecialAssignmentProxy,
            title="Confidential Review",
            assigned_by=manager,
            assigned_to=bookkeeper,
        )
        url = reverse(
            "dashboard:special_assignment:details", kwargs={"pk": assignment.pk}
        )
        response = client.get(url)

        assert response.status_code == 302
        assert "/auth/login" in response.url
