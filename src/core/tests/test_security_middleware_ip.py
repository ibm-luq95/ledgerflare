"""Tests verifying secure client IP extraction and file validation."""

from __future__ import annotations

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import RequestFactory, override_settings

from beach_wood_user.models import BWUser
from core.choices import BeachWoodUserTypeEnum
from core.middleware.security_logging import get_client_ip
from discussion.views import DiscussionCreateHtmxView


@pytest.fixture(autouse=True)
def setup_groups(db: None) -> None:
    call_command("create_groups")


class TestClientIpAndUploadSecurity:
    """Verify IP extraction prevents header spoofing and upload validation enforces boundaries."""

    def test_client_ip_defaults_to_remote_addr_ignoring_spoofed_forwarded_for(
        self, rf: RequestFactory
    ) -> None:
        """When not configured as a trusted proxy, X-Forwarded-For header must be ignored."""
        request = rf.get(
            "/",
            REMOTE_ADDR="198.51.100.1",
            HTTP_X_FORWARDED_FOR="203.0.113.195, 10.0.0.1",
        )
        with override_settings(
            USE_X_FORWARDED_HOST=False, SECURE_PROXY_SSL_HEADER=None
        ):
            extracted_ip = get_client_ip(request)
            assert extracted_ip == "198.51.100.1"

    def test_client_ip_uses_rightmost_forwarded_for_when_trusted(
        self, rf: RequestFactory
    ) -> None:
        """When behind trusted reverse proxy, extracts rightmost upstream IP."""
        request = rf.get(
            "/",
            REMOTE_ADDR="127.0.0.1",
            HTTP_X_FORWARDED_FOR="203.0.113.195, 198.51.100.5",
        )
        with override_settings(USE_X_FORWARDED_HOST=True):
            extracted_ip = get_client_ip(request)
            assert extracted_ip == "198.51.100.5"

    @pytest.mark.django_db
    def test_discussion_view_rejects_disallowed_file_types(
        self, rf: RequestFactory
    ) -> None:
        """Uploading an executable or unsupported file in discussion returns 400 Bad Request."""
        user = BWUser.objects.create_user(
            email="uploader@example.com",
            password="ValidPassword123!",
            user_type=BeachWoodUserTypeEnum.MANAGER,
        )
        bad_file = SimpleUploadedFile(
            "malicious.exe",
            b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00",
            content_type="application/x-msdownload",
        )
        request = rf.post(
            "/notifications/htmx/create/",
            {"body": "Check this file", "attachment": bad_file},
        )
        request.user = user
        from django.contrib.sessions.backends.db import SessionStore

        request.session = SessionStore()

        view = DiscussionCreateHtmxView.as_view()
        response = view(request)
        assert response.status_code == 400
