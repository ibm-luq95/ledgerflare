from django.urls import include, path

from document.views import (
    DocumentCreateView,
    DocumentDeleteView,
    DocumentDownloadView,
    DocumentListView,
    DocumentUpdateView,
    DocumentViewerView,
)


app_name = "document"

urlpatterns = [
    path("", DocumentListView.as_view(), name="list"),
    path("create", DocumentCreateView.as_view(), name="create"),
    path("download/<uuid:pk>", DocumentDownloadView.as_view(), name="download"),
    path("view/<uuid:pk>", DocumentViewerView.as_view(), name="view"),
    path("details/<uuid:pk>", DocumentDownloadView.as_view(), name="details"),
    path("update/<uuid:pk>", DocumentUpdateView.as_view(), name="update"),
    path("delete/<uuid:pk>", DocumentDeleteView.as_view(), name="delete"),
    path("api/", include("document.urls.api"), name="api"),
]
