# -*- coding: utf-8 -*-#

from django.urls import path
from rest_framework import routers

from staff_briefcase.views.accounts import StaffAccountsViewSet
from staff_briefcase.views.accounts.reveal import StaffAccountRevealPasswordApiView

app_name = "api"

router = routers.DefaultRouter()
router.register(
    r"staff-accounts-api", StaffAccountsViewSet, basename="staff-accounts-api-router"
)

urlpatterns = [
    path(
        "reveal-password/<uuid:pk>/",
        StaffAccountRevealPasswordApiView.as_view(),
        name="reveal-password",
    ),
] + router.urls
