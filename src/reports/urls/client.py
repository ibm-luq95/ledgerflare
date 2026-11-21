"""Client reports URLs."""
from __future__ import annotations

from django.urls import path

from reports.views.client import (
    JobsReportExportCsvView,
    JobsReportExportExcelView,
    JobsReportView,
)


app_name = "clients_reports"

urlpatterns = [
    path("jobs-report/", JobsReportView.as_view(), name="job_reports_list"),
    path(
        "jobs-report/export/excel/",
        JobsReportExportExcelView.as_view(),
        name="job_reports_export_excel",
    ),
    path(
        "jobs-report/export/csv/",
        JobsReportExportCsvView.as_view(),
        name="job_reports_export_csv",
    ),
]
