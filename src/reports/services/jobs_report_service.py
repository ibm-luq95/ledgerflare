"""Jobs report service layer module."""
from __future__ import annotations

import calendar
import hashlib
import json
from dataclasses import dataclass
from typing import Any, ClassVar

from django.core.cache import cache
from django.core.paginator import Page, Paginator
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from client.models import ClientProxy
from core.choices import JobStatusEnum
from job.models import JobProxy


@dataclass(frozen=True, slots=True)
class MonthCell:
    """Represents a monthly job cell in the report matrix."""

    month_idx: int
    month_name: str
    completed_count: int = 0
    in_progress_count: int = 0
    past_due_count: int = 0
    not_started_count: int = 0
    total_count: int = 0
    jobs_filter_url: str = ""
    has_jobs: bool = False


@dataclass(slots=True)
class ClientReportRow:
    """Represents an aggregated client report row across all 12 months."""

    client: ClientProxy
    months: list[MonthCell]
    total_jobs: int = 0
    completed_jobs: int = 0
    in_progress_jobs: int = 0
    past_due_jobs: int = 0
    not_started_jobs: int = 0
    completion_rate: float = 0.0
    health_status: str = "on_track"
    health_label: str = "On Track"
    health_color: str = "emerald"
    health_icon: str = "fa-circle-check"
    health_description: str = "0 past due jobs. Deliverables on track."


@dataclass(frozen=True, slots=True)
class ReportSummaryDTO:
    """Represents top-level executive KPI summary stats."""

    total_clients_count: int
    total_jobs_count: int
    total_completed_count: int
    overall_completion_rate: float
    total_in_progress_count: int
    total_past_due_count: int
    total_not_started_count: int


@dataclass(slots=True)
class JobsReportResult:
    """Container for complete jobs report calculation result."""

    summary_kpis: ReportSummaryDTO
    rows: list[ClientReportRow]
    months_header: list[dict[str, str | int]]
    page_obj: Page
    total_clients_count: int
    monthly_trends: list[dict[str, Any]]


class JobsReportService:
    """Service providing aggregated matrix data and KPI metrics for the jobs report."""

    CACHE_TTL_SECONDS: ClassVar[int] = 180
    MONTH_NAMES: ClassVar[list[str]] = [
        calendar.month_abbr[m].upper() for m in range(1, 13)
    ]

    def _generate_cache_key(
        self, filter_params: dict[str, Any], page: int, per_page: int
    ) -> str:
        """Generate unique cache key following resource_action_identifier convention."""
        normalized: dict[str, Any] = {}
        for k, v in sorted(filter_params.items()):
            if isinstance(v, (list, tuple, set)):
                normalized[k] = sorted(str(x) for x in v)
            elif v is not None:
                normalized[k] = str(v)
        params_str = json.dumps(normalized, sort_keys=True)
        params_hash = hashlib.sha256(params_str.encode("utf-8")).hexdigest()[:12]
        year = str(filter_params.get("period_year") or "all")
        return f"jobs_report_data_{year}_{params_hash}_p{page}_n{per_page}"

    def get_report_data(
        self,
        filter_params: dict[str, Any] | None = None,
        page: int = 1,
        per_page: int = 15,
        use_cache: bool = True,
    ) -> JobsReportResult:
        """Fetch and structure job report data into typed DTOs.

        Args:
            filter_params: Serialized inputs from the filter form.
            page: Current pagination page number.
            per_page: Number of clients to display per page.
            use_cache: Whether to use Valkey/Redis cache.

        Returns:
            JobsReportResult containing summary KPIs, client rows, and pagination.
        """
        filters = filter_params or {}
        cache_key = ""
        if use_cache:
            cache_key = self._generate_cache_key(
                filter_params=filters, page=page, per_page=per_page
            )
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

        period_year = filters.get("period_year")
        if not period_year or str(period_year).lower() in ("all", "none"):
            period_year = str(timezone.now().year)
        else:
            period_year = str(period_year)

        clients_pks = filters.get("clients")
        client_categories = filters.get("categories")
        job_categories = filters.get("job_categories")
        job_status = filters.get("job_status")
        job_type = filters.get("job_type")
        job_stats = filters.get("job_stats")
        managed_by = filters.get("managed_by")
        period_month = filters.get("period_month")

        clients_q = Q(is_deleted=False)
        if clients_pks:
            clients_q &= Q(pk__in=clients_pks)
        if client_categories:
            clients_q &= Q(categories__in=client_categories)
        if job_categories:
            clients_q &= Q(
                jobs__categories__in=job_categories, jobs__is_deleted=False
            )
        if managed_by:
            clients_q &= Q(
                jobs__managed_by__in=managed_by, jobs__is_deleted=False
            )

        order_by_choice = filters.get("order_by") or "current_week"
        health_status_choice = filters.get("health_status") or "all"

        now_date = timezone.now().date()
        start_of_week = now_date - timezone.timedelta(days=now_date.weekday())
        end_of_week = start_of_week + timezone.timedelta(days=6)

        client_jobs_count_filter = Q(jobs__is_deleted=False)
        if period_year and period_year.isdigit():
            client_jobs_count_filter &= Q(jobs__period_year=period_year)
        if job_categories:
            client_jobs_count_filter &= Q(jobs__categories__in=job_categories)
        if managed_by:
            client_jobs_count_filter &= Q(jobs__managed_by__in=managed_by)
        if period_month and str(period_month).isdigit():
            client_jobs_count_filter &= Q(jobs__period_month=str(period_month))

        client_week_jobs_filter = Q(
            jobs__is_deleted=False,
            jobs__due_date__range=(start_of_week, end_of_week),
        )
        client_past_due_filter = client_jobs_count_filter & Q(
            jobs__status=JobStatusEnum.PAST_DUE
        )

        clients_qs = (
            ClientProxy.objects.filter(clients_q)
            .annotate(
                total_period_jobs=Count(
                    "jobs", filter=client_jobs_count_filter, distinct=True
                ),
                current_week_jobs=Count(
                    "jobs", filter=client_week_jobs_filter, distinct=True
                ),
                past_due_jobs_count=Count(
                    "jobs", filter=client_past_due_filter, distinct=True
                ),
            )
            .prefetch_related("categories")
        )

        match health_status_choice:
            case "action_needed":
                clients_qs = clients_qs.filter(past_due_jobs_count__gte=3)
            case "at_risk":
                clients_qs = clients_qs.filter(
                    past_due_jobs_count__gte=1, past_due_jobs_count__lte=2
                )
            case "on_track":
                clients_qs = clients_qs.filter(past_due_jobs_count=0)
            case _:
                pass

        match order_by_choice:
            case "current_week":
                clients_qs = clients_qs.order_by(
                    "-current_week_jobs", "-total_period_jobs", "name"
                )
            case "most_jobs_count" | "most_jobs":
                clients_qs = clients_qs.order_by("-total_period_jobs", "name")
            case "least_jobs":
                clients_qs = clients_qs.order_by("total_period_jobs", "name")
            case "name_asc":
                clients_qs = clients_qs.order_by("name")
            case "name_desc":
                clients_qs = clients_qs.order_by("-name")
            case _:
                clients_qs = clients_qs.order_by("-total_period_jobs", "name")

        paginator = Paginator(clients_qs, per_page)
        page_obj = paginator.get_page(page)
        page_clients = list(page_obj.object_list)
        page_client_pks = [c.pk for c in page_clients]

        jobs_base_q = Q(is_deleted=False)
        if period_year and period_year.isdigit():
            jobs_base_q &= Q(period_year=period_year)
        if period_month and str(period_month).isdigit():
            jobs_base_q &= Q(period_month=str(period_month))
        if job_categories:
            jobs_base_q &= Q(categories__in=job_categories)
        if job_status:
            jobs_base_q &= Q(status__in=job_status)
        if job_type:
            jobs_base_q &= Q(job_type__in=job_type)
        if job_stats:
            jobs_base_q &= Q(state__in=job_stats)
        if managed_by:
            jobs_base_q &= Q(managed_by__in=managed_by)
        if clients_pks:
            jobs_base_q &= Q(client_id__in=clients_pks)
        if client_categories:
            jobs_base_q &= Q(client__categories__in=client_categories)

        summary_kpis = self._compute_summary_kpis(
            jobs_base_q=jobs_base_q,
            total_clients_count=paginator.count,
        )

        rows = self._build_client_rows(
            page_clients=page_clients,
            page_client_pks=page_client_pks,
            jobs_base_q=jobs_base_q,
            period_year=period_year,
        )

        months_header = [
            {
                "index": m_idx,
                "name": self.MONTH_NAMES[m_idx - 1],
                "year": period_year,
                "full_title": f"{self.MONTH_NAMES[m_idx - 1]} - {period_year}",
            }
            for m_idx in range(1, 13)
        ]

        monthly_trends = self._calculate_monthly_trends(jobs_base_q=jobs_base_q)

        result = JobsReportResult(
            summary_kpis=summary_kpis,
            rows=rows,
            months_header=months_header,
            page_obj=page_obj,
            total_clients_count=paginator.count,
            monthly_trends=monthly_trends,
        )

        if use_cache and cache_key:
            cache.set(cache_key, result, timeout=self.CACHE_TTL_SECONDS)

        return result

    def _calculate_monthly_trends(
        self, jobs_base_q: Q
    ) -> list[dict[str, Any]]:
        """Calculate month-by-month workload metrics for macro charting."""
        monthly_aggs = (
            JobProxy.objects.filter(jobs_base_q)
            .values("period_month")
            .annotate(
                total=Count("id"),
                completed=Count("id", filter=Q(status=JobStatusEnum.COMPLETED)),
                in_progress=Count(
                    "id", filter=Q(status=JobStatusEnum.IN_PROGRESS)
                ),
                past_due=Count("id", filter=Q(status=JobStatusEnum.PAST_DUE)),
                not_started=Count(
                    "id", filter=Q(status=JobStatusEnum.NOT_STARTED)
                ),
            )
        )
        trends_map = {}
        for item in monthly_aggs:
            try:
                m_num = int(item["period_month"])
                trends_map[m_num] = item
            except (ValueError, TypeError):
                continue

        trends: list[dict[str, Any]] = []
        for m_idx in range(1, 13):
            m_data = trends_map.get(m_idx, {})
            trends.append(
                {
                    "month": self.MONTH_NAMES[m_idx - 1],
                    "month_idx": m_idx,
                    "completed": m_data.get("completed", 0),
                    "in_progress": m_data.get("in_progress", 0),
                    "past_due": m_data.get("past_due", 0),
                    "not_started": m_data.get("not_started", 0),
                    "total": m_data.get("total", 0),
                }
            )
        return trends

    def _compute_summary_kpis(
        self, jobs_base_q: Q, total_clients_count: int
    ) -> ReportSummaryDTO:
        """Compute aggregate KPIs for the top summary cards."""
        agg = JobProxy.objects.filter(jobs_base_q).aggregate(
            total_jobs=Count("id"),
            completed=Count("id", filter=Q(status=JobStatusEnum.COMPLETED)),
            in_progress=Count("id", filter=Q(status=JobStatusEnum.IN_PROGRESS)),
            past_due=Count("id", filter=Q(status=JobStatusEnum.PAST_DUE)),
            not_started=Count("id", filter=Q(status=JobStatusEnum.NOT_STARTED)),
        )

        total = agg.get("total_jobs") or 0
        completed = agg.get("completed") or 0
        in_progress = agg.get("in_progress") or 0
        past_due = agg.get("past_due") or 0
        not_started = agg.get("not_started") or 0
        rate = round((completed / total * 100), 2) if total > 0 else 0.0

        return ReportSummaryDTO(
            total_clients_count=total_clients_count,
            total_jobs_count=total,
            total_completed_count=completed,
            overall_completion_rate=rate,
            total_in_progress_count=in_progress,
            total_past_due_count=past_due,
            total_not_started_count=not_started,
        )

    def _build_client_rows(
        self,
        page_clients: list[ClientProxy],
        page_client_pks: list[Any],
        jobs_base_q: Q,
        period_year: str,
    ) -> list[ClientReportRow]:
        """Aggregate monthly job counts in a single batch query and format rows."""
        if not page_client_pks:
            return []

        page_jobs_q = jobs_base_q & Q(client_id__in=page_client_pks)
        batch_aggregates = (
            JobProxy.objects.filter(page_jobs_q)
            .values("client_id", "period_month")
            .annotate(
                total=Count("id"),
                completed=Count("id", filter=Q(status=JobStatusEnum.COMPLETED)),
                in_progress=Count(
                    "id", filter=Q(status=JobStatusEnum.IN_PROGRESS)
                ),
                past_due=Count("id", filter=Q(status=JobStatusEnum.PAST_DUE)),
                not_started=Count(
                    "id", filter=Q(status=JobStatusEnum.NOT_STARTED)
                ),
            )
        )

        matrix: dict[tuple[Any, int], dict[str, int]] = {}
        for item in batch_aggregates:
            client_id = item["client_id"]
            try:
                month_val = int(item["period_month"])
            except (ValueError, TypeError):
                continue
            matrix[(client_id, month_val)] = {
                "total": item["total"],
                "completed": item["completed"],
                "in_progress": item["in_progress"],
                "past_due": item["past_due"],
                "not_started": item["not_started"],
            }

        rows: list[ClientReportRow] = []
        jobs_list_base_url = reverse("dashboard:job:list")

        for client in page_clients:
            client_months: list[MonthCell] = []
            c_total = 0
            c_completed = 0
            c_in_progress = 0
            c_past_due = 0
            c_not_started = 0

            for m_idx in range(1, 13):
                m_name = self.MONTH_NAMES[m_idx - 1]
                counts = matrix.get((client.pk, m_idx))
                if counts and counts["total"] > 0:
                    tot = counts["total"]
                    comp = counts["completed"]
                    inp = counts["in_progress"]
                    pd = counts["past_due"]
                    ns = counts["not_started"]

                    c_total += tot
                    c_completed += comp
                    c_in_progress += inp
                    c_past_due += pd
                    c_not_started += ns

                    filter_url = (
                        f"{jobs_list_base_url}?client={client.pk}&"
                        f"period_year={period_year}&period_month={m_idx}"
                    )

                    cell = MonthCell(
                        month_idx=m_idx,
                        month_name=m_name,
                        completed_count=comp,
                        in_progress_count=inp,
                        past_due_count=pd,
                        not_started_count=ns,
                        total_count=tot,
                        jobs_filter_url=filter_url,
                        has_jobs=True,
                    )
                else:
                    cell = MonthCell(
                        month_idx=m_idx,
                        month_name=m_name,
                        has_jobs=False,
                    )
                client_months.append(cell)

            c_rate = (
                round((c_completed / c_total * 100), 2) if c_total > 0 else 0.0
            )

            h_status, h_label, h_color, h_icon, h_desc = (
                self._calculate_health_status(
                    total_jobs=c_total,
                    completed_jobs=c_completed,
                    past_due_jobs=c_past_due,
                )
            )

            row = ClientReportRow(
                client=client,
                months=client_months,
                total_jobs=c_total,
                completed_jobs=c_completed,
                in_progress_jobs=c_in_progress,
                past_due_jobs=c_past_due,
                not_started_jobs=c_not_started,
                completion_rate=c_rate,
                health_status=h_status,
                health_label=h_label,
                health_color=h_color,
                health_icon=h_icon,
                health_description=h_desc,
            )
            rows.append(row)

        return rows

    @staticmethod
    def _calculate_health_status(
        total_jobs: int, completed_jobs: int, past_due_jobs: int
    ) -> tuple[str, str, str, str, str]:
        """Determine health status, label, badge color, icon, and explanation."""
        if past_due_jobs >= 3 or (
            past_due_jobs > 0 and completed_jobs == 0 and total_jobs >= 3
        ):
            return (
                "action_needed",
                _("Action Needed"),
                "rose",
                "fa-circle-exclamation",
                _(
                    "Action Needed: 3+ past due jobs. "
                    "Urgent manager intervention required."
                ),
            )
        if past_due_jobs >= 1:
            return (
                "at_risk",
                _("At Risk"),
                "amber",
                "fa-triangle-exclamation",
                _(
                    "At Risk: 1-2 past due jobs. "
                    "Attention needed to prevent further delivery delays."
                ),
            )
        return (
            "on_track",
            _("On Track"),
            "emerald",
            "fa-circle-check",
            _(
                "On Track: 0 past due jobs. "
                "All scheduled deliverables are on track."
            ),
        )
