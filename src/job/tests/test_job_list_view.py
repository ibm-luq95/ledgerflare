from __future__ import annotations

import pytest
from django.core.management import call_command
from django.test import RequestFactory
from django.urls import reverse
from model_bakery import baker

from beach_wood_user.models import BWUser
from core.choices import JobStateEnum, JobStatusEnum
from core.constants.users import CON_BOOKKEEPER, CON_MANAGER
from job.models import JobProxy
from job.views import JobExportView, JobListView, JobQuickPeekView

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def setup_groups(db):
    call_command("create_groups")


def test_job_list_view_annotations_and_kpi(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    baker.make(JobProxy, title="Job Alpha", status=JobStatusEnum.IN_PROGRESS)
    baker.make(JobProxy, title="Job Beta", status=JobStatusEnum.COMPLETED)
    baker.make(JobProxy, title="Job Gamma", status=JobStatusEnum.PAST_DUE)

    factory = RequestFactory()
    request = factory.get(reverse("dashboard:job:list"))
    request.user = admin_user

    view = JobListView()
    view.setup(request)
    qs = view.get_queryset()

    first_item = qs.first()
    assert first_item is not None
    assert hasattr(first_item, "total_tasks_count")
    assert hasattr(first_item, "completed_tasks_count")
    assert hasattr(first_item, "discussions_count")
    assert hasattr(first_item, "documents_count")

    context = view.get_context_data(object_list=qs)
    assert "kpi_stats" in context
    assert context["kpi_stats"]["total_jobs"] >= 3
    assert context["kpi_stats"]["in_progress_jobs"] >= 1
    assert context["kpi_stats"]["completed_jobs"] >= 1
    assert context["kpi_stats"]["past_due_jobs"] >= 1


def test_job_export_view(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    baker.make(JobProxy, title="Exportable Job 123", status=JobStatusEnum.COMPLETED)

    factory = RequestFactory()
    request = factory.get(reverse("dashboard:job:export"))
    request.user = admin_user

    view = JobExportView()
    view.setup(request)
    response = view.get(request)

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    assert "Exportable Job 123" in response.content.decode("utf-8")


def test_job_quick_peek_view(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    job = baker.make(
        JobProxy, title="Quick Peek Job 456", status=JobStatusEnum.NOT_STARTED
    )

    factory = RequestFactory()
    request = factory.get(reverse("dashboard:job:quick-peek", kwargs={"pk": job.pk}))
    request.user = admin_user

    view = JobQuickPeekView()
    view.setup(request, pk=job.pk)
    view.object = job
    context = view.get_context_data()

    assert context["job"] == job
    assert "tasks" in context
    assert "notes" in context
    assert "documents" in context


def test_job_list_view_filter_completed(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    baker.make(JobProxy, title="Active Job 1", status=JobStatusEnum.IN_PROGRESS)
    baker.make(JobProxy, title="Completed Job 2", status=JobStatusEnum.COMPLETED)

    factory = RequestFactory()
    request = factory.get(reverse("dashboard:job:list") + "?status=completed")
    request.user = admin_user

    view = JobListView()
    view.setup(request)
    qs = view.get_queryset()

    assert qs.count() == 1
    assert qs.first().title == "Completed Job 2"
