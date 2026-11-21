"""Jobs report service unit tests."""
from __future__ import annotations

import pytest
from model_bakery import baker

from client.models import ClientProxy
from core.choices import JobStatusEnum
from reports.services.jobs_report_service import JobsReportService


@pytest.mark.django_db
def test_jobs_report_service_aggregates_monthly_data() -> None:
    """Verify JobsReportService monthly aggregation and soft-delete filtering."""
    client = baker.make("client.Client", name="Alpha Corp", is_deleted=False)
    client_proxy = ClientProxy.objects.get(pk=client.pk)

    # 2 completed in May 2026, 1 past due in May 2026
    baker.make(
        "job.Job",
        client=client_proxy,
        period_year="2026",
        period_month="5",
        status=JobStatusEnum.COMPLETED,
        is_deleted=False,
        _quantity=2,
    )
    baker.make(
        "job.Job",
        client=client_proxy,
        period_year="2026",
        period_month="5",
        status=JobStatusEnum.PAST_DUE,
        is_deleted=False,
    )
    # 1 soft deleted in May 2026 (must be excluded)
    baker.make(
        "job.Job",
        client=client_proxy,
        period_year="2026",
        period_month="5",
        status=JobStatusEnum.COMPLETED,
        is_deleted=True,
    )

    service = JobsReportService()
    result = service.get_report_data(
        filter_params={"period_year": "2026"},
        page=1,
        per_page=15,
    )

    assert result.total_clients_count >= 1
    assert result.summary_kpis.total_jobs_count == 3
    assert result.summary_kpis.total_completed_count == 2
    assert result.summary_kpis.total_past_due_count == 1
    assert result.summary_kpis.overall_completion_rate == pytest.approx(
        66.67, 0.01
    )

    row = next(r for r in result.rows if r.client.pk == client.pk)
    assert row.total_jobs == 3
    assert row.completed_jobs == 2
    assert row.past_due_jobs == 1
    assert row.completion_rate == pytest.approx(66.67, 0.01)

    may_cell = row.months[4]
    assert may_cell.month_idx == 5
    assert may_cell.month_name.upper() == "MAY"
    assert may_cell.completed_count == 2
    assert may_cell.past_due_count == 1
    assert may_cell.total_count == 3
    assert may_cell.has_jobs is True
    assert "client=" in may_cell.jobs_filter_url
    assert "period_month=5" in may_cell.jobs_filter_url


@pytest.mark.django_db
def test_jobs_report_service_empty_client_row() -> None:
    """Verify JobsReportService handles clients with zero jobs correctly."""
    client = baker.make("client.Client", name="Beta LLC", is_deleted=False)
    service = JobsReportService()
    result = service.get_report_data(
        filter_params={"clients": [client.pk], "period_year": "2026"},
        page=1,
        per_page=15,
    )

    assert result.total_clients_count == 1
    row = result.rows[0]
    assert row.total_jobs == 0
    assert row.completion_rate == 0.0
    assert len(row.months) == 12
    for m in row.months:
        assert m.has_jobs is False
        assert m.total_count == 0


@pytest.mark.django_db
def test_jobs_report_service_sorted_by_most_jobs() -> None:
    """Verify clients are sorted by most jobs in the period descending."""
    client_low = baker.make("client.Client", name="Zeta Corp", is_deleted=False)
    client_high = baker.make("client.Client", name="Apex Inc", is_deleted=False)

    client_low_proxy = ClientProxy.objects.get(pk=client_low.pk)
    client_high_proxy = ClientProxy.objects.get(pk=client_high.pk)

    # 1 job for low
    baker.make(
        "job.Job",
        client=client_low_proxy,
        period_year="2026",
        period_month="3",
        status=JobStatusEnum.IN_PROGRESS,
        is_deleted=False,
    )
    # 5 jobs for high
    baker.make(
        "job.Job",
        client=client_high_proxy,
        period_year="2026",
        period_month="4",
        status=JobStatusEnum.COMPLETED,
        is_deleted=False,
        _quantity=5,
    )

    service = JobsReportService()
    result = service.get_report_data(
        filter_params={
            "period_year": "2026",
            "order_by": "most_jobs_count",
            "clients": [client_low.pk, client_high.pk],
        },
        page=1,
        per_page=15,
    )

    assert len(result.rows) == 2
    assert result.rows[0].client.pk == client_high.pk
    assert result.rows[0].total_jobs == 5
    assert result.rows[1].client.pk == client_low.pk
    assert result.rows[1].total_jobs == 1


@pytest.mark.django_db
def test_jobs_report_service_sorted_by_current_week() -> None:
    """Verify clients are sorted by current week jobs first."""
    from django.utils import timezone

    client_a = baker.make("client.Client", name="Client A", is_deleted=False)
    client_b = baker.make("client.Client", name="Client B", is_deleted=False)

    client_a_proxy = ClientProxy.objects.get(pk=client_a.pk)
    client_b_proxy = ClientProxy.objects.get(pk=client_b.pk)

    today = timezone.now().date()
    # Client B has a job due today (current week)
    baker.make(
        "job.Job",
        client=client_b_proxy,
        period_year="2026",
        period_month=str(today.month),
        due_date=today,
        status=JobStatusEnum.IN_PROGRESS,
        is_deleted=False,
    )
    # Client A has 5 jobs but none due this week (future month)
    baker.make(
        "job.Job",
        client=client_a_proxy,
        period_year="2026",
        period_month="12",
        due_date=today + timezone.timedelta(days=90),
        status=JobStatusEnum.IN_PROGRESS,
        is_deleted=False,
        _quantity=5,
    )

    service = JobsReportService()
    result = service.get_report_data(
        filter_params={
            "period_year": "2026",
            "order_by": "current_week",
            "clients": [client_a.pk, client_b.pk],
        },
        page=1,
        per_page=15,
    )

    # Client B should appear first because it has a job due in the current week
    assert len(result.rows) == 2
    assert result.rows[0].client.pk == client_b.pk
    assert result.rows[1].client.pk == client_a.pk


@pytest.mark.django_db
def test_jobs_report_service_health_status_and_filtering() -> None:
    """Verify health status calculation and filtering."""
    c_good = baker.make("client.Client", name="Good Corp", is_deleted=False)
    c_risk = baker.make("client.Client", name="Risk Corp", is_deleted=False)
    c_bad = baker.make("client.Client", name="Bad Corp", is_deleted=False)

    p_good = ClientProxy.objects.get(pk=c_good.pk)
    p_risk = ClientProxy.objects.get(pk=c_risk.pk)
    p_bad = ClientProxy.objects.get(pk=c_bad.pk)

    # Good: 2 completed, 0 past due -> on_track
    baker.make(
        "job.Job",
        client=p_good,
        period_year="2026",
        period_month="1",
        status=JobStatusEnum.COMPLETED,
        is_deleted=False,
        _quantity=2,
    )
    # Risk: 1 past due -> at_risk
    baker.make(
        "job.Job",
        client=p_risk,
        period_year="2026",
        period_month="2",
        status=JobStatusEnum.PAST_DUE,
        is_deleted=False,
    )
    # Bad: 3 past due -> action_needed
    baker.make(
        "job.Job",
        client=p_bad,
        period_year="2026",
        period_month="3",
        status=JobStatusEnum.PAST_DUE,
        is_deleted=False,
        _quantity=3,
    )

    service = JobsReportService()

    # 1. Unfiltered: all 3 with correct health badges
    res_all = service.get_report_data(
        filter_params={
            "period_year": "2026",
            "clients": [c_good.pk, c_risk.pk, c_bad.pk],
        },
        page=1,
        per_page=10,
    )
    rows_by_name = {r.client.name: r for r in res_all.rows}
    assert rows_by_name["Good Corp"].health_status == "on_track"
    assert rows_by_name["Risk Corp"].health_status == "at_risk"
    assert rows_by_name["Bad Corp"].health_status == "action_needed"

    # 2. Filter action_needed
    res_bad = service.get_report_data(
        filter_params={
            "period_year": "2026",
            "health_status": "action_needed",
            "clients": [c_good.pk, c_risk.pk, c_bad.pk],
        },
        page=1,
        per_page=10,
    )
    assert len(res_bad.rows) == 1
    assert res_bad.rows[0].client.name == "Bad Corp"


@pytest.mark.django_db
def test_jobs_report_service_calculates_monthly_trends() -> None:
    """Verify JobsReportService accurately groups 12-month trend metrics."""
    client = baker.make(
        "client.Client", name="Trend Test Corp", is_deleted=False
    )
    client_proxy = ClientProxy.objects.get(pk=client.pk)

    # Jan: 2 completed
    baker.make(
        "job.Job",
        client=client_proxy,
        period_year="2026",
        period_month="1",
        status=JobStatusEnum.COMPLETED,
        is_deleted=False,
        _quantity=2,
    )
    # Mar: 1 in-progress, 1 past-due
    baker.make(
        "job.Job",
        client=client_proxy,
        period_year="2026",
        period_month="3",
        status=JobStatusEnum.IN_PROGRESS,
        is_deleted=False,
    )
    baker.make(
        "job.Job",
        client=client_proxy,
        period_year="2026",
        period_month="3",
        status=JobStatusEnum.PAST_DUE,
        is_deleted=False,
    )

    service = JobsReportService()
    result = service.get_report_data(
        filter_params={"period_year": "2026", "clients": [client.pk]},
        page=1,
        per_page=10,
    )

    assert len(result.monthly_trends) == 12

    jan_trend = result.monthly_trends[0]
    assert jan_trend["month"].upper() == "JAN"
    assert jan_trend["completed"] == 2
    assert jan_trend["total"] == 2

    mar_trend = result.monthly_trends[2]
    assert mar_trend["month"].upper() == "MAR"
    assert mar_trend["in_progress"] == 1
    assert mar_trend["past_due"] == 1
    assert mar_trend["total"] == 2

    feb_trend = result.monthly_trends[1]
    assert feb_trend["total"] == 0


@pytest.mark.django_db
def test_jobs_report_service_caching() -> None:
    """Verify JobsReportService caches result and returns cached object on second call."""
    from django.core.cache import cache

    cache.clear()

    client = baker.make("client.Client", name="Cache Test LLC", is_deleted=False)
    service = JobsReportService()
    filters = {"period_year": "2026", "clients": [client.pk]}

    # 1. First call (populates cache)
    result_1 = service.get_report_data(filter_params=filters, page=1, per_page=10)
    cache_key = service._generate_cache_key(filters, page=1, per_page=10)
    assert cache.get(cache_key) is not None

    # 2. Second call (retrieves from cache)
    result_2 = service.get_report_data(filter_params=filters, page=1, per_page=10)
    assert result_2.total_clients_count == result_1.total_clients_count
    assert len(result_2.rows) == len(result_1.rows)

    cache.clear()



