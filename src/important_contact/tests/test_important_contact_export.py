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
from core.choices import ImportantContactLabelsEnum
from core.constants.site_settings import SITE_SETTINGS_DB_SLUG
from core.constants.users import CON_MANAGER
from important_contact.models import ImportantContactProxy
from important_contact.services import ImportantContactExportService
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


def test_important_contact_export_service_csv() -> None:
    client = ClientProxy.objects.create(name="Wayne Enterprises")
    contact = baker.make(
        ImportantContactProxy,
        contact_first_name="Lucius",
        contact_last_name="Fox",
        company_name="Wayne Tech",
        contact_email="lucius@wayne.com",
        contact_phone="+1-555-0100",
        contact_label=ImportantContactLabelsEnum.CEO,
        is_deleted=False,
    )
    client.important_contacts.add(contact)

    service = ImportantContactExportService()
    response = service.export_csv(
        ImportantContactProxy.objects.prefetch_related("client")
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv; charset=utf-8"
    assert "attachment; filename=" in response["Content-Disposition"]
    content = response.content.decode("utf-8")
    assert "Lucius Fox" in content
    assert "Wayne Tech" in content
    assert "Wayne Enterprises" in content


def test_important_contact_export_service_xlsx() -> None:
    client = ClientProxy.objects.create(name="Wayne Enterprises")
    contact = baker.make(
        ImportantContactProxy,
        contact_first_name="Alfred",
        contact_last_name="Pennyworth",
        company_name="Wayne Manor",
        contact_email="alfred@wayne.com",
        contact_label=ImportantContactLabelsEnum.OTHER,
        is_deleted=False,
    )
    client.important_contacts.add(contact)

    service = ImportantContactExportService()
    response = service.export_xlsx(
        ImportantContactProxy.objects.prefetch_related("client")
    )

    assert response.status_code == 200
    assert (
        response["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert "attachment; filename=" in response["Content-Disposition"]
    assert len(response.content) > 0


def test_important_contact_export_csv_view(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    baker.make(
        ImportantContactProxy,
        contact_first_name="Diana",
        contact_last_name="Prince",
        contact_email="diana@example.com",
        is_deleted=False,
    )

    client = DjangoTestClient()
    client.force_login(admin_user)

    url = reverse("dashboard:important_contact:export_csv")
    response = client.get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv; charset=utf-8"
    assert "Diana Prince" in response.content.decode("utf-8")


def test_important_contact_export_excel_view(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    baker.make(
        ImportantContactProxy,
        contact_first_name="Clark",
        contact_last_name="Kent",
        contact_email="clark@example.com",
        is_deleted=False,
    )

    client = DjangoTestClient()
    client.force_login(admin_user)

    url = reverse("dashboard:important_contact:export_excel")
    response = client.get(url)

    assert response.status_code == 200
    assert (
        response["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def test_important_contact_export_unified_view(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    baker.make(
        ImportantContactProxy,
        contact_first_name="Barry",
        contact_last_name="Allen",
        contact_email="barry@example.com",
        is_deleted=False,
    )

    client = DjangoTestClient()
    client.force_login(admin_user)

    url = reverse("dashboard:important_contact:export") + "?format=xlsx"
    response = client.get(url)
    assert response.status_code == 200
    assert (
        response["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    url_csv = reverse("dashboard:important_contact:export") + "?format=csv"
    response_csv = client.get(url_csv)
    assert response_csv.status_code == 200
    assert response_csv["Content-Type"] == "text/csv; charset=utf-8"
