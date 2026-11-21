from __future__ import annotations

from typing import Any

import pytest
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.test import Client as DjangoTestClient
from django.urls import reverse
from model_bakery import baker

from beach_wood_user.models import BWUser
from client.models import ClientProxy
from core.choices import NoteSectionEnum
from core.constants.site_settings import SITE_SETTINGS_DB_SLUG
from core.constants.users import CON_MANAGER
from job.models import JobProxy
from note.models import NoteProxy
from note.services import NoteExportService
from site_settings.models import SiteSettings


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def setup_test_environment(db: Any) -> None:
    call_command("create_groups")
    SiteSettings.objects.get_or_create(
        slug=SITE_SETTINGS_DB_SLUG,
        defaults={"name": "LedgerFlare", "email": "info@ledgerflare.com"},
    )
    Site.objects.get_or_create(domain="testserver", defaults={"name": "testserver"})


def test_note_export_service_csv() -> None:
    client = ClientProxy.objects.create(name="Omega Corp")
    job = baker.make(JobProxy, title="Audit 2026", client=client)
    baker.make(
        NoteProxy,
        title="CSV Note",
        body="<p>Body text</p>",
        client=client,
        job=job,
        note_section=NoteSectionEnum.JOB,
        is_deleted=False,
    )

    service = NoteExportService()
    response = service.export_csv(NoteProxy.objects.all())

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv; charset=utf-8"
    assert "attachment; filename=" in response["Content-Disposition"]
    content = response.content.decode("utf-8")
    assert "CSV Note" in content
    assert "Omega Corp" in content
    assert "Audit 2026" in content


def test_note_export_service_xlsx() -> None:
    client = ClientProxy.objects.create(name="Omega Corp")
    baker.make(
        NoteProxy,
        title="XLSX Note",
        body="<p>Body text</p>",
        client=client,
        note_section=NoteSectionEnum.CLIENT,
        is_deleted=False,
    )

    service = NoteExportService()
    response = service.export_xlsx(NoteProxy.objects.all())

    assert response.status_code == 200
    assert (
        response["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert "attachment; filename=" in response["Content-Disposition"]
    assert len(response.content) > 0


def test_note_export_csv_view(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    baker.make(NoteProxy, title="Note CSV View", is_deleted=False)

    client = DjangoTestClient()
    client.force_login(admin_user)

    url = reverse("dashboard:note:export_csv")
    response = client.get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv; charset=utf-8"
    assert "Note CSV View" in response.content.decode("utf-8")


def test_note_export_excel_view(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    baker.make(NoteProxy, title="Note Excel View", is_deleted=False)

    client = DjangoTestClient()
    client.force_login(admin_user)

    url = reverse("dashboard:note:export_excel")
    response = client.get(url)

    assert response.status_code == 200
    assert (
        response["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def test_note_export_unified_view(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    baker.make(NoteProxy, title="Unified Note Export", is_deleted=False)

    client = DjangoTestClient()
    client.force_login(admin_user)

    url = reverse("dashboard:note:export") + "?format=xlsx"
    response = client.get(url)
    assert response.status_code == 200
    assert (
        response["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    url_csv = reverse("dashboard:note:export") + "?format=csv"
    response_csv = client.get(url_csv)
    assert response_csv.status_code == 200
    assert response_csv["Content-Type"] == "text/csv; charset=utf-8"
