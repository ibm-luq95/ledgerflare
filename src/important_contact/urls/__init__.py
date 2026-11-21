from __future__ import annotations

from django.urls import include, path

from important_contact.views import (
    ImportantContactCreateView,
    ImportantContactDeleteView,
    ImportantContactExportCsvView,
    ImportantContactExportExcelView,
    ImportantContactExportView,
    ImportantContactListViewBW,
    ImportantContactQuickPeekView,
    ImportantContactUpdateView,
)


app_name = "important_contact"

urlpatterns = [
    path("", ImportantContactListViewBW.as_view(), name="list"),
    path("export/", ImportantContactExportView.as_view(), name="export"),
    path("export/csv/", ImportantContactExportCsvView.as_view(), name="export_csv"),
    path(
        "export/excel/", ImportantContactExportExcelView.as_view(), name="export_excel"
    ),
    path("create", ImportantContactCreateView.as_view(), name="create"),
    path(
        "<uuid:pk>/quick-peek/",
        ImportantContactQuickPeekView.as_view(),
        name="quick-peek",
    ),
    path("update/<uuid:pk>", ImportantContactUpdateView.as_view(), name="update"),
    path("delete/<uuid:pk>", ImportantContactDeleteView.as_view(), name="delete"),
    path("api/", include("important_contact.urls.api"), name="api"),
]
