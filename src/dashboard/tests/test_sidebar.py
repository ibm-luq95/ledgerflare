# -*- coding: utf-8 -*-#
from __future__ import annotations

from types import SimpleNamespace
import uuid

import pytest
from django.template import Context, Template
from django.urls import ResolverMatch
from core.constants.users import CON_ASSISTANT, CON_BOOKKEEPER, CON_CFO, CON_MANAGER


def _create_mock_user(user_type: str = CON_MANAGER, is_superuser: bool = False) -> SimpleNamespace:
    return SimpleNamespace(
        user_type=user_type,
        is_superuser=is_superuser,
        briefcase=SimpleNamespace(pk=uuid.UUID("00000000-0000-0000-0000-000000000000")),
    )


def _get_test_context(request: SimpleNamespace) -> Context:
    return Context(
        {
            "request": request,
            "perms": {},
            "CON_MANAGER": CON_MANAGER,
            "CON_ASSISTANT": CON_ASSISTANT,
            "CON_BOOKKEEPER": CON_BOOKKEEPER,
            "CON_CFO": CON_CFO,
        }
    )


@pytest.mark.django_db
def test_dashboard_sidebar_active_link_on_dashboard_home():
    mock_request = SimpleNamespace(
        resolver_match=ResolverMatch(
            func=lambda x: None,
            args=(),
            kwargs={},
            url_name="home",
            app_names=["dashboard", "manager"],
            namespaces=["dashboard", "manager"],
            route="dashboard/manager/",
        ),
        user=_create_mock_user(user_type=CON_MANAGER),
    )

    template_content = """
    {% include "components/inc/dashboard/left_side.html" %}
    """
    rendered = Template(template_content).render(_get_test_context(mock_request))

    assert "bg-neutral-700 text-white" in rendered


@pytest.mark.django_db
def test_dashboard_sidebar_active_link_on_clients_list():
    mock_request = SimpleNamespace(
        resolver_match=ResolverMatch(
            func=lambda x: None,
            args=(),
            kwargs={},
            url_name="list",
            app_names=["dashboard", "client"],
            namespaces=["dashboard", "client"],
            route="dashboard/client/",
        ),
        user=_create_mock_user(user_type=CON_MANAGER),
    )

    template_content = """
    {% include "components/inc/dashboard/left_side.html" %}
    """
    rendered = Template(template_content).render(_get_test_context(mock_request))

    assert "bg-neutral-700 text-white" in rendered


@pytest.mark.django_db
def test_dashboard_sidebar_active_link_on_jobs_list():
    mock_request = SimpleNamespace(
        resolver_match=ResolverMatch(
            func=lambda x: None,
            args=(),
            kwargs={},
            url_name="list",
            app_names=["dashboard", "job"],
            namespaces=["dashboard", "job"],
            route="dashboard/job/",
        ),
        user=_create_mock_user(user_type=CON_MANAGER),
    )

    template_content = """
    {% include "components/inc/dashboard/left_side.html" %}
    """
    rendered = Template(template_content).render(_get_test_context(mock_request))

    assert "bg-neutral-700 text-white" in rendered


@pytest.mark.django_db
def test_dashboard_sidebar_staff_accordion_active_on_assistant_list():
    mock_request = SimpleNamespace(
        resolver_match=ResolverMatch(
            func=lambda x: None,
            args=(),
            kwargs={},
            url_name="list",
            app_names=["dashboard", "management_assistant"],
            namespaces=["dashboard", "management_assistant"],
            route="dashboard/management/assistant/",
        ),
        user=_create_mock_user(user_type=CON_MANAGER, is_superuser=True),
    )

    template_content = """
    {% include "components/inc/dashboard/left_side.html" %}
    """
    rendered = Template(template_content).render(_get_test_context(mock_request))

    assert 'id="users-accordion"' in rendered
    assert "active" in rendered
    assert "bg-neutral-700 text-white" in rendered


@pytest.mark.django_db
def test_dashboard_sidebar_archive_accordion_active_on_archive_jobs():
    mock_request = SimpleNamespace(
        resolver_match=ResolverMatch(
            func=lambda x: None,
            args=(),
            kwargs={},
            url_name="list",
            app_names=["dashboard", "archive", "jobs"],
            namespaces=["dashboard", "archive", "jobs"],
            route="dashboard/archive/jobs/",
        ),
        user=_create_mock_user(user_type=CON_MANAGER, is_superuser=True),
    )

    template_content = """
    {% include "components/inc/dashboard/left_side.html" %}
    """
    rendered = Template(template_content).render(_get_test_context(mock_request))

    assert 'id="archive-accordion"' in rendered
    assert "active" in rendered
    assert "bg-neutral-700 text-white" in rendered


@pytest.mark.django_db
def test_dashboard_sidebar_reports_accordion_active_on_jobs_report():
    mock_request = SimpleNamespace(
        resolver_match=ResolverMatch(
            func=lambda x: None,
            args=(),
            kwargs={},
            url_name="job_reports_list",
            app_names=["dashboard", "reports", "clients_reports"],
            namespaces=["dashboard", "reports", "clients_reports"],
            route="dashboard/reports/clients/",
        ),
        user=_create_mock_user(user_type=CON_MANAGER),
    )

    template_content = """
    {% include "components/inc/dashboard/left_side.html" %}
    """
    rendered = Template(template_content).render(_get_test_context(mock_request))

    assert 'id="reports-accordion"' in rendered
    assert "active" in rendered
    assert "bg-neutral-700 text-white" in rendered
