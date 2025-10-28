# -*- coding: utf-8 -*-#
from django.contrib.auth.views import LogoutView
from django.urls import path

from beach_wood_user.views import BWForgetPasswordView
from beach_wood_user.views import BWLoginViewBW
from beach_wood_user.views import BWLogoutView


app_name = "auth"

urlpatterns = [
    path("login", BWLoginViewBW.as_view(), name="login"),
    path("logout", BWLogoutView.as_view(), name="logout"),
    path("reset", BWForgetPasswordView.as_view(), name="reset"),
]
