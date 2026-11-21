"""Tests for JobWorkstationView."""

from __future__ import annotations

import datetime

import pytest
from django.contrib.auth.models import Group
from django.test import RequestFactory
from django.urls import reverse
from model_bakery import baker

from beach_wood_user.models import BWUser
from bookkeeper.models import BookkeeperProxy
from client.models import ClientProxy
from core.choices import JobStatusEnum
from core.constants.users import (
    ASSISTANT_GROUP_NAME,
    BOOKKEEPER_GROUP_NAME,
    CON_BOOKKEEPER,
    CON_MANAGER,
    MANAGER_GROUP_NAME,
)
from job.models import JobProxy
from task.models import TaskProxy


@pytest.fixture(autouse=True)
def setup_groups():
    """Ensure permission groups exist for tests."""
    for group_name in [
        BOOKKEEPER_GROUP_NAME,
        ASSISTANT_GROUP_NAME,
        MANAGER_GROUP_NAME,
    ]:
        Group.objects.get_or_create(name=group_name)


@pytest.mark.django_db
def test_job_workstation_unauthenticated_redirect(client) -> None:
    """Verify unauthenticated requests redirect to login."""
    url = reverse("dashboard:job:workstation")
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_job_workstation_manager_context() -> None:
    """Verify manager gets complete firm-wide workstation context and metrics."""
    from job.views.workstation import JobWorkstationView

    user = baker.make(
        BWUser,
        first_name="Admin",
        last_name="Manager",
        user_type=CON_MANAGER,
        is_superuser=True,
    )
    client_obj = baker.make(ClientProxy, name="Acme Corp")
    job = baker.make(
        JobProxy,
        title="Monthly Bookkeeping",
        client=client_obj,
        period_year="2026",
        period_month="8",
        status=JobStatusEnum.IN_PROGRESS,
        start_date=datetime.date(2026, 8, 15),
        due_date=datetime.date(2026, 8, 28),
    )
    baker.make(TaskProxy, job=job, title="Bank Reconciliation", is_completed=False)

    factory = RequestFactory()
    request = factory.get(reverse("dashboard:job:workstation") + "?year=2026&month=8")
    request.user = user

    view = JobWorkstationView()
    view.setup(request)
    context = view.get_context_data()

    assert context["current_year"] == 2026
    assert context["current_month_num"] == 8
    assert "calendar_weeks" in context
    assert "kanban_columns" in context
    assert "agenda_groups" in context
    assert "metrics" in context
    assert context["metrics"]["total_jobs"] >= 1
    assert context["is_manager_or_admin"] is True


@pytest.mark.django_db
def test_job_workstation_bookkeeper_scoping() -> None:
    """Verify bookkeepers only receive jobs assigned to their clients."""
    from job.views.workstation import JobWorkstationView

    bk_user1 = baker.make(
        BWUser,
        first_name="Jane",
        last_name="Bookkeeper",
        user_type=CON_BOOKKEEPER,
    )
    bk1 = BookkeeperProxy.objects.get(user=bk_user1)

    bk_user2 = baker.make(
        BWUser,
        first_name="Other",
        last_name="Bookkeeper",
        user_type=CON_BOOKKEEPER,
    )
    bk2 = BookkeeperProxy.objects.get(user=bk_user2)

    client1 = baker.make(ClientProxy, name="Client 1")
    client1.bookkeepers.add(bk1)

    client2 = baker.make(ClientProxy, name="Client 2")
    client2.bookkeepers.add(bk2)

    baker.make(
        JobProxy,
        title="Job for BK 1",
        client=client1,
        period_year="2026",
        period_month="8",
        status=JobStatusEnum.NOT_STARTED,
        start_date=datetime.date(2026, 8, 10),
    )
    baker.make(
        JobProxy,
        title="Job for BK 2",
        client=client2,
        period_year="2026",
        period_month="8",
        status=JobStatusEnum.NOT_STARTED,
        start_date=datetime.date(2026, 8, 10),
    )

    factory = RequestFactory()
    request = factory.get(reverse("dashboard:job:workstation") + "?year=2026&month=8")
    request.user = bk_user1

    view = JobWorkstationView()
    view.setup(request)
    context = view.get_context_data()

    job_titles = [j.title for j in context["jobs"]]
    assert "Job for BK 1" in job_titles
    assert "Job for BK 2" not in job_titles


@pytest.mark.django_db
def test_job_workstation_admin_filter_specific_staff() -> None:
    """Verify admin can view workstation filtered by a specific staff member."""
    from job.views.workstation import JobWorkstationView

    admin_user = baker.make(
        BWUser,
        first_name="Admin",
        last_name="Manager",
        user_type=CON_MANAGER,
        is_superuser=True,
    )
    bk_user = baker.make(
        BWUser,
        first_name="Target",
        last_name="Bookkeeper",
        user_type=CON_BOOKKEEPER,
    )
    bk = BookkeeperProxy.objects.get(user=bk_user)

    client_target = baker.make(ClientProxy, name="Target Client")
    client_target.bookkeepers.add(bk)

    client_other = baker.make(ClientProxy, name="Other Client")

    baker.make(
        JobProxy,
        title="Target Staff Job",
        client=client_target,
        period_year="2026",
        period_month="8",
        status=JobStatusEnum.IN_PROGRESS,
        start_date=datetime.date(2026, 8, 10),
    )
    baker.make(
        JobProxy,
        title="Other Staff Job",
        client=client_other,
        period_year="2026",
        period_month="8",
        status=JobStatusEnum.IN_PROGRESS,
        start_date=datetime.date(2026, 8, 10),
    )

    factory = RequestFactory()
    request = factory.get(
        reverse("dashboard:job:workstation") + f"?year=2026&month=8&staff={bk_user.id}"
    )
    request.user = admin_user

    view = JobWorkstationView()
    view.setup(request)
    context = view.get_context_data()

    assert context["selected_staff"] == bk_user
    job_titles = [j.title for j in context["jobs"]]
    assert "Target Staff Job" in job_titles
    assert "Other Staff Job" not in job_titles


@pytest.mark.django_db
def test_job_workstation_render_with_unassigned_job(client) -> None:
    """Verify workstation template renders without error when a job has no managed_by."""
    from site_settings.models import SiteSettings

    baker.make(SiteSettings, slug="web-app-site-settings")

    admin_user = BWUser.objects.create_superuser(
        email="super_ws@ledgerflare.com",
        password="Password123!",
        user_type=CON_MANAGER,
    )
    baker.make(
        JobProxy,
        title="Unassigned Job In Workstation",
        managed_by=None,
        period_year="2026",
        period_month="8",
        status=JobStatusEnum.IN_PROGRESS,
        start_date=datetime.date(2026, 8, 15),
    )

    client.force_login(admin_user)
    response = client.get(reverse("dashboard:job:workstation") + "?year=2026&month=8")
    assert response.status_code == 200
    assert "Unassigned Job In Workstation" in response.content.decode("utf-8")
