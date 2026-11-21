"""Jobs report view integration tests."""
from __future__ import annotations

import pytest
from django.urls import reverse
from model_bakery import baker


@pytest.mark.django_db
def test_jobs_report_view_authenticated_access(client) -> None:
    """Verify authenticated staff access to the jobs report view."""
    user = baker.make(
        "beach_wood_user.BWUser", user_type="developer", is_superuser=True
    )
    client.force_login(user)

    url = reverse("dashboard:reports:clients_reports:job_reports_list")
    response = client.get(url)

    assert response.status_code == 200
    assert "summary_kpis" in response.context
    assert "report_rows" in response.context
    assert "months_header" in response.context
    assert "filter_form" in response.context
    assert "selected_period_year" in response.context


@pytest.mark.django_db
def test_jobs_report_view_order_by_filter(client) -> None:
    """Verify GET parameter order_by is correctly applied in the view."""
    user = baker.make(
        "beach_wood_user.BWUser", user_type="developer", is_superuser=True
    )
    client.force_login(user)

    client_a = baker.make("client.Client", name="Alpha Corp", is_deleted=False)
    client_z = baker.make("client.Client", name="Zulu Corp", is_deleted=False)

    url = reverse("dashboard:reports:clients_reports:job_reports_list")
    response = client.get(f"{url}?order_by=name_desc")

    assert response.status_code == 200
    rows = response.context["report_rows"]
    client_names = [r.client.name for r in rows]
    assert client_names.index("Zulu Corp") < client_names.index("Alpha Corp")

