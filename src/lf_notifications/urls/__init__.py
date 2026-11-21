from __future__ import annotations

from django.urls import path, include

from lf_notifications.views.list import NotificationListView

app_name = "lf_notifications"

urlpatterns = [
    path("list/", NotificationListView.as_view(), name="list"),
    path("api/", include("lf_notifications.urls.api")),
]
