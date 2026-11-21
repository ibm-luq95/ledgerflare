from __future__ import annotations

from django.views.generic import TemplateView

from core.api.throttling import ExportDataRateThrottle
from core.views.mixins import BWLoginRequiredMixin, ThrottledViewMixin


class BankRegisterView(BWLoginRequiredMixin, ThrottledViewMixin, TemplateView):
    throttle_classes = [ExportDataRateThrottle]
    template_name = "client/bank_register.html"
