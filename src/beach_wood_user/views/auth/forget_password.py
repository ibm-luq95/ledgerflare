# -*- coding: utf-8 -*-#
from typing import Any
from django.views.generic import TemplateView

from core.api.throttling import AuthEndpointRateThrottle
from core.utils import get_trans_txt
from core.views.mixins import ThrottledViewMixin


class BWForgetPasswordView(ThrottledViewMixin, TemplateView):
    """
    Provides users the ability to forget password view
    """
    throttle_classes = [AuthEndpointRateThrottle]
    template_name = "beach_wood_user/auth/reset_password.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", get_trans_txt("Reset Password"))
        return context
