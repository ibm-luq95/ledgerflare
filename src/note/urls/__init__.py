from django.urls import include, path

from note.views import (
    NoteCreateView,
    NoteDeleteView,
    NoteExportCsvView,
    NoteExportExcelView,
    NoteExportView,
    NoteListView,
    NoteQuickPeekView,
    NoteUpdateView,
)


app_name = "note"

urlpatterns = [
    path("", NoteListView.as_view(), name="list"),
    path("export/", NoteExportView.as_view(), name="export"),
    path("export/csv/", NoteExportCsvView.as_view(), name="export_csv"),
    path("export/excel/", NoteExportExcelView.as_view(), name="export_excel"),
    path("create", NoteCreateView.as_view(), name="create"),
    path(
        "<uuid:pk>/quick-peek/",
        NoteQuickPeekView.as_view(),
        name="quick-peek",
    ),
    path("update/<uuid:pk>", NoteUpdateView.as_view(), name="update"),
    path("delete/<uuid:pk>", NoteDeleteView.as_view(), name="delete"),
    path("api/", include("note.urls.api"), name="api"),
]
