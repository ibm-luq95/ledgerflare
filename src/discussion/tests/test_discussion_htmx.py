from __future__ import annotations

from typing import Any

import pytest
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.urls import reverse
from model_bakery import baker

from beach_wood_user.models import BWUser
from client.models import ClientProxy
from core.constants.users import CON_BOOKKEEPER, CON_MANAGER
from discussion.models import DiscussionProxy
from job.models import JobProxy
from special_assignment.models import SpecialAssignmentProxy


@pytest.fixture(autouse=True)
def setup_test_environment(db: Any) -> None:
    """Ensure Django auth groups and sites exist before running tests."""
    call_command("create_groups")
    Site.objects.get_or_create(domain="testserver", defaults={"name": "testserver"})


@pytest.mark.django_db
class TestDiscussionCreateHtmxView:
    """Test suite for DiscussionCreateHtmxView."""

    def test_unauthenticated_request_redirects_to_login(self, client):
        url = reverse("dashboard:discussion:htmx_create")
        response = client.post(url, {"body": "Hello World", "job": "dummy-id"})
        assert response.status_code == 302
        assert "/auth/login" in response.url

    def test_manager_can_post_discussion_to_special_assignment(self, client):
        manager = BWUser.objects.create_user(
            email="manager_htmx@ledgerflare.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        bookkeeper = BWUser.objects.create_user(
            email="bookkeeper_htmx@ledgerflare.com",
            password="ValidPassword123!",
            user_type=CON_BOOKKEEPER,
        )
        test_client = baker.make(ClientProxy, name="Acme Corp", is_deleted=False)
        assignment = baker.make(
            SpecialAssignmentProxy,
            title="Audit 2026",
            assigned_by=manager,
            assigned_to=bookkeeper,
            client=test_client,
            is_deleted=False,
        )

        client.force_login(manager)
        url = reverse("dashboard:discussion:htmx_create")
        response = client.post(
            url,
            {
                "body": "Manager update on assignment progress",
                "special_assignment": str(assignment.pk),
            },
        )

        assert response.status_code == 200
        assert "Manager update on assignment progress" in response.content.decode(
            "utf-8"
        )
        disc = DiscussionProxy.objects.filter(
            special_assignment=assignment,
            sender=manager,
        ).first()
        assert disc is not None
        assert disc.body == "Manager update on assignment progress"

    def test_manager_can_post_discussion_to_job(self, client):
        manager = BWUser.objects.create_user(
            email="manager_job_htmx@ledgerflare.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        test_client = ClientProxy.objects.create(name="Tech Solutions")
        job = JobProxy.objects.create(
            title="Monthly Reconciliation",
            client=test_client,
        )

        client.force_login(manager)
        url = reverse("dashboard:discussion:htmx_create")
        response = client.post(
            url,
            {
                "body": "Job reconciliation started",
                "job": str(job.pk),
            },
        )

        assert response.status_code == 200
        assert "Job reconciliation started" in response.content.decode("utf-8")
        disc = DiscussionProxy.objects.filter(
            job=job,
            sender=manager,
        ).first()
        assert disc is not None
        assert disc.body == "Job reconciliation started"

    def test_xss_content_is_sanitized(self, client):
        manager = BWUser.objects.create_user(
            email="manager_xss@ledgerflare.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        test_client = ClientProxy.objects.create(name="Secure Client")
        job = JobProxy.objects.create(title="Tax Review", client=test_client)

        client.force_login(manager)
        url = reverse("dashboard:discussion:htmx_create")
        malicious_input = '<p>Normal text</p><script>alert("xss")</script><img src="x" onerror="alert(1)">'
        response = client.post(
            url,
            {
                "body": malicious_input,
                "job": str(job.pk),
            },
        )

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "<script>" not in content
        assert "onerror" not in content
        assert "Normal text" in content

    def test_empty_body_and_no_attachment_returns_bad_request(self, client):
        manager = BWUser.objects.create_user(
            email="manager_empty@ledgerflare.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        test_client = ClientProxy.objects.create(name="Empty Client")
        job = JobProxy.objects.create(title="Empty Test", client=test_client)

        client.force_login(manager)
        url = reverse("dashboard:discussion:htmx_create")
        response = client.post(
            url,
            {
                "body": "   ",
                "job": str(job.pk),
            },
        )

        assert response.status_code == 400

    def test_vue_api_endpoint_list_discussions(self, client):
        manager = BWUser.objects.create_user(
            email="manager_api_list@ledgerflare.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        test_client = ClientProxy.objects.create(name="API Client")
        job = JobProxy.objects.create(title="API Job", client=test_client)
        DiscussionProxy.objects.create(
            job=job,
            sender=manager,
            body="Existing discussion from manager",
        )

        client.force_login(manager)
        url = reverse("dashboard:discussion:api:discussion-api-router-list")
        response = client.get(url, {"job": str(job.pk)})

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["body"] == "Existing discussion from manager"
        assert data[0]["sender_name"] == manager.fullname or manager.username
        assert "sender_avatar" in data[0]

    def test_vue_api_endpoint_post_discussion(self, client):
        manager = BWUser.objects.create_user(
            email="manager_api_post@ledgerflare.com",
            password="ValidPassword123!",
            user_type=CON_MANAGER,
        )
        test_client = ClientProxy.objects.create(name="API Post Client")
        job = JobProxy.objects.create(title="API Post Job", client=test_client)

        client.force_login(manager)
        url = reverse("dashboard:discussion:api:discussion-api-router-list")
        response = client.post(
            url,
            {
                "body": "Vue 3 message posted via DRF API",
                "job": str(job.pk),
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["body"] == "Vue 3 message posted via DRF API"
        disc = DiscussionProxy.objects.filter(
            job=job,
            sender=manager,
        ).first()
        assert disc is not None
        assert disc.body == "Vue 3 message posted via DRF API"
