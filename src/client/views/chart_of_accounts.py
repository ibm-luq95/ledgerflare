from __future__ import annotations

from django.views.generic import TemplateView

from core.api.throttling import ExportDataRateThrottle
from core.views.mixins import BWLoginRequiredMixin, ThrottledViewMixin


class ChartOfAccountClientView(BWLoginRequiredMixin, ThrottledViewMixin, TemplateView):
    throttle_classes = [ExportDataRateThrottle]
    template_name = "client/chart_of_accounts.html"
