from __future__ import annotations

from typing import Any

import pytest
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.test import RequestFactory
from django.urls import reverse
from model_bakery import baker

from beach_wood_user.models import BWUser
from client.models import ClientProxy
from core.choices import ImportantContactLabelsEnum
from core.constants.site_settings import SITE_SETTINGS_DB_SLUG
from core.constants.users import CON_MANAGER
from important_contact.models import ImportantContactProxy
from important_contact.views import ImportantContactListViewBW
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


def test_important_contact_list_view_kpi_stats(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    client = ClientProxy.objects.create(name="Apex Systems")

    # 1 payroll, 1 ceo, 1 other
    c1 = baker.make(
        ImportantContactProxy,
        contact_first_name="Jane",
        contact_last_name="Doe",
        contact_email="jane@example.com",
        contact_label=ImportantContactLabelsEnum.PAYROLL,
        is_deleted=False,
    )
    client.important_contacts.add(c1)

    baker.make(
        ImportantContactProxy,
        contact_first_name="John",
        contact_last_name="Smith",
        contact_email="john@example.com",
        contact_label=ImportantContactLabelsEnum.CEO,
        is_deleted=False,
    )

    baker.make(
        ImportantContactProxy,
        contact_first_name="Alex",
        contact_last_name="Taylor",
        contact_email="alex@example.com",
        contact_label=ImportantContactLabelsEnum.OTHER,
        is_deleted=False,
    )

    factory = RequestFactory()
    request = factory.get(reverse("dashboard:important_contact:list"))
    request.user = admin_user

    view = ImportantContactListViewBW()
    view.setup(request)
    context = view.get_context_data(object_list=view.get_queryset())

    kpi = context["kpi_stats"]
    assert kpi["total_contacts"] == 3
    assert kpi["payroll_contacts"] == 1
    assert kpi["ceo_contacts"] == 1
    assert kpi["other_contacts"] == 1
    assert kpi["linked_clients_contacts"] == 1


def test_important_contact_list_view_prefetch_eager_loading(
    admin_user: BWUser, django_assert_num_queries: Any
) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    client = ClientProxy.objects.create(name="Delta Global")

    for i in range(5):
        contact = baker.make(
            ImportantContactProxy,
            contact_first_name=f"First{i}",
            contact_last_name=f"Last{i}",
            contact_email=f"contact{i}@example.com",
            contact_label=ImportantContactLabelsEnum.PAYROLL,
            is_deleted=False,
        )
        client.important_contacts.add(contact)

    factory = RequestFactory()
    request = factory.get(reverse("dashboard:important_contact:list"))
    request.user = admin_user

    view = ImportantContactListViewBW()
    view.setup(request)
    qs = view.get_queryset()

    # Iterating over contacts and evaluating reverse M2M client.all() should execute exactly 2 queries:
    # 1 for contacts + 1 for prefetched clients (O(1) database queries, zero N+1!)
    with django_assert_num_queries(2):
        for contact in qs:
            _ = [c.name for c in contact.client.all()]
