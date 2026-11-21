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


def test_important_contact_quick_peek_endpoint(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    client = ClientProxy.objects.create(name="Stark Industries")
    contact = baker.make(
        ImportantContactProxy,
        contact_first_name="Pepper",
        contact_last_name="Potts",
        company_name="Stark Corp",
        contact_email="pepper@stark.com",
        contact_phone="+1-555-0199",
        contact_city="Malibu",
        contact_state="CA",
        contact_label=ImportantContactLabelsEnum.CEO,
        is_deleted=False,
    )
    client.important_contacts.add(contact)

    test_client = DjangoTestClient()
    test_client.force_login(admin_user)

    url = reverse("dashboard:important_contact:quick-peek", kwargs={"pk": contact.pk})
    response = test_client.get(
        url, credentials={"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert "Pepper Potts" in content
    assert "Stark Corp" in content
    assert "pepper@stark.com" in content
    assert "+1-555-0199" in content
    assert "Stark Industries" in content
