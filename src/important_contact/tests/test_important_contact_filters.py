from __future__ import annotations

from typing import Any

import pytest
from django.contrib.sites.models import Site
from django.core.management import call_command
from model_bakery import baker

from client.models import ClientProxy
from core.choices import ImportantContactLabelsEnum
from core.constants.site_settings import SITE_SETTINGS_DB_SLUG
from important_contact.filters import ImportantContactFilter
from important_contact.models import ImportantContactProxy
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


def test_important_contact_filter_by_label_and_names() -> None:
    client = ClientProxy.objects.create(name="Epsilon Ventures")
    c1 = baker.make(
        ImportantContactProxy,
        contact_first_name="Arthur",
        contact_last_name="Dent",
        company_name="Magrathea Inc",
        contact_email="arthur@example.com",
        contact_label=ImportantContactLabelsEnum.PAYROLL,
        is_deleted=False,
    )
    client.important_contacts.add(c1)

    baker.make(
        ImportantContactProxy,
        contact_first_name="Ford",
        contact_last_name="Prefect",
        company_name="Betelgeuse Corp",
        contact_email="ford@example.com",
        contact_label=ImportantContactLabelsEnum.CEO,
        is_deleted=False,
    )

    # Filter by label
    filterset = ImportantContactFilter(
        {"contact_label": ImportantContactLabelsEnum.PAYROLL},
        queryset=ImportantContactProxy.objects.all(),
    )
    assert filterset.qs.count() == 1
    assert filterset.qs.first().contact_first_name == "Arthur"

    # Filter by first name keyword
    filterset = ImportantContactFilter(
        {"contact_first_name": "ford"},
        queryset=ImportantContactProxy.objects.all(),
    )
    assert filterset.qs.count() == 1
    assert filterset.qs.first().contact_first_name == "Ford"

    # Filter by company name keyword
    filterset = ImportantContactFilter(
        {"company_name": "magrathea"},
        queryset=ImportantContactProxy.objects.all(),
    )
    assert filterset.qs.count() == 1
    assert filterset.qs.first().company_name == "Magrathea Inc"
