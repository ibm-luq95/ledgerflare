from __future__ import annotations

from django.views.generic import TemplateView

from core.views.mixins import BWLoginRequiredMixin


class ExpenseCreateView(BWLoginRequiredMixin, TemplateView):
    template_name = "client/expense_create.html"
