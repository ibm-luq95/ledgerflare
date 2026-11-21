from datetime import timedelta
from typing import Any
import pytest
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker

from beach_wood_user.models import BWUser
from core.choices.special_assignment import SpecialAssignmentStatusEnum
from special_assignment.models import SpecialAssignmentProxy


from site_settings.models import SiteSettings
from core.constants.site_settings import SITE_SETTINGS_DB_SLUG


@pytest.fixture(autouse=True)
def setup_test_environment(db: Any) -> None:
    """Ensure Django auth groups, site settings, and sites exist before running tests."""
    call_command("create_groups")
    SiteSettings.objects.get_or_create(
        slug=SITE_SETTINGS_DB_SLUG,
        defaults={"name": "LedgerFlare", "email": "info@ledgerflare.com"},
    )
    Site.objects.get_or_create(domain="testserver", defaults={"name": "testserver"})


@pytest.mark.django_db
def test_special_assignment_list_view_kpi_stats(client, admin_user):
    client.force_login(admin_user)
    today = timezone.now().date()

    baker.make(
        SpecialAssignmentProxy,
        title="In Progress Assignment",
        status=SpecialAssignmentStatusEnum.IN_PROGRESS,
        due_date=today + timedelta(days=2),
        assigned_to=admin_user,
        is_deleted=False,
    )
    baker.make(
        SpecialAssignmentProxy,
        title="Not Started Overdue Assignment",
        status=SpecialAssignmentStatusEnum.NOT_STARTED,
        due_date=today - timedelta(days=2),
        is_seen=False,
        assigned_to=admin_user,
        is_deleted=False,
    )
    baker.make(
        SpecialAssignmentProxy,
        title="Completed Assignment",
        status=SpecialAssignmentStatusEnum.COMPLETED,
        due_date=today - timedelta(days=1),
        assigned_to=admin_user,
        is_deleted=False,
    )

    url = reverse("dashboard:special_assignment:list")
    response = client.get(url)
    assert response.status_code == 200
    assert "kpi_stats" in response.context
    stats = response.context["kpi_stats"]
    assert stats["total_assignments"] == 2
    assert stats["in_progress"] == 1
    assert stats["overdue"] == 1
    assert stats["unseen"] >= 1


@pytest.mark.django_db
def test_special_assignment_list_view_filter_query(client, admin_user):
    client.force_login(admin_user)
    today = timezone.now().date()

    baker.make(
        SpecialAssignmentProxy,
        title="Alpha Project Assignment",
        status=SpecialAssignmentStatusEnum.IN_PROGRESS,
        due_date=today + timedelta(days=2),
        assigned_to=admin_user,
        is_deleted=False,
    )
    baker.make(
        SpecialAssignmentProxy,
        title="Beta Task Assignment",
        status=SpecialAssignmentStatusEnum.NOT_STARTED,
        due_date=today + timedelta(days=5),
        assigned_to=admin_user,
        is_deleted=False,
    )

    url = reverse("dashboard:special_assignment:list")
    response = client.get(f"{url}?title=Alpha")
    assert response.status_code == 200
    items = list(response.context["object_list"])
    assert len(items) == 1
    assert items[0].title == "Alpha Project Assignment"


@pytest.mark.django_db
def test_special_assignment_list_view_bookkeeper_scoping(
    client, bookkeeper_user, admin_user
):
    from core.constants.users import CON_BOOKKEEPER

    bookkeeper_user.user_type = CON_BOOKKEEPER
    bookkeeper_user.is_superuser = False
    bookkeeper_user.save()

    client.force_login(bookkeeper_user)
    today = timezone.now().date()

    # Assignment assigned to this bookkeeper
    baker.make(
        SpecialAssignmentProxy,
        title="My Bookkeeper Task",
        status=SpecialAssignmentStatusEnum.IN_PROGRESS,
        due_date=today + timedelta(days=2),
        assigned_to=bookkeeper_user,
        is_deleted=False,
    )
    # Assignment assigned to admin
    baker.make(
        SpecialAssignmentProxy,
        title="Admin Private Task",
        status=SpecialAssignmentStatusEnum.IN_PROGRESS,
        due_date=today + timedelta(days=2),
        assigned_to=admin_user,
        is_deleted=False,
    )

    url = reverse("dashboard:special_assignment:list")
    response = client.get(url)
    assert response.status_code == 200
    items = list(response.context["object_list"])
    titles = [item.title for item in items]
    assert "My Bookkeeper Task" in titles
    assert "Admin Private Task" not in titles
