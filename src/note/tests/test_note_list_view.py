from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker

from beach_wood_user.models import BWUser
from client.models import ClientProxy
from core.choices import NoteSectionEnum
from core.constants.site_settings import SITE_SETTINGS_DB_SLUG
from core.constants.users import CON_BOOKKEEPER, CON_MANAGER
from job.models import JobProxy
from note.models import NoteProxy
from note.views import NoteListView
from site_settings.models import SiteSettings
from task.models import TaskProxy


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def setup_test_environment(db: Any) -> None:
    """Setup Django test environment."""
    call_command("create_groups")
    SiteSettings.objects.get_or_create(
        slug=SITE_SETTINGS_DB_SLUG,
        defaults={"name": "LedgerFlare", "email": "info@ledgerflare.com"},
    )
    Site.objects.get_or_create(domain="testserver", defaults={"name": "testserver"})


def test_note_list_view_kpi_stats(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    client = ClientProxy.objects.create(name="Acme Corp")
    job = baker.make(JobProxy, title="Job Alpha", client=client)
    task = baker.make(TaskProxy, title="Task Alpha", job=job)

    # 1 client note, 1 job note, 1 task note
    baker.make(NoteProxy, title="Note 1", client=client, note_section=NoteSectionEnum.CLIENT, is_deleted=False)
    baker.make(NoteProxy, title="Note 2", job=job, note_section=NoteSectionEnum.JOB, is_deleted=False)
    baker.make(NoteProxy, title="Note 3", task=task, note_section=NoteSectionEnum.TASK, is_deleted=False)

    factory = RequestFactory()
    request = factory.get(reverse("dashboard:note:list"))
    request.user = admin_user

    view = NoteListView()
    view.setup(request)
    context = view.get_context_data(object_list=view.get_queryset())

    kpi = context["kpi_stats"]
    assert kpi["total_notes"] == 3
    assert kpi["client_notes"] == 1
    assert kpi["job_notes"] == 1
    assert kpi["task_notes"] == 1
    assert kpi["recent_notes"] == 3


def test_note_list_view_select_related_eager_loading(admin_user: BWUser, django_assert_num_queries: Any) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    client = ClientProxy.objects.create(name="Beta LLC")
    job = baker.make(JobProxy, title="Job Beta", client=client)
    task = baker.make(TaskProxy, title="Task Beta", job=job)

    for i in range(5):
        baker.make(
            NoteProxy,
            title=f"Note {i}",
            client=client,
            job=job,
            task=task,
            note_section=NoteSectionEnum.JOB,
            is_deleted=False,
        )

    factory = RequestFactory()
    request = factory.get(reverse("dashboard:note:list"))
    request.user = admin_user

    view = NoteListView()
    view.setup(request)
    qs = view.get_queryset()

    # Iterating and accessing related client, job, and task should not trigger queries
    with django_assert_num_queries(1):
        for note in qs:
            _ = note.client.name
            _ = note.job.title
            _ = note.task.title
