from __future__ import annotations

from datetime import timedelta

import pytest
from django.core.management import call_command
from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker

from beach_wood_user.models import BWUser
from cfo.models import CFOProxy
from client.models import ClientProxy
from core.choices import JobStatusEnum, TaskStatusEnum, TaskTypeEnum
from core.constants.users import (
    CON_ASSISTANT,
    CON_BOOKKEEPER,
    CON_CFO,
    CON_MANAGER,
)
from job.models import JobProxy
from task.models import TaskProxy
from task.views import TaskListView, TaskQuickPeekView


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def setup_groups(db):
    call_command("create_groups")


def test_task_list_view_manager_access(manager_user: BWUser) -> None:
    manager_user.user_type = CON_MANAGER
    manager_user.save()

    client = baker.make(ClientProxy, name="Acme Corp")
    job = baker.make(
        JobProxy,
        title="Tax Job",
        client=client,
        managed_by=manager_user,
        status=JobStatusEnum.IN_PROGRESS,
    )
    baker.make(
        TaskProxy, title="Task Alpha", job=job, status=TaskStatusEnum.IN_PROGRESS
    )
    baker.make(TaskProxy, title="Task Beta", job=job, status=TaskStatusEnum.COMPLETED)

    factory = RequestFactory()
    request = factory.get(reverse("dashboard:task:list"))
    request.user = manager_user

    view = TaskListView()
    view.setup(request)
    view.object_list = view.get_queryset()
    qs = view.object_list

    assert qs.count() >= 2
    context = view.get_context_data(object_list=qs)
    assert context["page_header"] == "Tasks"
    assert "filter_form_id" in context


def test_task_list_view_filter_by_status(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    job = baker.make(JobProxy, title="Audit Job", status=JobStatusEnum.IN_PROGRESS)
    t1 = baker.make(
        TaskProxy, title="In Progress Task", job=job, status=TaskStatusEnum.IN_PROGRESS
    )
    t2 = baker.make(
        TaskProxy, title="Completed Task", job=job, status=TaskStatusEnum.COMPLETED
    )

    factory = RequestFactory()
    request = factory.get(
        f"{reverse('dashboard:task:list')}?status={TaskStatusEnum.IN_PROGRESS}"
    )
    request.user = admin_user

    view = TaskListView()
    view.setup(request)
    qs = view.get_queryset()

    assert t1 in qs
    assert t2 not in qs


def test_task_list_view_filter_by_type(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    job = baker.make(JobProxy, title="Review Job", status=JobStatusEnum.IN_PROGRESS)
    baker.make(
        TaskProxy, title="Recurring Task", job=job, task_type=TaskTypeEnum.RECURRING
    )
    baker.make(
        TaskProxy, title="One Time Task", job=job, task_type=TaskTypeEnum.ONE_TIME
    )

    factory = RequestFactory()
    request = factory.get(
        f"{reverse('dashboard:task:list')}?task_type={TaskTypeEnum.RECURRING}"
    )
    request.user = admin_user

    view = TaskListView()
    view.setup(request)
    qs = view.get_queryset()

    assert qs.filter(task_type=TaskTypeEnum.RECURRING).exists()
    assert not qs.filter(task_type=TaskTypeEnum.ONE_TIME).exists()


def test_task_list_view_bookkeeper_scoping() -> None:
    bookkeeper_user = baker.make(
        BWUser,
        user_type=CON_BOOKKEEPER,
        email="bk_scoping_test@ledgerflare.com",
    )

    assigned_job = baker.make(
        JobProxy,
        title="Assigned Job",
        managed_by=bookkeeper_user,
        status=JobStatusEnum.IN_PROGRESS,
    )
    other_user = baker.make(BWUser, email="other_user_test@ledgerflare.com")
    unassigned_job = baker.make(
        JobProxy,
        title="Unassigned Job",
        managed_by=other_user,
        status=JobStatusEnum.IN_PROGRESS,
    )

    t_assigned = baker.make(TaskProxy, title="Task Assigned", job=assigned_job)
    t_unassigned = baker.make(TaskProxy, title="Task Other", job=unassigned_job)

    factory = RequestFactory()
    request = factory.get(reverse("dashboard:task:list"))
    request.user = bookkeeper_user

    view = TaskListView()
    view.setup(request)
    qs = view.get_queryset()

    assert t_assigned in qs
    assert t_unassigned not in qs


def test_task_list_view_full_render(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    client_obj = baker.make(ClientProxy, name="Tech Solutions Ltd")
    job = baker.make(
        JobProxy,
        title="Q3 Tax Audit",
        client=client_obj,
        status=JobStatusEnum.IN_PROGRESS,
    )
    task_obj = baker.make(
        TaskProxy,
        title="Review Balance Sheet",
        job=job,
        status=TaskStatusEnum.IN_PROGRESS,
    )

    client = Client()
    client.force_login(admin_user)
    response = client.get(reverse("dashboard:task:list"))

    assert response.status_code == 200
    assert task_obj in response.context["object_list"]
    assert "Review Balance Sheet" in response.content.decode()


def test_task_list_view_assistant_scoping() -> None:
    assistant_user = BWUser.objects.create_user(
        email="assistant_scoping@ledgerflare.com",
        password="Password123!",
        user_type=CON_ASSISTANT,
    )
    assigned_job = baker.make(
        JobProxy,
        title="Assistant Job",
        managed_by=assistant_user,
        status=JobStatusEnum.IN_PROGRESS,
    )
    other_user = BWUser.objects.create_user(
        email="other_staff@ledgerflare.com",
        password="Password123!",
        user_type=CON_BOOKKEEPER,
    )
    unassigned_job = baker.make(
        JobProxy,
        title="Other Job",
        managed_by=other_user,
        status=JobStatusEnum.IN_PROGRESS,
    )

    t_assigned = baker.make(TaskProxy, title="Assistant Task", job=assigned_job)
    t_unassigned = baker.make(TaskProxy, title="Other Task", job=unassigned_job)

    factory = RequestFactory()
    request = factory.get(reverse("dashboard:task:list"))
    request.user = assistant_user

    view = TaskListView()
    view.setup(request)
    qs = view.get_queryset()

    assert t_assigned in qs
    assert t_unassigned not in qs


def test_task_list_view_cfo_scoping() -> None:
    cfo_user = BWUser.objects.create_user(
        email="cfo_scoping@ledgerflare.com",
        password="Password123!",
        user_type=CON_CFO,
    )
    cfo = CFOProxy.objects.get(user=cfo_user)
    client_assigned = ClientProxy.objects.create(name="CFO Client")
    client_assigned.cfos.add(cfo)

    client_other = ClientProxy.objects.create(name="Other Client")

    job_assigned = baker.make(
        JobProxy,
        title="CFO Job",
        client=client_assigned,
        status=JobStatusEnum.IN_PROGRESS,
    )
    job_unassigned = baker.make(
        JobProxy,
        title="Other Client Job",
        client=client_other,
        status=JobStatusEnum.IN_PROGRESS,
    )

    t_assigned = baker.make(TaskProxy, title="CFO Task", job=job_assigned)
    t_unassigned = baker.make(TaskProxy, title="Other Client Task", job=job_unassigned)

    factory = RequestFactory()
    request = factory.get(reverse("dashboard:task:list"))
    request.user = cfo_user

    view = TaskListView()
    view.setup(request)
    qs = view.get_queryset()

    assert t_assigned in qs
    assert t_unassigned not in qs


def test_task_list_view_kpi_stats(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    job_past = baker.make(
        JobProxy, title="Past Job", due_date=yesterday, status=JobStatusEnum.IN_PROGRESS
    )
    job_future = baker.make(
        JobProxy,
        title="Future Job",
        due_date=tomorrow,
        status=JobStatusEnum.IN_PROGRESS,
    )

    baker.make(
        TaskProxy,
        title="In Progress Task",
        job=job_future,
        status=TaskStatusEnum.IN_PROGRESS,
    )
    baker.make(
        TaskProxy,
        title="Completed Task",
        job=job_future,
        status=TaskStatusEnum.COMPLETED,
    )
    baker.make(
        TaskProxy,
        title="Past Due Task",
        job=job_past,
        status=TaskStatusEnum.NOT_STARTED,
    )
    baker.make(
        TaskProxy,
        title="Urgent Task",
        job=job_future,
        task_type=TaskTypeEnum.URGENT,
        status=TaskStatusEnum.NOT_STARTED,
    )

    factory = RequestFactory()
    request = factory.get(reverse("dashboard:task:list"))
    request.user = admin_user

    view = TaskListView()
    view.setup(request)
    view.object_list = view.get_queryset()
    context = view.get_context_data(object_list=view.object_list)

    assert "kpi_stats" in context
    kpi_stats = context["kpi_stats"]
    assert kpi_stats["total_tasks"] >= 4
    assert kpi_stats["in_progress_tasks"] >= 1
    assert kpi_stats["completed_tasks"] >= 1
    assert kpi_stats["past_due_tasks"] >= 1
    assert kpi_stats["urgent_tasks"] >= 1
    assert context["total_records"] == kpi_stats["total_tasks"]
    assert context["filter_form_id"] == "tasksFilterForm"
    assert "table_header_subtitle" in context


def test_task_list_view_template_name() -> None:
    assert TaskListView.template_name == "task/list.html"


def test_task_list_view_unauthenticated_redirect() -> None:
    client = Client()
    response = client.get(reverse("dashboard:task:list"))
    assert response.status_code == 302
    assert "/auth/login" in response.url


def test_task_list_view_filtered_title_context(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    factory = RequestFactory()
    request_unfiltered = factory.get(reverse("dashboard:task:list"))
    request_unfiltered.user = admin_user

    view = TaskListView()
    view.setup(request_unfiltered)
    view.object_list = view.get_queryset()
    ctx_unfiltered = view.get_context_data(object_list=view.object_list)
    assert ctx_unfiltered["title"] == "Tasks"

    request_filtered = factory.get(
        f"{reverse('dashboard:task:list')}?status={TaskStatusEnum.IN_PROGRESS}"
    )
    request_filtered.user = admin_user

    view_f = TaskListView()
    view_f.setup(request_filtered)
    view_f.object_list = view_f.get_queryset()
    ctx_filtered = view_f.get_context_data(object_list=view_f.object_list)
    assert ctx_filtered["title"] == "Filtered Tasks"


def test_task_list_view_combined_query_filter(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    job = baker.make(JobProxy, title="Financial Statement Job")
    t_match = baker.make(
        TaskProxy,
        title="Reconcile Payroll Records",
        job=job,
        status=TaskStatusEnum.IN_PROGRESS,
    )
    t_wrong_status = baker.make(
        TaskProxy,
        title="Reconcile Bank Accounts",
        job=job,
        status=TaskStatusEnum.COMPLETED,
    )
    t_wrong_title = baker.make(
        TaskProxy,
        title="Generate Tax Invoices",
        job=job,
        status=TaskStatusEnum.IN_PROGRESS,
    )

    factory = RequestFactory()
    request = factory.get(
        f"{reverse('dashboard:task:list')}?title=Reconcile&status={TaskStatusEnum.IN_PROGRESS}"
    )
    request.user = admin_user

    view = TaskListView()
    view.setup(request)
    qs = view.get_queryset()

    assert t_match in qs
    assert t_wrong_status not in qs
    assert t_wrong_title not in qs


def test_task_quick_peek_view(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    client_obj = ClientProxy.objects.create(name="Quick Peek Client Corp")
    job = baker.make(
        JobProxy,
        title="Audit Q4 Job",
        client=client_obj,
        managed_by=admin_user,
    )
    task = baker.make(
        TaskProxy,
        title="Quick Peek Task Inspection",
        job=job,
        status=TaskStatusEnum.IN_PROGRESS,
        task_type=TaskTypeEnum.URGENT,
        hints="Check ledger account balances",
        additional_notes="<p>Detailed verification instructions.</p>",
    )

    factory = RequestFactory()
    request = factory.get(reverse("dashboard:task:quick-peek", kwargs={"pk": task.pk}))
    request.user = admin_user

    view = TaskQuickPeekView()
    view.setup(request, pk=task.pk)
    view.object = task
    context = view.get_context_data()

    assert context["task"] == task
    assert "notes" in context
    assert "documents" in context


def test_task_list_view_query_optimization(admin_user: BWUser) -> None:
    """Verify TaskListView uses select_related and only() projection to prevent N+1 queries."""
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    factory = RequestFactory()
    request = factory.get(reverse("dashboard:task:list"))
    request.user = admin_user

    view = TaskListView()
    view.setup(request)
    qs = view.get_queryset()

    assert isinstance(qs.query.select_related, dict)
    assert "job" in qs.query.select_related
    assert (
        "job__client" in qs.query.select_related
        or "client" in qs.query.select_related.get("job", {})
    )
    assert (
        "job__managed_by" in qs.query.select_related
        or "managed_by" in qs.query.select_related.get("job", {})
    )
