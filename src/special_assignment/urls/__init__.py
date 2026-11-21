# -*- coding: utf-8 -*-#
from django.urls import path, include

from special_assignment.views import (
    SpecialAssignmentDetailsView,
    SpecialAssignmentCreateView,
    SpecialAssignmentUpdateView,
    SpecialAssignmentDeleteView,
    SpecialAssignmentListView,
    SpecialAssignmentQuickPeekView,
    SpecialAssignmentExportView,
    SpecialAssignmentExportCsvView,
    SpecialAssignmentExportExcelView,
    RequestedSpecialAssignmentsListView,
)

app_name = "special_assignment"

urlpatterns = [
    path("", SpecialAssignmentListView.as_view(), name="list"),
    path("export/", SpecialAssignmentExportView.as_view(), name="export"),
    path("export/csv/", SpecialAssignmentExportCsvView.as_view(), name="export_csv"),
    path(
        "export/excel/", SpecialAssignmentExportExcelView.as_view(), name="export_excel"
    ),
    path("requested", RequestedSpecialAssignmentsListView.as_view(), name="requested"),
    path("create", SpecialAssignmentCreateView.as_view(), name="create"),
    path("<uuid:pk>", SpecialAssignmentDetailsView.as_view(), name="details"),
    path(
        "<uuid:pk>/quick-peek/",
        SpecialAssignmentQuickPeekView.as_view(),
        name="quick-peek",
    ),
    path("update/<uuid:pk>", SpecialAssignmentUpdateView.as_view(), name="update"),
    path("delete/<uuid:pk>", SpecialAssignmentDeleteView.as_view(), name="delete"),
    path("api/", include("special_assignment.urls.api"), name="api"),
]
