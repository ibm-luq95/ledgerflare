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


def test_note_quick_peek_endpoint(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    client = ClientProxy.objects.create(name="Quick Peek Client")
    job = baker.make(JobProxy, title="Quick Peek Job", client=client)
    note = baker.make(
        NoteProxy,
        title="Important Briefing",
        body="<p>Detailed notes content for test.</p>",
        client=client,
        job=job,
        note_section=NoteSectionEnum.JOB,
        is_deleted=False,
    )

    test_client = DjangoTestClient()
    test_client.force_login(admin_user)

    url = reverse("dashboard:note:quick-peek", kwargs={"pk": note.pk})
    response = test_client.get(url, credentials={"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"})

    assert response.status_code == 200
    assert "Important Briefing" in response.content.decode()
    assert "Quick Peek Client" in response.content.decode()
    assert "Quick Peek Job" in response.content.decode()
