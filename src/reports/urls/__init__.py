from django.urls import include, path
from django.views.generic import RedirectView


app_name = "reports"

urlpatterns = [
    path("clients/", include("reports.urls.client"), name="clients_reports"),
    path(
        "new",
        RedirectView.as_view(pattern_name="dashboard:job:workstation"),
        name="new_report",
    ),
]
