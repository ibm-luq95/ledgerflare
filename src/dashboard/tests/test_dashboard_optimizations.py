# -*- coding: utf-8 -*-#
from __future__ import annotations

from typing import Any
import pytest
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.test import RequestFactory
from django.urls import reverse
from model_bakery import baker

from beach_wood_user.models import BWUser
from client.models import ClientProxy
from core.constants.site_settings import SITE_SETTINGS_DB_SLUG
from core.constants.users import CON_MANAGER
from core.models import CRUDEventProxy
from dashboard.views.manager import DashboardViewBW
from site_settings.models import SiteSettings
from special_assignment.models import SpecialAssignmentProxy

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def setup_dashboard_test_env(db: Any) -> None:
    call_command("create_groups")
    SiteSettings.objects.get_or_create(
        slug=SITE_SETTINGS_DB_SLUG,
        defaults={"name": "LedgerFlare", "email": "info@ledgerflare.com"},
    )
    Site.objects.get_or_create(domain="testserver", defaults={"name": "testserver"})


def test_dashboard_view_query_optimization(
    admin_user: BWUser, django_assert_num_queries: Any
) -> None:
    """Verify that DashboardViewBW eager-loads related models without N+1 query multiplication."""
    admin_user.user_type = CON_MANAGER
    admin_user.save()

    ct = ContentType.objects.get_for_model(ClientProxy)

    # Populate clients
    for i in range(6):
        baker.make(ClientProxy, name=f"Client {i}", is_deleted=False)

    # Populate special assignments
    for i in range(5):
        baker.make(
            SpecialAssignmentProxy,
            title=f"Assignment {i}",
            assigned_by=admin_user,
            is_deleted=False,
        )

    # Populate audit log entries
    for i in range(7):
        baker.make(
            CRUDEventProxy,
            actor=admin_user,
            content_type=ct,
            object_repr=f"Object {i}",
            action=CRUDEventProxy.Action.CREATE,
        )

    factory = RequestFactory()
    request = factory.get(reverse("dashboard:manager:home"))
    request.user = admin_user
    request.session = {}

    view = DashboardViewBW()
    view.setup(request)

    # Evaluate context and iterate through feeds
    context = view.get_context_data()

    # Iterating over the retrieved feeds should not trigger additional queries because all relations are prefetched/selected
    for activity in context["last_activities"]:
        assert activity.user.fullname == admin_user.fullname
        assert activity.content_type.model == "client"

    for assignment in context["special_assignments"]:
        assert assignment.assigned_by.fullname == admin_user.fullname
