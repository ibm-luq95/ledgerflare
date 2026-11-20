"""Tests for special assignment and profile image malware validation."""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import patch

import pytest
from django.contrib.sites.models import Site
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from model_bakery import baker

from beach_wood_user.models import BWUser
from core.services.malware_scanner import MalwareDetectedError
from special_assignment.forms import MiniSpecialAssignmentForm


@pytest.fixture(autouse=True)
def setup_test_environment(db: Any) -> None:
    """Ensure Django auth groups and sites exist before running tests."""
    call_command("create_groups")
    Site.objects.get_or_create(domain="testserver", defaults={"name": "testserver"})


@pytest.mark.django_db
def test_special_assignment_mini_form_rejects_infected_attachment() -> None:
    """Verify MiniSpecialAssignmentForm rejects infected attachment with validation error."""
    user = baker.make(BWUser)
    assigned_by = baker.make(BWUser)
    eicar = SimpleUploadedFile(
        "threat.pdf",
        b"%PDF-1.4\nEICAR payload test",
        content_type="application/pdf",
    )
    form = MiniSpecialAssignmentForm(
        data={
            "title": "Tax Audit Assignment",
            "body": "<p>Review tax schedule</p>",
            "assigned_to": str(user.pk),
            "assigned_by": str(assigned_by.pk),
            "start_date": "2026-01-01",
            "due_date": "2026-01-15",
        },
        files={"attachment": eicar},
    )
    with patch(
        "core.services.malware_scanner.ClamAVScanner.scan_stream",
        side_effect=MalwareDetectedError("Malware detected by scanner: Win.Test.EICAR"),
    ):
        assert not form.is_valid()
        assert "attachment" in form.errors
        assert any("Malware detected" in str(msg) for msg in form.errors["attachment"])


@pytest.mark.django_db
def test_special_assignment_mini_form_accepts_clean_attachment() -> None:
    """Verify MiniSpecialAssignmentForm accepts clean attachment."""
    user = baker.make(BWUser)
    assigned_by = baker.make(BWUser)
    clean = SimpleUploadedFile(
        "clean.pdf",
        b"%PDF-1.4\nClean assignment PDF",
        content_type="application/pdf",
    )
    form = MiniSpecialAssignmentForm(
        data={
            "title": "Tax Audit Assignment",
            "body": "<p>Review tax schedule</p>",
            "assigned_to": str(user.pk),
            "assigned_by": str(assigned_by.pk),
            "start_date": "2026-01-01",
            "due_date": "2026-01-15",
        },
        files={"attachment": clean},
    )
    with patch("core.services.malware_scanner.ClamAVScanner.scan_stream"):
        assert form.is_valid()
