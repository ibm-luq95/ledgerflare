from __future__ import annotations

import pytest
from django.core.management import call_command
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from model_bakery import baker

from beach_wood_user.models import BWUser
from client.models import ClientProxy
from core.choices import JobStatusEnum
from core.constants.users import CON_MANAGER
from job.models import JobProxy
from job_category.models import JobCategory
from task.models import TaskProxy


@pytest.mark.django_db
def test_job_list_view_query_count(client: Client) -> None:
    call_command("create_groups")
    admin_user = BWUser.objects.create_superuser(
        email="job_admin@example.com",
        password="Password123!",
        user_type=CON_MANAGER,
    )
    categories = [baker.make(JobCategory, name=f"JobCat {i}") for i in range(5)]
    clients = [baker.make(ClientProxy, name=f"Client {i}") for i in range(5)]
    managers = [
        BWUser.objects.create_user(
            email=f"mgr_{i}@example.com",
            password="Password123!",
            first_name=f"MgrFirst{i}",
            last_name=f"MgrLast{i}",
            user_type=CON_MANAGER,
        )
        for i in range(3)
    ]

    for i in range(30):
        job = baker.make(
            JobProxy,
            title=f"Job {i:02d}",
            status=JobStatusEnum.IN_PROGRESS,
            client=clients[i % len(clients)],
            managed_by=managers[i % len(managers)],
        )
        job.categories.add(categories[i % len(categories)])
        baker.make(TaskProxy, title=f"Task {i}", job=job, is_completed=(i % 2 == 0))

    client.force_login(admin_user)

    with CaptureQueriesContext(connection) as ctx:
        response = client.get(reverse("dashboard:job:list"))

    assert response.status_code == 200
    assert len(ctx.captured_queries) <= 35, (
        f"Expected <= 35 queries, got {len(ctx.captured_queries)}"
    )
