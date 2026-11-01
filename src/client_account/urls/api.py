# -*- coding: utf-8 -*-#
from django.urls import path
from rest_framework import routers

from client_account.views import ClientAccountViewSet
from client_account.views.reveal import ClientAccountRevealPasswordApiView

app_name = "api"

router = routers.DefaultRouter()
router.register(
    r"client-accounts-api", ClientAccountViewSet, basename="client-account-api-router"
)

urlpatterns = [
    path(
        "reveal-password/<uuid:pk>/",
        ClientAccountRevealPasswordApiView.as_view(),
        name="reveal-password",
    ),
] + router.urls
