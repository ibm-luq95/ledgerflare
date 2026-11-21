"""Jobs report view module."""
from __future__ import annotations

import json
from typing import Any, ClassVar

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from core.api.throttling import ExportDataRateThrottle
from core.cache import BWSiteSettingsViewMixin
from core.forms.per_page_form import PerPageForm
from core.views.mixins import BWLoginRequiredMixin, ThrottledViewMixin
from reports.filters.client import ClientJobsFilter
from reports.services.jobs_report_service import JobsReportService


class JobsReportView(
    ThrottledViewMixin,
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    FormView,
):
    """View rendering the annual matrix and KPI report for client jobs."""

    throttle_classes: ClassVar[list[type[ExportDataRateThrottle]]] = [
        ExportDataRateThrottle
    ]
    http_method_names: ClassVar[list[str]] = ["get"]
    form_class = ClientJobsFilter
    success_url = reverse_lazy("dashboard:reports:clients_reports:job_reports_list")
    permission_required = "client.can_view_jobs_report"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "reports/client/jobs/list.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Populate template context with aggregated report DTOs and filters."""
        context = super().get_context_data(**kwargs)
        context["title"] = _("Clients jobs report")
        context["page_header"] = _("Reports")

        try:
            page = int(self.request.GET.get("page", 1))
        except (ValueError, TypeError):
            page = 1

        try:
            per_page = int(self.request.GET.get("per_page", 10))
        except (ValueError, TypeError):
            per_page = 10

        per_page_form = PerPageForm(initial={"per_page": per_page})
        context["per_page_filter_form"] = per_page_form

        form = self.get_form()
        filter_inputs = form.serialize_inputs()
        selected_year = (
            filter_inputs.get("period_year") or str(timezone.now().year)
        )

        service = JobsReportService()
        report_result = service.get_report_data(
            filter_params=filter_inputs,
            page=page,
            per_page=per_page,
        )

        context["summary_kpis"] = report_result.summary_kpis
        context["report_rows"] = report_result.rows
        context["months_header"] = report_result.months_header
        context["page_obj"] = report_result.page_obj
        context["total_clients_count"] = report_result.total_clients_count
        context["monthly_trends"] = report_result.monthly_trends
        context["monthly_trends_json"] = json.dumps(report_result.monthly_trends)
        context["selected_period_year"] = selected_year
        context["filter_form"] = form

        return context

    def get_form_kwargs(self) -> dict[str, Any]:
        """Inject current request into filter form kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        if self.request.GET:
            kwargs["data"] = self.request.GET
        return kwargs
