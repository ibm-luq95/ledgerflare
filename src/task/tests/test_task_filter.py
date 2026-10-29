from __future__ import annotations

from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone
from model_bakery import baker

from beach_wood_user.models import BWUser
from bookkeeper.models import BookkeeperProxy
from client.models import ClientProxy
from core.choices import TaskStatusEnum, TaskTypeEnum
from core.constants.users import CON_BOOKKEEPER
from job.models import JobProxy
from task.filters import TaskFilter
from task.models import TaskProxy


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def setup_groups(db):
    call_command("create_groups")


def test_filter_by_title_icontains() -> None:
    job = baker.make(JobProxy, title="Job 1")
    t1 = baker.make(TaskProxy, title="Prepare quarterly review", job=job)
    t2 = baker.make(TaskProxy, title="File annual tax returns", job=job)

    qs = TaskProxy.objects.all()
    filterset = TaskFilter(data={"title": "quarterly"}, queryset=qs)
    assert filterset.is_valid()
    results = filterset.qs

    assert t1 in results
    assert t2 not in results


def test_filter_by_hints_icontains() -> None:
    job = baker.make(JobProxy, title="Job 1")
    t1 = baker.make(
        TaskProxy,
        title="Task 1",
        hints="Check bank reconciliation statement",
        job=job,
    )
    t2 = baker.make(
        TaskProxy,
        title="Task 2",
        hints="Contact vendor for missing invoice",
        job=job,
    )

    qs = TaskProxy.objects.all()
    filterset = TaskFilter(data={"hints": "bank"}, queryset=qs)
    assert filterset.is_valid()
    results = filterset.qs

    assert t1 in results
    assert t2 not in results


def test_filter_by_task_type() -> None:
    job = baker.make(JobProxy, title="Job 1")
    t1 = baker.make(
        TaskProxy,
        title="Recurring Task",
        task_type=TaskTypeEnum.RECURRING,
        job=job,
    )
    t2 = baker.make(
        TaskProxy,
        title="Urgent Task",
        task_type=TaskTypeEnum.URGENT,
        job=job,
    )

    qs = TaskProxy.objects.all()
    filterset = TaskFilter(data={"task_type": TaskTypeEnum.RECURRING}, queryset=qs)
    assert filterset.is_valid()
    results = filterset.qs

    assert t1 in results
    assert t2 not in results


def test_filter_by_status() -> None:
    job = baker.make(JobProxy, title="Job 1")
    t1 = baker.make(
        TaskProxy,
        title="In Progress Task",
        status=TaskStatusEnum.IN_PROGRESS,
        job=job,
    )
    t2 = baker.make(
        TaskProxy,
        title="Completed Task",
        status=TaskStatusEnum.COMPLETED,
        job=job,
    )

    qs = TaskProxy.objects.all()
    filterset = TaskFilter(data={"status": TaskStatusEnum.IN_PROGRESS}, queryset=qs)
    assert filterset.is_valid()
    results = filterset.qs

    assert t1 in results
    assert t2 not in results


def test_filter_by_is_completed() -> None:
    job = baker.make(JobProxy, title="Job 1")
    t_completed = baker.make(
        TaskProxy,
        title="Done Task",
        status=TaskStatusEnum.COMPLETED,
        is_completed=True,
        job=job,
    )
    t_incomplete = baker.make(
        TaskProxy,
        title="Pending Task",
        status=TaskStatusEnum.IN_PROGRESS,
        is_completed=False,
        job=job,
    )

    qs = TaskProxy.objects.all()

    # Filter is_completed=true
    filter_true = TaskFilter(data={"is_completed": "true"}, queryset=qs)
    assert filter_true.is_valid()
    assert t_completed in filter_true.qs
    assert t_incomplete not in filter_true.qs

    # Filter is_completed=false
    filter_false = TaskFilter(data={"is_completed": "false"}, queryset=qs)
    assert filter_false.is_valid()
    assert t_incomplete in filter_false.qs
    assert t_completed not in filter_false.qs


def test_filter_by_job() -> None:
    job1 = baker.make(JobProxy, title="Audit Job")
    job2 = baker.make(JobProxy, title="Tax Job")

    t1 = baker.make(TaskProxy, title="Task Job 1", job=job1)
    t2 = baker.make(TaskProxy, title="Task Job 2", job=job2)

    qs = TaskProxy.objects.all()
    filterset = TaskFilter(data={"job": str(job1.pk)}, queryset=qs)
    assert filterset.is_valid()
    results = filterset.qs

    assert t1 in results
    assert t2 not in results


def test_filter_by_job_client() -> None:
    client_a = baker.make(ClientProxy, name="Client Alpha")
    client_b = baker.make(ClientProxy, name="Client Beta")

    job_a = baker.make(JobProxy, title="Job A", client=client_a)
    job_b = baker.make(JobProxy, title="Job B", client=client_b)

    t_a = baker.make(TaskProxy, title="Task Alpha", job=job_a)
    t_b = baker.make(TaskProxy, title="Task Beta", job=job_b)

    qs = TaskProxy.objects.all()

    # Test via job__client field
    filter_job_client = TaskFilter(data={"job__client": str(client_a.pk)}, queryset=qs)
    assert filter_job_client.is_valid()
    assert t_a in filter_job_client.qs
    assert t_b not in filter_job_client.qs

    # Test via client alias field
    filter_client = TaskFilter(data={"client": str(client_a.pk)}, queryset=qs)
    assert filter_client.is_valid()
    assert t_a in filter_client.qs
    assert t_b not in filter_client.qs


def test_filter_by_job_managed_by() -> None:
    manager_1 = baker.make(BWUser, email="manager1@ledgerflare.com")
    manager_2 = baker.make(BWUser, email="manager2@ledgerflare.com")

    job_1 = baker.make(JobProxy, title="Job 1", managed_by=manager_1)
    job_2 = baker.make(JobProxy, title="Job 2", managed_by=manager_2)

    t1 = baker.make(TaskProxy, title="Task M1", job=job_1)
    t2 = baker.make(TaskProxy, title="Task M2", job=job_2)

    qs = TaskProxy.objects.all()

    # Test via job__managed_by
    filter_jmb = TaskFilter(data={"job__managed_by": str(manager_1.pk)}, queryset=qs)
    assert filter_jmb.is_valid()
    assert t1 in filter_jmb.qs
    assert t2 not in filter_jmb.qs

    # Test via managed_by alias
    filter_mb = TaskFilter(data={"managed_by": str(manager_1.pk)}, queryset=qs)
    assert filter_mb.is_valid()
    assert t1 in filter_mb.qs
    assert t2 not in filter_mb.qs


def test_filter_by_job_bookkeeper() -> None:
    bk_user_1 = BWUser.objects.create_user(
        email="bk1_filter@ledgerflare.com",
        password="Password123!",
        user_type=CON_BOOKKEEPER,
    )
    bk_user_2 = BWUser.objects.create_user(
        email="bk2_filter@ledgerflare.com",
        password="Password123!",
        user_type=CON_BOOKKEEPER,
    )
    bookkeeper_1 = BookkeeperProxy.objects.get(user=bk_user_1)
    bookkeeper_2 = BookkeeperProxy.objects.get(user=bk_user_2)

    client_1 = baker.make(ClientProxy, name="Client 1")
    client_1.bookkeepers.add(bookkeeper_1)

    client_2 = baker.make(ClientProxy, name="Client 2")
    client_2.bookkeepers.add(bookkeeper_2)

    job_1 = baker.make(JobProxy, title="Job BK 1", client=client_1)
    job_2 = baker.make(JobProxy, title="Job BK 2", client=client_2)

    t1 = baker.make(TaskProxy, title="Task BK 1", job=job_1)
    t2 = baker.make(TaskProxy, title="Task BK 2", job=job_2)

    qs = TaskProxy.objects.all()

    # Test via job__bookkeeper
    filter_jbk = TaskFilter(data={"job__bookkeeper": str(bookkeeper_1.pk)}, queryset=qs)
    assert filter_jbk.is_valid()
    assert t1 in filter_jbk.qs
    assert t2 not in filter_jbk.qs

    # Test via bookkeeper alias
    filter_bk = TaskFilter(data={"bookkeeper": str(bookkeeper_1.pk)}, queryset=qs)
    assert filter_bk.is_valid()
    assert t1 in filter_bk.qs
    assert t2 not in filter_bk.qs


def test_filter_by_created_date_preset() -> None:
    now = timezone.now()
    past_date = now - timedelta(days=40)

    job = baker.make(JobProxy, title="Job Dates")
    t_today = baker.make(TaskProxy, title="Today Task", job=job)
    t_past = baker.make(TaskProxy, title="Past Task", job=job)
    TaskProxy.objects.filter(pk=t_past.pk).update(created_at=past_date)

    qs = TaskProxy.objects.all()
    filterset = TaskFilter(data={"created": "today"}, queryset=qs)
    assert filterset.is_valid()
    results = filterset.qs

    assert t_today in results
    assert t_past not in results


def test_filter_combined_fields() -> None:
    client_target = baker.make(ClientProxy, name="Target Client")
    client_other = baker.make(ClientProxy, name="Other Client")

    job_target = baker.make(JobProxy, title="Target Job", client=client_target)
    job_other = baker.make(JobProxy, title="Other Job", client=client_other)

    t_match = baker.make(
        TaskProxy,
        title="Audit Payroll",
        hints="Check Q3 slips",
        task_type=TaskTypeEnum.RECURRING,
        status=TaskStatusEnum.IN_PROGRESS,
        job=job_target,
    )
    t_wrong_status = baker.make(
        TaskProxy,
        title="Audit Payroll",
        hints="Check Q3 slips",
        task_type=TaskTypeEnum.RECURRING,
        status=TaskStatusEnum.COMPLETED,
        job=job_target,
    )
    t_wrong_client = baker.make(
        TaskProxy,
        title="Audit Payroll",
        hints="Check Q3 slips",
        task_type=TaskTypeEnum.RECURRING,
        status=TaskStatusEnum.IN_PROGRESS,
        job=job_other,
    )

    qs = TaskProxy.objects.all()
    filterset = TaskFilter(
        data={
            "job__client": str(client_target.pk),
            "status": TaskStatusEnum.IN_PROGRESS,
            "task_type": TaskTypeEnum.RECURRING,
            "title": "Payroll",
        },
        queryset=qs,
    )
    assert filterset.is_valid()
    results = filterset.qs

    assert t_match in results
    assert t_wrong_status not in results
    assert t_wrong_client not in results


def test_filter_form_fields_and_widgets() -> None:
    filterset = TaskFilter()
    form = filterset.form

    expected_fields = [
        "title",
        "hints",
        "task_type",
        "status",
        "is_completed",
        "job",
        "job__client",
        "job__managed_by",
        "job__bookkeeper",
        "client",
        "managed_by",
        "bookkeeper",
        "created",
        "created_between",
    ]

    for field_name in expected_fields:
        assert field_name in form.fields, (
            f"Field '{field_name}' should be in TaskFilter form"
        )


def test_task_filter_multilingual_hints_search() -> None:
    job = baker.make(JobProxy, title="Job Audit")
    t1 = baker.make(
        TaskProxy,
        title="Spanish Hint Task",
        hints="Revisión de nómina y café",
        job=job,
    )
    t2 = baker.make(
        TaskProxy,
        title="Arabic Hint Task",
        hints="مُحَمَّدٌ مُحَاسِب",
        job=job,
    )

    # Search with "nomina" (accent insensitive)
    filter_es = TaskFilter(data={"hints": "nomina"}, queryset=TaskProxy.objects.all())
    assert filter_es.is_valid()
    assert t1 in filter_es.qs
    assert t2 not in filter_es.qs

    # Search with "محمد" (diacritic insensitive)
    filter_ar = TaskFilter(data={"hints": "محمد"}, queryset=TaskProxy.objects.all())
    assert filter_ar.is_valid()
    assert t2 in filter_ar.qs
    assert t1 not in filter_ar.qs
