from __future__ import annotations

from typing import Any

import pytest
from django.contrib.sites.models import Site
from django.core.management import call_command
from model_bakery import baker

from client.models import ClientProxy
from core.choices import NoteSectionEnum
from core.constants.site_settings import SITE_SETTINGS_DB_SLUG
from job.models import JobProxy
from note.filters import NoteFilter
from note.models import NoteProxy
from site_settings.models import SiteSettings
from task.models import TaskProxy


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def setup_test_environment(db: Any) -> None:
    call_command("create_groups")
    SiteSettings.objects.get_or_create(
        slug=SITE_SETTINGS_DB_SLUG,
        defaults={"name": "LedgerFlare", "email": "info@ledgerflare.com"},
    )
    Site.objects.get_or_create(domain="testserver", defaults={"name": "testserver"})


def test_note_filter_by_section_and_title() -> None:
    client = ClientProxy.objects.create(name="Delta Inc")
    baker.make(
        NoteProxy,
        title="Audit checklist",
        body="Review expenses",
        note_section=NoteSectionEnum.CLIENT,
        client=client,
        is_deleted=False,
    )
    baker.make(
        NoteProxy,
        title="Tax reconciliation",
        body="Review returns",
        note_section=NoteSectionEnum.JOB,
        is_deleted=False,
    )

    # Filter by section
    filterset = NoteFilter(
        {"note_section": NoteSectionEnum.CLIENT}, queryset=NoteProxy.objects.all()
    )
    assert filterset.qs.count() == 1
    assert filterset.qs.first().title == "Audit checklist"

    # Filter by title keyword
    filterset = NoteFilter({"title": "tax"}, queryset=NoteProxy.objects.all())
    assert filterset.qs.count() == 1
    assert filterset.qs.first().title == "Tax reconciliation"

    # Filter by body keyword
    filterset = NoteFilter({"body": "expenses"}, queryset=NoteProxy.objects.all())
    assert filterset.qs.count() == 1
    assert filterset.qs.first().title == "Audit checklist"


def test_note_filter_multilingual_normalized_search() -> None:
    baker.make(
        NoteProxy,
        title="French Invoice",
        body="Règlement des honoraires du café",
        is_deleted=False,
    )
    baker.make(
        NoteProxy,
        title="Arabic Memo",
        body="مُحَمَّدٌ أَحْمَد للمحاسبة",
        is_deleted=False,
    )

    # Search with unaccented "cafe"
    filter_cafe = NoteFilter({"body": "cafe"}, queryset=NoteProxy.objects.all())
    assert filter_cafe.qs.count() == 1
    assert filter_cafe.qs.first().title == "French Invoice"

    # Search with simplified arabic "محمد"
    filter_arabic = NoteFilter({"body": "محمد"}, queryset=NoteProxy.objects.all())
    assert filter_arabic.qs.count() == 1
    assert filter_arabic.qs.first().title == "Arabic Memo"
