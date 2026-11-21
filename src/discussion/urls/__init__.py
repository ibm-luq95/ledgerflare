from __future__ import annotations

from django.urls import include, path

from discussion.views import DiscussionCreateHtmxView, DiscussionListView

app_name = "discussion"

urlpatterns = [
    path("", DiscussionListView.as_view(), name="list"),
    path("htmx/create/", DiscussionCreateHtmxView.as_view(), name="htmx_create"),
    path("api/", include("discussion.urls.api"), name="apis"),
]
