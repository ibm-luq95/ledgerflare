# -*- coding: utf-8 -*-#
from django.urls import path
from rest_framework import routers

from discussion.views import DiscussionViewSet
from discussion.views.api import DiscussionNotificationsApiView

app_name = "api"

router = routers.DefaultRouter()
router.register(r"discussion-api", DiscussionViewSet, basename="discussion-api-router")

urlpatterns = [
    path(
        "discussion-notifications",
        DiscussionNotificationsApiView.as_view(),
        name="set-discussion-notifications",
    ),
] + router.urls
