"""Jobs report export views integration tests."""
from __future__ import annotations

import pytest
from django.urls import reverse
from model_bakery import baker


@pytest.mark.django_db
def test_jobs_report_export_excel_view_returns_file(client) -> None:
    """Verify authenticated staff can download Excel jobs report."""
    user = baker.make(
        "beach_wood_user.BWUser", user_type="developer", is_superuser=True
    )
    client.force_login(user)

    url = reverse("dashboard:reports:clients_reports:job_reports_export_excel")
    response = client.get(url)

    assert response.status_code == 200
    assert (
        response["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert "attachment; filename=" in response["Content-Disposition"]
    assert len(response.content) > 0


@pytest.mark.django_db
def test_jobs_report_export_csv_view_returns_file(client) -> None:
    """Verify authenticated staff can download CSV jobs report."""
    user = baker.make(
        "beach_wood_user.BWUser", user_type="developer", is_superuser=True
    )
    client.force_login(user)

    url = reverse("dashboard:reports:clients_reports:job_reports_export_csv")
    response = client.get(url)

    assert response.status_code == 200
    assert "text/csv" in response["Content-Type"]
    assert "attachment; filename=" in response["Content-Disposition"]
    assert b"Client Name,Categories,Jan" in response.content
