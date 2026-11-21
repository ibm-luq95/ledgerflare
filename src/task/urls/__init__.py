from django.urls import include, path

from task.views import (
    TaskCreateView,
    TaskDeleteView,
    TaskExportCsvView,
    TaskExportExcelView,
    TaskExportView,
    TaskListView,
    TaskQuickPeekView,
    TaskUpdateView,
)


app_name = "task"

urlpatterns = [
    path("", TaskListView.as_view(), name="list"),
    path("create", TaskCreateView.as_view(), name="create"),
    path("export/", TaskExportView.as_view(), name="export"),
    path("export/csv/", TaskExportCsvView.as_view(), name="export_csv"),
    path("export/excel/", TaskExportExcelView.as_view(), name="export_excel"),
    path("<uuid:pk>/quick-peek/", TaskQuickPeekView.as_view(), name="quick-peek"),
    path("update/<uuid:pk>", TaskUpdateView.as_view(), name="update"),
    path("delete/<uuid:pk>", TaskDeleteView.as_view(), name="delete"),
    path("api/", include("task.urls.api"), name="api"),
]
