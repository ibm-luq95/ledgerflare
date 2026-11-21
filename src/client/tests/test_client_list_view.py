from __future__ import annotations

import pytest
from django.core.management import call_command
from django.test import Client, RequestFactory
from django.urls import reverse
from model_bakery import baker

from beach_wood_user.models import BWUser
from bookkeeper.models import BookkeeperProxy
from client.models import ClientProxy
from core.constants.status_labels import CON_ENABLED, CON_PAST_DUE
from core.constants.users import CON_BOOKKEEPER, CON_MANAGER


@pytest.fixture(autouse=True)
def setup_groups(db):
    call_command("create_groups")


@pytest.mark.django_db
def test_client_list_view_annotations_and_kpi(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    baker.make(ClientProxy, name="Acme Inc", status=CON_ENABLED)
    baker.make(ClientProxy, name="Beta LLC", status=CON_ENABLED)

    factory = RequestFactory()
    request = factory.get(reverse("dashboard:client:list"))
    request.user = admin_user

    from client.views.client import ClientListView

    view = ClientListView()
    view.setup(request)
    qs = view.get_queryset()

    first_item = qs.first()
    assert first_item is not None
    assert hasattr(first_item, "total_jobs_count")
    assert hasattr(first_item, "total_tasks_count")
    assert hasattr(first_item, "total_special_assignments_count")

    context = view.get_context_data(object_list=qs)
    assert "kpi_stats" in context
    assert context["kpi_stats"]["total_clients"] >= 2
    assert context["kpi_stats"]["active_clients"] >= 2


@pytest.mark.django_db
def test_client_list_view_bookkeeper_scoping() -> None:
    user = BWUser.objects.create_user(
        email="bookkeeper_test@example.com",
        password="Password123!",
        user_type=CON_BOOKKEEPER,
    )
    client1 = baker.make(ClientProxy, name="Assigned Client", status=CON_ENABLED)
    baker.make(ClientProxy, name="Unassigned Client", status=CON_ENABLED)

    bookkeeper_proxy = BookkeeperProxy.objects.get(user=user)
    bookkeeper_proxy.clients.add(client1)

    factory = RequestFactory()
    request = factory.get(reverse("dashboard:client:list"))
    request.user = user

    from client.views.client import ClientListView

    view = ClientListView()
    view.setup(request)
    qs = view.get_queryset()

    assert qs.count() == 1
    assert qs.first().name == "Assigned Client"


@pytest.mark.django_db
def test_client_list_view_renders_template_success(client: Client) -> None:
    user = BWUser.objects.create_superuser(
        email="superadmin_test@example.com",
        password="Password123!",
        user_type=CON_MANAGER,
    )
    baker.make(ClientProxy, name="Render Test Client", status=CON_ENABLED)

    client.force_login(user)
    response = client.get(reverse("dashboard:client:list"))

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Render Test Client" in content
    assert "Total Clients" in content
    assert "Active Clients" in content


@pytest.mark.django_db
def test_client_health_indicators_annotations(admin_user: BWUser) -> None:
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    client = baker.make(ClientProxy, name="Health Check Client", status=CON_ENABLED)
    baker.make("job.JobProxy", client=client, status=CON_PAST_DUE)

    factory = RequestFactory()
    request = factory.get(reverse("dashboard:client:list"))
    request.user = admin_user

    from client.views.client import ClientListView

    view = ClientListView()
    view.setup(request)
    qs = view.get_queryset()

    item = qs.filter(pk=client.pk).first()
    assert item is not None
    assert hasattr(item, "past_due_jobs_count")
    assert item.past_due_jobs_count == 1


@pytest.mark.django_db
def test_client_export_csv_view(client: Client) -> None:
    user = BWUser.objects.create_superuser(
        email="export_admin@example.com",
        password="Password123!",
        user_type=CON_MANAGER,
    )
    baker.make(
        ClientProxy, name="Export Acme Corp", status=CON_ENABLED, industry="Tech"
    )

    client.force_login(user)
    response = client.get(
        reverse("dashboard:client:export_csv") + "?name__icontains=Export+Acme"
    )

    assert response.status_code == 200
    assert "text/csv" in response["Content-Type"]
    assert "attachment; filename=" in response["Content-Disposition"]
    content = response.content.decode("utf-8")
    assert "Export Acme Corp" in content
    assert "Tech" in content


@pytest.mark.django_db
def test_client_export_excel_view(client: Client) -> None:
    user = BWUser.objects.create_superuser(
        email="export_excel_admin@example.com",
        password="Password123!",
        user_type=CON_MANAGER,
    )
    baker.make(
        ClientProxy, name="Export Excel Corp", status=CON_ENABLED, industry="Finance"
    )

    client.force_login(user)
    response = client.get(
        reverse("dashboard:client:export_excel") + "?name__icontains=Export+Excel"
    )

    assert response.status_code == 200
    assert (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        in response["Content-Type"]
    )
    assert "attachment; filename=" in response["Content-Disposition"]
    assert response["Content-Disposition"].endswith('.xlsx"')
    assert len(response.content) > 0


@pytest.mark.django_db
def test_client_export_format_query_param(client: Client) -> None:
    user = BWUser.objects.create_superuser(
        email="export_param_admin@example.com",
        password="Password123!",
        user_type=CON_MANAGER,
    )
    baker.make(
        ClientProxy, name="Export Param Corp", status=CON_ENABLED, industry="Healthcare"
    )

    client.force_login(user)
    excel_response = client.get(reverse("dashboard:client:export") + "?format=xlsx")
    assert excel_response.status_code == 200
    assert (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        in excel_response["Content-Type"]
    )

    csv_response = client.get(reverse("dashboard:client:export") + "?format=csv")
    assert csv_response.status_code == 200
    assert "text/csv" in csv_response["Content-Type"]


@pytest.mark.django_db
def test_client_quick_peek_view(client: Client) -> None:
    user = BWUser.objects.create_superuser(
        email="peek_admin@example.com",
        password="Password123!",
        user_type=CON_MANAGER,
    )
    c = baker.make(
        ClientProxy,
        name="Quick Peek Corp",
        email="peek@corp.com",
        status=CON_ENABLED,
    )

    client.force_login(user)
    response = client.get(reverse("dashboard:client:quick-peek", kwargs={"pk": c.pk}))

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Quick Peek Corp" in content
    assert "peek@corp.com" in content
