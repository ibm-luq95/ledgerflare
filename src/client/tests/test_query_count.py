from __future__ import annotations

import pytest
from django.core.management import call_command
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from model_bakery import baker

from beach_wood_user.models import BWUser
from bookkeeper.models import BookkeeperProxy
from cfo.models.proxy import CFOProxy
from client.models import ClientProxy
from client_category.models import ClientCategory
from core.constants.status_labels import CON_ENABLED
from core.constants.users import CON_BOOKKEEPER, CON_MANAGER
from job.models import JobProxy


@pytest.mark.django_db
def test_client_list_view_query_count(client: Client) -> None:
    call_command("create_groups")
    user = BWUser.objects.create_superuser(
        email="query_count_admin@example.com",
        password="Password123!",
        user_type=CON_MANAGER,
    )
    categories = [baker.make(ClientCategory, name=f"Cat {i}") for i in range(5)]
    bookkeepers = []
    for i in range(5):
        bk_user = BWUser.objects.create_user(
            email=f"bk_{i}@example.com",
            password="Password123!",
            first_name=f"First{i}",
            last_name=f"Last{i}",
            user_type=CON_BOOKKEEPER,
        )
        bookkeepers.append(BookkeeperProxy.objects.get(user=bk_user))

    cfos = []
    for i in range(3):
        cfo_user = BWUser.objects.create_user(
            email=f"cfo_{i}@example.com",
            password="Password123!",
            first_name=f"CFOFirst{i}",
            last_name=f"CFOLast{i}",
            user_type=CON_MANAGER,
        )
        cfos.append(baker.make(CFOProxy, user=cfo_user))

    for i in range(50):
        c = baker.make(
            ClientProxy,
            name=f"Client {i:02d}",
            status=CON_ENABLED,
        )
        c.categories.add(categories[i % len(categories)])
        c.bookkeepers.add(bookkeepers[i % len(bookkeepers)])
        c.cfos.add(cfos[i % len(cfos)])
        baker.make(JobProxy, client=c, status=CON_ENABLED)

    client.force_login(user)

    with CaptureQueriesContext(connection) as ctx:
        response = client.get(reverse("dashboard:client:list"))

    assert response.status_code == 200
    assert len(ctx.captured_queries) <= 35, (
        f"Expected <= 35 queries, got {len(ctx.captured_queries)}"
    )
