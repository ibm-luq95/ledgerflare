"""Jobs report export views for Excel and CSV formats."""
from __future__ import annotations

from typing import Any, ClassVar

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View

from core.api.throttling import ExportDataRateThrottle
from core.cache import BWSiteSettingsViewMixin
from core.views.mixins import BWLoginRequiredMixin, ThrottledViewMixin
from reports.filters.client import ClientJobsFilter
from reports.services.jobs_report_export_service import JobsReportExportService
from reports.services.jobs_report_service import JobsReportService


class BaseJobsReportExportView(
    ThrottledViewMixin,
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    View,
):
    """Base class for jobs report export views."""

    throttle_classes: ClassVar[list[type[ExportDataRateThrottle]]] = [
        ExportDataRateThrottle
    ]
    permission_required = "client.can_view_jobs_report"
    permission_denied_message = _("You do not have permission to access this page.")
    http_method_names: ClassVar[list[str]] = ["get"]

    def get_report_data(self, request: HttpRequest) -> tuple[Any, str]:
        """Extract filtered report result across all matching records."""
        filter_form = ClientJobsFilter(request=request, data=request.GET or None)
        filter_inputs = filter_form.serialize_inputs()
        selected_year = (
            filter_inputs.get("period_year") or str(timezone.now().year)
        )

        service = JobsReportService()
        # Fetch full dataset without pagination limit (up to 10,000 clients)
        report_result = service.get_report_data(
            filter_params=filter_inputs,
            page=1,
            per_page=10000,
        )
        return report_result, selected_year


class JobsReportExportExcelView(BaseJobsReportExportView):
    """View to export client jobs report to Microsoft Excel (.xlsx)."""

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Handle GET request to generate and download Excel workbook."""
        report_result, selected_year = self.get_report_data(request)
        export_service = JobsReportExportService()
        excel_buffer = export_service.export_excel(
            report_result=report_result, year=selected_year
        )

        filename = f"client_jobs_report_{selected_year}.xlsx"
        response = HttpResponse(
            excel_buffer.getvalue(),
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class JobsReportExportCsvView(BaseJobsReportExportView):
    """View to export client jobs report to CSV format."""

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Handle GET request to generate and download CSV file."""
        report_result, selected_year = self.get_report_data(request)
        export_service = JobsReportExportService()
        csv_content = export_service.export_csv(
            report_result=report_result, year=selected_year
        )

        filename = f"client_jobs_report_{selected_year}.csv"
        response = HttpResponse(csv_content, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
