from django.urls import path, include

from client_accounting.views.dashboard import ClientDashboardView

app_name = "client_accounting"

urlpatterns = [
    path("dashboard/<uuid:pk>", ClientDashboardView.as_view(), name="dashboard"),
    # path("create", DocumentCreateView.as_view(), name="create"),
    # path("update/<uuid:pk>", DocumentUpdateView.as_view(), name="update"),
    # path("delete/<uuid:pk>", DocumentDeleteView.as_view(), name="delete"),
    # path("api/", include("document.urls.api"), name="api"),
]
